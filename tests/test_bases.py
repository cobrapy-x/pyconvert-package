"""Tests for number-base conversion."""

import random

import pytest

from pyconvert import DIGITS, MAX_BASE, MIN_BASE, convert_base

BASES = list(range(MIN_BASE, MAX_BASE + 1))


# ---------------------------------------------------------------- the spec ---
@pytest.mark.parametrize("number, from_base, to_base, expected", [
    (100, 10, 2, "1100100"),
    ("10101111", 2, 16, "AF"),
    ("FF", 16, 10, "255"),
    (1000, 10, 36, "RS"),
])
def test_documented_examples(number, from_base, to_base, expected):
    assert convert_base(number, from_base, to_base) == expected


# ------------------------------------------- agreement with Python builtins ---
@pytest.mark.parametrize("value", [0, 1, 2, 7, 8, 255, 256, 1000, 65535,
                                   123456789, 2 ** 64, 10 ** 30])
def test_matches_bin_oct_hex(value):
    assert convert_base(value, 10, 2) == format(value, "b")
    assert convert_base(value, 10, 8) == format(value, "o")
    assert convert_base(value, 10, 16) == format(value, "X")


@pytest.mark.parametrize("base", BASES)
def test_matches_int_parsing_for_every_base(base):
    """Rendering in a base then parsing with int() must return the original."""
    rng = random.Random(f"base-{base}")
    for _ in range(50):
        value = rng.randint(0, 10 ** 15)
        assert int(convert_base(value, 10, base), base) == value


@pytest.mark.parametrize("to_base", BASES)
def test_three_hop_round_trip(to_base):
    rng = random.Random(f"hop-{to_base}")
    for _ in range(30):
        value = rng.randint(-10 ** 12, 10 ** 12)
        hop1 = convert_base(value, 10, to_base)
        hop2 = convert_base(hop1, to_base, 7)
        back = convert_base(hop2, 7, 10)
        assert int(back) == value


# ------------------------------------------------------------- input forms ---
def test_input_is_case_insensitive():
    assert convert_base("ff", 16, 10) == convert_base("FF", 16, 10) == "255"
    assert convert_base("zZ", 36, 10) == "1295"


def test_output_is_always_uppercase():
    assert convert_base(255, 10, 16) == "FF"
    assert convert_base(35, 10, 36) == "Z"
    assert convert_base(1295, 10, 36) == "ZZ"


def test_underscores_are_allowed_as_separators():
    assert convert_base("1111_1111", 2, 16) == "FF"
    assert convert_base("1_000_000", 10, 10) == "1000000"


def test_surrounding_whitespace_is_ignored():
    assert convert_base("  FF  ", 16, 10) == "255"


def test_explicit_plus_sign_is_accepted():
    assert convert_base("+255", 10, 16) == "FF"


def test_integer_input_is_read_in_the_source_base():
    """An int is read as its written digits, like the string form."""
    assert convert_base(1100100, 2, 10) == "100"
    assert convert_base(1100100, 10, 10) == "1100100"


def test_result_is_always_a_string_even_for_base_ten():
    result = convert_base("FF", 16, 10)
    assert isinstance(result, str)
    assert result == "255"
    assert int(result) == 255


# -------------------------------------------------------------- negatives ----
def test_negative_sign_is_preserved():
    assert convert_base(-255, 10, 16) == "-FF"
    assert convert_base("-1100100", 2, 10) == "-100"
    assert convert_base("-0.5", 10, 2) == "-0.1"


def test_negative_zero_normalises_to_zero():
    assert convert_base("-0", 10, 2) == "0"
    assert convert_base("-0.0", 10, 2) == "0"


@pytest.mark.parametrize("base", BASES)
def test_zero_is_zero_in_every_base(base):
    assert convert_base(0, 10, base) == "0"
    assert convert_base("0", base, 10) == "0"


# ------------------------------------------------------------- fractions -----
@pytest.mark.parametrize("number, from_base, to_base, expected", [
    ("0.5", 10, 2, "0.1"),
    ("0.25", 10, 2, "0.01"),
    ("0.75", 10, 2, "0.11"),
    ("A.8", 16, 10, "10.5"),
    ("0.1", 2, 10, "0.5"),
    ("1.1", 2, 10, "1.5"),
    ("0.4", 16, 10, "0.25"),
    (".5", 10, 2, "0.1"),
    ("0.", 10, 2, "0"),
])
def test_terminating_fractions_are_exact(number, from_base, to_base, expected):
    assert convert_base(number, from_base, to_base) == expected


def test_non_terminating_fraction_is_truncated_not_wrong():
    """One tenth has no finite binary form, so it runs to `precision`."""
    assert convert_base("0.1", 10, 2) == "0.0001100110011001"
    assert convert_base("0.1", 10, 2, precision=4) == "0.0001"
    assert convert_base("0.1", 10, 2, precision=0) == "0"


def test_precision_only_limits_non_terminating_results():
    """A result that terminates early stops early, whatever precision says."""
    assert convert_base("0.5", 10, 2, precision=100) == "0.1"


@pytest.mark.parametrize("base", [2, 4, 8, 16, 32])
def test_dyadic_fractions_round_trip_through_power_of_two_bases(base):
    """Halves, quarters and eighths are exact in any power-of-two base."""
    rng = random.Random(f"dyadic-{base}")
    for _ in range(40):
        numerator = rng.randint(-10 ** 6, 10 ** 6)
        denominator = 2 ** rng.randint(0, 12)
        value = numerator / denominator
        rendered = convert_base(str(value), 10, base, precision=60)
        assert float(convert_base(rendered, base, 10, precision=60)) == value


def test_trailing_zeros_are_stripped():
    assert convert_base("0.50", 10, 10) == "0.5"
    assert convert_base("1.000", 10, 10) == "1"


# -------------------------------------------------------------- constants ----
def test_digit_alphabet_matches_the_base_limit():
    assert DIGITS == "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    assert len(DIGITS) == MAX_BASE == 36
    assert MIN_BASE == 2


@pytest.mark.parametrize("position, character", list(enumerate(
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")))
def test_each_digit_renders_at_its_own_value(position, character):
    assert convert_base(position, 10, 36) == character


def test_base_36_uses_the_whole_alphabet():
    rendered = convert_base(int("".join(DIGITS[1:]), 36), 10, 36)
    assert rendered == DIGITS[1:]
