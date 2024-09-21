import pytest

from domain.values import Units
from domain.values import Read 

def test_read_initialization():
    r = Read(10, 1, Units.CELSIUS)
    assert r.value == 10
    assert r.source == 1
    assert r.units == Units.CELSIUS

def test_read_addition():
    r1 = Read(10, 1, Units.CELSIUS)
    r2 = Read(5, 2, Units.CELSIUS)
    result = r1 + r2
    assert result.value == 15
    assert result.source == 1
    assert result.units == Units.CELSIUS

def test_read_addition_different_units():
    r1 = Read(10, 1, Units.CELSIUS)
    r2 = Read(5, 2, Units.PERCENT)
    with pytest.raises(ValueError):
        r1 + r2

def test_read_addition_invalid_type():
    r = Read(10, 1, Units.CELSIUS)
    with pytest.raises(TypeError):
        r + 5

def test_read_subtraction():
    r1 = Read(10, 1, Units.CELSIUS)
    r2 = Read(5, 2, Units.CELSIUS)
    result = r1 - r2
    assert result.value == 5
    assert result.source == 1
    assert result.units == Units.CELSIUS

def test_read_subtraction_different_units():
    r1 = Read(10, 1, Units.CELSIUS)
    r2 = Read(5, 2, Units.PERCENT)
    with pytest.raises(ValueError):
        r1 - r2

def test_read_subtraction_invalid_type():
    r = Read(10, 1, Units.CELSIUS)
    with pytest.raises(TypeError):
        r - 5

def test_read_representation():
    r = Read(10, 1, Units.CELSIUS)
    assert repr(r) == "Read(value=10, source=1, units=Units.CELSIUS)"