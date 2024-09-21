import json
from enum import Enum


class Units(int, Enum):
    CELSIUS = 0
    PERCENT = 1
    TESLA = 2
    VOLT = 3
    AMPERE = 4
    ADIMENTIONAL = 5


class Read:
    def __init__(self, value: int, source: int, units: Units):
        self.value = value
        self.source = source
        self.units = units

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


def load_reads():
    try:
        with open("reads.json", "r") as f:
            data = json.load(f)
            return {int(k): Read(**v) for k, v in data.items()}
    except FileNotFoundError:
        return {}


def save_reads(reads):
    with open("reads.json", "w") as f:
        json.dump({str(k): v.__dict__ for k, v in reads.items()}, f)
