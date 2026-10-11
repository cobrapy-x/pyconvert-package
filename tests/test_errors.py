"""Tests for the exception hierarchy and the quality of error messages.

Error text is part of the public interface here. A unit converter is mostly
used interactively, so "unknown unit 'KM' (did you mean 'km'?)" is the
difference between a two-second fix and a trip to the documentation.
"""

import itertools

import pytest

import pyconvert
from pyconvert import (
    AMBIGUOUS,
    CATEGORIES,
    IncompatibleUnitsError,
    InvalidBaseError,
    InvalidDigitError,
    PyConvertError,
    RegistryError,
    UnknownCategoryError,
    UnknownUnitError,
    convert,
    convert_all,
    convert_base,
)
from pyconvert.registry import ALIASES, BASE_UNITS, build_index, resolve

ERROR_TYPES = [
    UnknownUnitError,
    UnknownCategoryError,
    IncompatibleUnitsError,
    InvalidBaseError,
    InvalidDigitError,
    RegistryError,
]


# ------------------------------------------------------------- hierarchy -----
@pytest.mark.parametrize("error_type", ERROR_TYPES)
def test_every_error_subclasses_the_package_base(error_type):
    """One except clause must be able to catch everything this library raises."""
    assert issubclass(error_type, PyConvertError)


@pytest.mark.parametrize("error_type, builtin", [
    (UnknownUnitError, KeyError),
    (UnknownCategoryError, KeyError),
    (InvalidBaseError, ValueError),
    (InvalidDigitError, ValueError),
    (RegistryError, RuntimeError),
])
def test_errors_also_subclass_the_expected_builtin(error_type, builtin):
    """Code written against builtin exception types keeps working."""
    assert issubclass(error_type, builtin)


def test_unknown_unit_is_catchable_as_keyerror():
    with pytest.raises(KeyError):
        convert(1, "km", "nonexistent")


def test_unknown_unit_str_is_not_double_quoted():
    """KeyError.__str__ would wrap the message in a second set of quotes."""
    error = UnknownUnitError("zzz")
    assert str(error) == "unknown unit 'zzz'"


# -------------------------------------------------------- unknown units ------
def test_unknown_unit_names_the_offending_symbol():
    with pytest.raises(UnknownUnitError, match="nonexistent"):
        convert(1, "km", "nonexistent")


@pytest.mark.parametrize("typo, expected", [
    ("KM", "km"),
    ("Km", "km"),
    ("KG", "kg"),
    ("MPH", "mph"),
])
def test_wrong_case_is_suggested_back(typo, expected):
    """Wrong case is the most common mistake, and a plain ratio misses it."""
    with pytest.raises(UnknownUnitError) as info:
        resolve(typo)
    assert expected in info.value.suggestions
    assert "did you mean" in str(info.value)


@pytest.mark.parametrize("typo, expected", [
    ("kilomter", "kilometer"),
    ("metre ", "metre"),
    ("kilogrm", "kilogram"),
])
def test_near_misses_are_suggested(typo, expected):
    with pytest.raises(UnknownUnitError) as info:
        resolve(typo)
    assert expected in info.value.suggestions


def test_nonsense_gets_no_misleading_suggestion():
    with pytest.raises(UnknownUnitError) as info:
        resolve("qqqqqqqq")
    assert info.value.suggestions == []
    assert "did you mean" not in str(info.value)


@pytest.mark.parametrize("value", [42, None, 3.5, [], {}])
def test_non_string_units_are_rejected(value):
    with pytest.raises(UnknownUnitError):
        resolve(value)


# ------------------------------------------- deliberately ambiguous units ----
@pytest.mark.parametrize("spelling", sorted(AMBIGUOUS))
def test_ambiguous_spelling_explains_the_alternatives(spelling):
    """These are refused on purpose, so the message must say what to use."""
    with pytest.raises(UnknownUnitError) as info:
        resolve(spelling)
    message = str(info.value)
    assert spelling in message
    assert info.value.hint == AMBIGUOUS[spelling]
    # No fuzzy guess: for "C" that would unhelpfully offer "c", the speed of light.
    assert "did you mean" not in message


