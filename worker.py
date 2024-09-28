import logging
import threading
import time
from json import loads
from queue import Queue

from paho.mqtt import client as mqtt
from redis import Redis
from serial import Serial

from domain.values import Read, Units, save_read_to_redis

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(threadName)s - %(levelname)s - %(message)s",
)


def read_from_bytes(bytes_data: bytearray) -> Read:
    """
    Create a Read object from a bytearray.

    Args:
    bytes_data (bytearray): A bytearray of 6 bytes.

    Returns:
    Read: A Read object created from the bytearray data.

    Raises:
    ValueError: If the bytearray doesn't contain exactly 6 bytes.
    """
    if len(bytes_data) != 6:
        raise ValueError("El bytearray debe contener exactamente 6 bytes.")

    source = bytes_data[0]
    value = int.from_bytes(bytes_data[1:5], byteorder="big", signed=False)
    units = Units(bytes_data[5])

    return Read(value, source, units)


class SerialBytesReceiver:
    def __init__(self, uart: Serial, header: int, queue: Queue):
        self.__uart = uart
        self.__header = header
        self._running = False
        self.__output_queue = queue

    def _calculate_checksum(self, data: bytearray) -> int:
        return sum(data) & 0xFF

    def stop(self):
        self._running = False
        if self.__uart:
            self.__uart.close()

    def _receive_buffer(self):
        logger = logging.getLogger(__name__)
        while self._running:
            if self.__uart.in_waiting > 0:
                header = self.__uart.read(1)[0]
                if header == self.__header:
                    break

        if not self._running:
            return None

        while self.__uart.in_waiting < 1 and self._running:
            time.sleep(0.01)
        if not self._running:
            return None
        length = self.__uart.read(1)[0]

        buffer = bytearray()
        while len(buffer) < length and self._running:
            if self.__uart.in_waiting > 0:
                buffer.extend(
                    self.__uart.read(min(length - len(buffer), self.__uart.in_waiting))
                )
            time.sleep(0.01)

        if not self._running:
            return None
        while self.__uart.in_waiting < 1 and self._running:
            time.sleep(0.01)
        if not self._running:
            return None
        received_checksum = self.__uart.read(1)[0]

        calculated_checksum = self._calculate_checksum(buffer)
        if calculated_checksum != received_checksum:
            logger.error("Error de checksum")
            return None

        return buffer

    def runner(self):
        logger = logging.getLogger(__name__)
        self._running = True
        while self._running:
            buffer = self._receive_buffer()
            if buffer:
                for read_bytes in [buffer[i : i + 6] for i in range(0, len(buffer), 6)]:
                    self.__output_queue.put(read_from_bytes(read_bytes))
                logger.info(
                    f"Received elemnts added in Queue, {self.__output_queue.qsize()} elements in queue"
                )


class QueueConsumer:
    def __init__(self, queue: Queue):
        self.__input_queue = queue
        self._running = False

    def stop(self):
        self._running = False

    def runner(self):
        logger = logging.getLogger(__name__)
        self._running = True
        while self._running:
            if not self.__input_queue.empty():
                read: Read = self.__input_queue.get()
                logger.info(f"Consumed message: {read}")
                reads = load_reads()
                reads[read.source] = Read(**read.dict())
                save_reads(reads)

            else:
                time.sleep(0.1)


class MQTTConsumer:
    def __init__(self, client: mqtt.Client, input_topic: str, output_queue: Queue):
        self.__client = client
        self.__topic = input_topic
        self._running = False
        self._output_queue = output_queue

    def stop(self):
        self._running = False

    def __on_message(self, client, userdata, message):
        logger = logging.getLogger(__name__)
        payload = message.payload.decode()
        logger.info(f"Received message: {payload}")
        try:
            for read in loads(payload).values():
                self._output_queue.put(
                    Read(value=read["value"], source=read["id"], units=read["unit"])
                )
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def runner(self):
        logger = logging.getLogger(__name__)
        self._running = True
        self.__client.subscribe(self.__topic)
        self.__client.on_message = self.__on_message
        logger.info("Running MQTT consumer")
        self.__client.loop_forever()


class ReadLogger:
    def __init__(self, input_queue: Queue, redis_client: Redis):
        self.__input_queue = input_queue
        self._running = False
        self._redis_client = redis_client

    def stop(self):
        self._running = False

    def runner(self):
        logger = logging.getLogger(__name__)
        self._running = True
        while self._running:
            if not self.__input_queue.empty():
                read: Read = self.__input_queue.get()
                logger.info(f"Consumed message: {read}")
                save_read_to_redis(self._redis_client, read)
            else:
                time.sleep(0.1)


def main():
    received_queue = Queue()
    client = mqtt.Client()
    client.connect(host="broker.hivemq.com", port=1883)
    redis_client = Redis(host="redis", port=6379, db=0)

    mqtt_consumer = MQTTConsumer(
        client=client, input_topic="sda-2024/20240928", output_queue=received_queue
    )

    read_logger = ReadLogger(input_queue=received_queue, redis_client=redis_client)

    mqtt_consumer_thread = threading.Thread(
        target=mqtt_consumer.runner, name="MQTTConsumer"
    )
    read_logger_thread = threading.Thread(target=read_logger.runner, name="ReadLogger")
    mqtt_consumer_thread.start()
    read_logger_thread.start()


if __name__ == "__main__":
    main()
