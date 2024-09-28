import json
from enum import Enum
from time import time

from redis import Redis


class Units(int, Enum):
    CELSIUS = 0
    PERCENT = 1
    TESLA = 2
    VOLT = 3
    AMPERE = 4
    ADIMENTIONAL = 5


class Read:
    def __init__(self, value: int, source: int, units: Units, timestamp: int = None):
        self.value = value
        self.source = source
        self.units = units
        self.timestamp = int(time())

    def __add__(self, other):
        if not isinstance(other, Read):
            raise TypeError("Solo se pueden sumar objetos Read")
        if self.units != other.units:
            raise ValueError("No se pueden sumar lecturas con diferentes unidades")
        return Read(self.value + other.value, self.source, self.units)

    def __sub__(self, other):
        if not isinstance(other, Read):
            raise TypeError("Solo se pueden restar objetos Read")
        if self.units != other.units:
            raise ValueError("No se pueden restar lecturas con diferentes unidades")
        return Read(self.value - other.value, self.source, self.units)

    def __repr__(self):
        return f"Read(value={self.value}, source={self.source}, units={self.units})"

    def dict(self):
        return self.__dict__


def save_read_to_redis(redis_client: Redis, read: Read):
    """
    Save a Read object to Redis using the source as the key
    """
    key = f"read:{read.source}"
    value = json.dumps(read.dict())
    redis_client.set(key, value)


def get_read_from_redis(redis_client: Redis, source: int) -> Read:
    """
    Retrieve a Read object from Redis given a source
    """
    key = f"read:{source}"
    value = redis_client.get(key)
    if value is None:
        return None
    read_dict = json.loads(value)
    return Read(**read_dict)