def test_ambiguous_hint_beats_a_misleading_fuzzy_match():
    with pytest.raises(UnknownUnitError) as info:
        resolve("C")
    assert "celsius" in str(info.value)
    assert "coulomb" in str(info.value)


def test_ton_names_all_three_masses():
    with pytest.raises(UnknownUnitError) as info:
        convert(1, "ton", "kg")
    message = str(info.value)
    for alternative in ("t", "ton_us", "ton_uk"):
        assert alternative in message


# ------------------------------------------------- incompatible categories ---
def test_incompatible_units_names_both_categories():
    with pytest.raises(IncompatibleUnitsError) as info:
        convert(1, "kg", "m")
    message = str(info.value)
    assert "mass" in message
    assert "length" in message
    assert info.value.source_category == "mass"
    assert info.value.target_category == "length"


CATEGORY_PAIRS = list(itertools.combinations(sorted(CATEGORIES), 2))


@pytest.mark.parametrize("first, second", CATEGORY_PAIRS)
def test_no_cross_category_pair_is_ever_allowed(first, second):
    """Every unit of one category against every unit of another must refuse."""
    for source in CATEGORIES[first]:
        for target in CATEGORIES[second]:
            with pytest.raises(IncompatibleUnitsError):
                convert(1, source, target)


def test_cross_category_is_refused_before_arithmetic():
    """A bad pair must raise even for a value that would be valid."""
    with pytest.raises(IncompatibleUnitsError):
        convert(0, "celsius", "metre")


# ------------------------------------------------------- non-numeric input ---
@pytest.mark.parametrize("value", ["1", "x", None, [], {}, complex(1, 2)])
def test_non_numeric_value_raises_typeerror(value):
    with pytest.raises(TypeError, match="real number"):
        convert(value, "km", "mi")


def test_bool_is_rejected_despite_being_an_int():
    """True would silently mean one metre, which is never what was meant."""
    with pytest.raises(TypeError, match="bool"):
        convert(True, "m", "cm")


def test_convert_all_reports_a_bad_element():
    with pytest.raises(TypeError, match="every value"):
        convert_all([1, 2, "three"], "m", "cm")


# ------------------------------------------------------------ bad bases ------
@pytest.mark.parametrize("base", [0, 1, 37, 64, -2, 100])
def test_base_outside_two_to_thirty_six_is_rejected(base):
    with pytest.raises(InvalidBaseError, match="from 2 to 36"):
        convert_base(1, 10, base)
    with pytest.raises(InvalidBaseError):
        convert_base(1, base, 10)


@pytest.mark.parametrize("base", [10.0, "10", None, True, False])
def test_non_integer_base_is_rejected(base):
    with pytest.raises(InvalidBaseError):
        convert_base(1, 10, base)


def test_invalid_base_records_the_value():
    with pytest.raises(InvalidBaseError) as info:
        convert_base(1, 10, 99)
    assert info.value.base == 99


# ----------------------------------------------------------- bad digits ------
@pytest.mark.parametrize("number, base, bad_digit", [
    ("G", 16, "G"),
    ("12", 2, "2"),
    ("9", 8, "9"),
    ("2", 2, "2"),
    ("1!1", 10, "!"),
    ("1 1", 10, " "),
])
def test_digit_invalid_for_the_base_is_named(number, base, bad_digit):
    with pytest.raises(InvalidDigitError) as info:
        convert_base(number, base, 10)
    assert info.value.digit == bad_digit
    assert repr(bad_digit) in str(info.value)
    assert f"base {base}" in str(info.value)


@pytest.mark.parametrize("number", ["", "   ", "_", "-", "+"])
def test_input_with_no_digits_says_so(number):
    with pytest.raises(InvalidDigitError, match="no digits"):
        convert_base(number, 10, 2)


