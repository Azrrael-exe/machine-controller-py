import logging
import threading
import time
from queue import Queue

from serial import Serial

from domain.values import Read, Units, load_reads, save_reads

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


def main():
    received_queue = Queue()
    byte_receiver = SerialBytesReceiver(
        header=0x7E,
        uart=Serial(port="/dev/tty.usbmodemF412FA65971C2", baudrate=115200),
        queue=received_queue,
    )

    queue_consumer = QueueConsumer(queue=received_queue)

    received_thread = threading.Thread(target=byte_receiver.runner)
    consumer_thread = threading.Thread(target=queue_consumer.runner)

    received_thread.start()
    consumer_thread.start()

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        byte_receiver.stop()
        queue_consumer.stop()
        received_thread.join()
        consumer_thread.join()
        print("Programa terminado por el usuario")


if __name__ == "__main__":
    main()
