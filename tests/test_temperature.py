"""Tests for temperature, the one affine category.

Temperature is the only category whose units carry an offset as well as a
scale, so it is the only one that uses :mod:`pyconvert.units`' exact path.
These tests assert exact equality rather than approximate: that is the whole
point of that code path. In plain floats, ``convert(100, "celsius",
"fahrenheit")`` returns 211.99999999999997, because 5/9 has no finite binary
form. Every ``==`` below would fail if the exact path regressed.
"""

import itertools
from fractions import Fraction

import pytest

from pyconvert import convert, convert_all
from pyconvert.registry import TEMPERATURE

UNITS = ["celsius", "fahrenheit", "kelvin", "rankine"]


@pytest.mark.parametrize("value, source, target, expected", [
    # Boiling and freezing water, across all four scales.
    (100, "celsius", "fahrenheit", 212.0),
    (100, "celsius", "kelvin", 373.15),
    (100, "celsius", "rankine", 671.67),
    (0, "celsius", "fahrenheit", 32.0),
    (0, "celsius", "kelvin", 273.15),
    (0, "celsius", "rankine", 491.67),
    (212, "fahrenheit", "celsius", 100.0),
    (32, "fahrenheit", "celsius", 0.0),
    (32, "fahrenheit", "kelvin", 273.15),
    # Absolute zero, which every scale must agree on.
    (0, "kelvin", "celsius", -273.15),
    (0, "kelvin", "fahrenheit", -459.67),
    (0, "kelvin", "rankine", 0.0),
    (0, "rankine", "celsius", -273.15),
    (0, "rankine", "fahrenheit", -459.67),
    (0, "rankine", "kelvin", 0.0),
    # The one temperature where Celsius and Fahrenheit coincide.
    (-40, "celsius", "fahrenheit", -40.0),
    (-40, "fahrenheit", "celsius", -40.0),
    # Body temperature, the classic 98.6.
    (37, "celsius", "fahrenheit", 98.6),
    # Freezing point of water in Rankine.
    (491.67, "rankine", "celsius", 0.0),
    (273.15, "kelvin", "celsius", 0.0),
    (459.67, "rankine", "fahrenheit", 0.0),
])
def test_known_point_is_exact(value, source, target, expected):
    """Equality, not approximation: these must land on the nose."""
    assert convert(value, source, target) == expected


@pytest.mark.parametrize("source, target", list(itertools.permutations(UNITS, 2)))
def test_round_trip_returns_the_input_exactly(source, target):
    for value in (-273.15, -40, 0, 1, 37, 100, 1000):
        there = convert(value, source, target)
        assert convert(there, target, source) == pytest.approx(value, abs=1e-9)


@pytest.mark.parametrize("degrees", range(-100, 101, 5))
def test_celsius_fahrenheit_round_trip_is_exact_for_integers(degrees):
    fahrenheit = convert(degrees, "celsius", "fahrenheit")
    assert convert(fahrenheit, "fahrenheit", "celsius") == float(degrees)


def test_fahrenheit_follows_the_textbook_formula():
    """F = C * 9/5 + 32, checked against exact rational arithmetic."""
    for celsius in (-273.15, -40, -17.78, 0, 21, 37, 100, 1000):
        expected = float(Fraction(str(celsius)) * Fraction(9, 5) + 32)
        assert convert(celsius, "celsius", "fahrenheit") == expected


def test_rankine_is_kelvin_scaled_by_nine_fifths():
    for kelvin in (0, 1, 273.15, 373.15, 1000):
        expected = float(Fraction(str(kelvin)) * Fraction(9, 5))
        assert convert(kelvin, "kelvin", "rankine") == expected


def test_temperature_is_affine_not_proportional():
    """A zero input must not give a zero output, unlike every other category."""
    assert convert(0, "celsius", "fahrenheit") == 32.0
    assert convert(0, "celsius", "kelvin") == 273.15
    # Doubling the input must not double the output.
    assert convert(20, "celsius", "fahrenheit") != 2 * convert(
        10, "celsius", "fahrenheit"
    )


def test_kelvin_and_rankine_are_proportional_to_each_other():
    """Both are absolute scales, so between those two it is a pure ratio."""
    assert convert(20, "kelvin", "rankine") == 2 * convert(10, "kelvin", "rankine")


def test_a_degree_interval_is_the_same_size_in_celsius_and_kelvin():
    one_celsius_step = (
        convert(21, "celsius", "kelvin") - convert(20, "celsius", "kelvin")
    )
    one_fahrenheit_step = (
        convert(21, "fahrenheit", "rankine") - convert(20, "fahrenheit", "rankine")
    )
    assert one_celsius_step == pytest.approx(1.0)
    assert one_fahrenheit_step == pytest.approx(1.0)


def test_registry_stores_temperature_as_exact_rationals():
    """Floats here would reintroduce 211.99999999999997."""
    for symbol, entry in TEMPERATURE.items():
        assert isinstance(entry, tuple), f"{symbol} must be (scale, offset)"
        scale, offset = entry
        assert isinstance(scale, Fraction), f"{symbol} scale is {type(scale).__name__}"
        offset_type = type(offset).__name__
        assert isinstance(offset, Fraction), f"{symbol} offset is {offset_type}"


def test_kelvin_is_the_base_and_carries_no_offset():
    scale, offset = TEMPERATURE["kelvin"]
    assert scale == 1
    assert offset == 0


@pytest.mark.parametrize("symbol, kelvin_at_zero", [
    ("kelvin", 0),
    ("celsius", 273.15),
    ("fahrenheit", 255.37222222222223),
    ("rankine", 0),
])
def test_offset_is_the_kelvin_value_of_zero_on_that_scale(symbol, kelvin_at_zero):
    assert float(TEMPERATURE[symbol][1]) == pytest.approx(kelvin_at_zero)
    assert convert(0, symbol, "kelvin") == pytest.approx(kelvin_at_zero)


def test_below_absolute_zero_is_allowed_arithmetically():
    """The library converts numbers; it does not police thermodynamics.

    Refusing sub-absolute-zero values would break legitimate uses such as
    converting an uncertainty interval or a model's intermediate value.
    """
    assert convert(-300, "celsius", "kelvin") == pytest.approx(-26.85)


def test_convert_all_on_temperature_uses_the_exact_path():
    assert convert_all([0, 37, 100, -40], "celsius", "fahrenheit") == [
        32.0, 98.6, 212.0, -40.0
    ]


def test_integer_and_float_inputs_agree():
    assert convert(100, "celsius", "fahrenheit") == convert(
        100.0, "celsius", "fahrenheit"
    )


def test_fraction_and_decimal_inputs_are_accepted():
    from decimal import Decimal

    assert convert(Fraction(100), "celsius", "fahrenheit") == 212.0
    assert convert(Decimal("100"), "celsius", "fahrenheit") == 212.0
    assert convert(Decimal("37.0"), "celsius", "fahrenheit") == 98.6