def test_more_than_one_decimal_point_is_rejected():
    with pytest.raises(InvalidDigitError):
        convert_base("1.2.3", 10, 2)


@pytest.mark.parametrize("number", [1.5, None, [], {}, complex(1, 2)])
def test_non_integer_non_string_number_raises_typeerror(number):
    with pytest.raises(TypeError):
        convert_base(number, 10, 2)


def test_float_input_is_told_to_use_a_string():
    with pytest.raises(TypeError, match="pass a fractional value as a string"):
        convert_base(10.5, 10, 2)


@pytest.mark.parametrize("precision", [-1, 1.5, "4", None, True])
def test_bad_precision_is_rejected(precision):
    with pytest.raises(ValueError, match="precision"):
        convert_base(1, 10, 2, precision=precision)


# ----------------------------------------------------- unknown categories ----
@pytest.mark.parametrize("name", ["mazz", "", "Length", 7, "temperatures"])
def test_unknown_category_lists_the_real_ones(name):
    with pytest.raises(UnknownCategoryError) as info:
        pyconvert.list_units(name)
    assert "available" in str(info.value)
    assert "length" in str(info.value)


def test_list_units_with_no_argument_returns_every_unit():
    """``None`` is the documented default meaning "all", not a bad category."""
    assert pyconvert.list_units(None) == pyconvert.list_units()
    assert len(pyconvert.list_units(None)) == sum(len(t) for t in CATEGORIES.values())


def test_base_unit_validates_its_category():
    with pytest.raises(UnknownCategoryError):
        pyconvert.base_unit("nope")


# ------------------------------------------------- registry self-validation ---
def test_the_shipped_registry_reports_no_problems():
    assert build_index(CATEGORIES, ALIASES, BASE_UNITS)[1] == []


def test_duplicate_symbol_across_categories_is_reported():
    _, problems = build_index(
        {"alpha": {"x": 1.0}, "beta": {"x": 1.0}}, {}, {"alpha": "x", "beta": "x"}
    )
    assert problems == ["symbol 'x' is defined in both 'alpha' and 'beta'"]


def test_alias_pointing_at_a_missing_unit_is_reported():
    _, problems = build_index({"alpha": {"x": 1.0}}, {"q": "ghost"}, {"alpha": "x"})
    assert problems == ["alias 'q' points at unknown unit 'ghost'"]


def test_alias_shadowing_a_canonical_symbol_is_reported():
    _, problems = build_index({"alpha": {"x": 1.0}}, {"x": "x"}, {"alpha": "x"})
    assert len(problems) == 1
    assert "shadows" in problems[0]


def test_base_unit_with_a_scale_other_than_one_is_reported():
    _, problems = build_index({"alpha": {"x": 5.0}}, {}, {"alpha": "x"})
    assert len(problems) == 1
    assert "scale 1 and offset 0" in problems[0]


def test_missing_base_unit_declaration_is_reported():
    _, problems = build_index({"alpha": {"x": 1.0}}, {}, {})
    assert problems == ["category 'alpha' has no declared base unit"]


def test_base_unit_absent_from_its_table_is_reported():
    _, problems = build_index({"alpha": {"x": 1.0}}, {}, {"alpha": "y"})
    assert "base unit 'y' is not present in 'alpha'" in problems


def test_all_problems_are_collected_not_just_the_first():
    """Editing the registry should surface every mistake in one run."""
    _, problems = build_index(
        {"alpha": {"x": 1.0}, "beta": {"x": 1.0, "y": 2.0}},
        {"ghost": "missing", "x": "x"},
        {"alpha": "x", "beta": "x"},
    )
    assert len(problems) >= 3


def test_registry_error_message_lists_the_problems():
    error = RegistryError("the unit registry is inconsistent:\n  - first\n  - second")
    assert "first" in str(error)
    assert "second" in str(error)
