"""Tests for unit conversion and the registry that backs it."""

import itertools
import random

import pytest

import pyconvert
from pyconvert import convert, convert_all
from pyconvert.registry import ALIASES, BASE_UNITS, CATEGORIES, build_index, resolve

MULTIPLICATIVE = {name: table for name, table in CATEGORIES.items()
                  if name != "temperature"}
ALL_UNITS = [(category, symbol)
             for category, table in CATEGORIES.items() for symbol in table]


# ---------------------------------------------------------------- the spec ---
@pytest.mark.parametrize("value, source, target, expected", [
    (100, "km", "mi", 62.13711922373339),
    (100, "celsius", "fahrenheit", 212.0),
    (1024, "MiB", "GiB", 1.0),
])
def test_documented_examples(value, source, target, expected):
    """The examples in the README and docstrings must stay true."""
    assert convert(value, source, target) == expected


# ------------------------------------------------- definitional identities ---
# Relationships fixed by definition, independent of the metre or the kilogram.
# An inverted factor (the bug that shipped in v0.1.0, where metre->feet held
# 0.3048 instead of 3.28084) fails here even though it would round-trip fine.
@pytest.mark.parametrize("value, source, target, expected", [
    (1, "m", "cm", 100),
    (1, "mi", "ft", 5280),
    (1, "mi", "yd", 1760),
    (1, "ft", "in", 12),
    (1, "yd", "ft", 3),
    (1, "in", "thou", 1000),
    (1, "fathom", "ft", 6),
    (1, "furlong", "ft", 660),
    (1, "nmi", "m", 1852),
    (1, "lb", "oz", 16),
    (1, "st", "lb", 14),
    (1, "ton_us", "lb", 2000),
    (1, "ton_uk", "lb", 2240),
    (1, "t", "kg", 1000),
    (1, "t", "quintal", 10),
    (1, "ha", "m2", 10_000),
    (1, "ac", "ft2", 43_560),
    (1, "are", "m2", 100),
    (1, "L", "mL", 1000),
    (1, "m3", "L", 1000),
    (1, "gal_us", "qt_us", 4),
    (1, "gal_us", "floz_us", 128),
    (1, "gal_us", "in3", 231),
    (1, "gal_imp", "floz_imp", 160),
    (1, "bbl", "gal_us", 42),
    (1, "kcal", "cal", 1000),
    (1, "kWh", "MJ", 3.6),
    (1, "Wh", "J", 3600),
    (1, "kWh", "Wh", 1000),
    (1, "kW", "W", 1000),
    (1, "atm", "Pa", 101_325),
    (1, "atm", "torr", 760),
    (1, "bar", "kPa", 100),
    (1, "inHg", "mmHg", 25.4),
    (1, "d", "h", 24),
    (1, "d", "min", 1440),
    (1, "h", "s", 3600),
    (1, "week", "d", 7),
    (1, "fortnight", "d", 14),
    (1, "yr", "d", 365.25),
    (1, "Hz", "rpm", 60),
    (1, "B", "bit", 8),
    (1, "kB", "B", 1000),
    (1, "KiB", "B", 1024),
    (1, "GiB", "MiB", 1024),
    (1, "GB", "MB", 1000),
    (1, "turn", "deg", 360),
    (1, "deg", "arcmin", 60),
    (1, "arcmin", "arcsec", 60),
    (1, "A", "mA", 1000),
    (1, "kV", "V", 1000),
])
def test_definitional_identity(value, source, target, expected):
    assert convert(value, source, target) == pytest.approx(expected, rel=1e-12)


@pytest.mark.parametrize("unit, expected", [
    # Values that are exact by international definition, so equality is fair.
    ("in", 0.0254), ("ft", 0.3048), ("yd", 0.9144), ("mi", 1609.344),
    ("nmi", 1852.0),
])
def test_exact_length_definitions(unit, expected):
    assert convert(1, unit, "m") == expected


@pytest.mark.parametrize("unit, base, expected", [
    # Conversions TO a category's base unit divide by exactly 1.0, so the only
    # rounding is the factor's own -- these must be exactly equal.
    ("lb", "kg", 0.45359237),
    ("oz", "kg", 0.028349523125),
    ("gal_us", "m3", 0.003785411784),
    ("gal_imp", "m3", 0.00454609),
    ("BTU", "J", 1055.05585262),
    ("hp", "W", 745.6998715822702),
    ("hp_metric", "W", 735.49875),
    ("psi", "Pa", 6894.757293168362),
    ("ac", "m2", 4046.8564224),
    ("ft3", "m3", 0.028316846592),
    ("mmHg", "Pa", 133.322387415),
    ("eV", "J", 1.602176634e-19),
])
def test_exact_definition_against_base_unit(unit, base, expected):
    assert convert(1, unit, base) == expected


def test_results_are_ieee_doubles_and_we_do_not_pretend_otherwise():
    """Between two non-base units the result carries normal float error.

    One imperial gallon is exactly 4.54609 L, but the factors are stored
    relative to the cubic metre, and 0.00454609 / 0.001 lands one unit in the
    last place below 4.54609. Converting the engine to exact rationals would
    remove this -- and would also change ``100 km -> mi`` from the documented
    62.13711922373339 to 62.1371192237334, as well as costing roughly ten
    times the runtime. The float path stays; exactness is guaranteed where it
    is cheap (conversions to a base unit) and where the error would otherwise
    be visible to everyone (temperature, which uses the exact path).
    """
    assert convert(1, "gal_imp", "L") == pytest.approx(4.54609, rel=1e-15)
    assert convert(1, "gal_imp", "L") != 4.54609


def test_quintal_is_one_hundred_kilograms():
    """v0.1.0 had this as 1000 kg, wrong by a factor of ten."""
    assert convert(1, "quintal", "kg") == 100.0


def test_metre_to_feet_is_not_inverted():
    """The v0.1.0 bug, pinned: one metre is more than three feet, not a third."""
    assert convert(1, "m", "ft") == pytest.approx(3.280839895, rel=1e-9)
    assert convert(1, "ft", "m") == 0.3048


# ----------------------------------------------- structural self-consistency ---
@pytest.mark.parametrize("category, symbol", ALL_UNITS, ids=lambda v: str(v))
def test_unit_round_trips_through_its_base(category, symbol):
    base = BASE_UNITS[category]
    there_and_back = convert(convert(1.0, symbol, base), base, symbol)
    assert there_and_back == pytest.approx(1.0, abs=1e-12)


@pytest.mark.parametrize("category", sorted(MULTIPLICATIVE))
def test_every_pair_in_category_is_mutually_consistent(category):
    """a->b and b->a must be reciprocal for every pair, not just via the base."""
    for a, b in itertools.permutations(MULTIPLICATIVE[category], 2):
        product = convert(1, a, b) * convert(1, b, a)
        assert product == pytest.approx(1.0, rel=1e-9), f"{a} <-> {b}"


@pytest.mark.parametrize("category", sorted(CATEGORIES))
def test_conversion_is_transitive(category):
    """a->c must agree with a->b->c."""
    symbols = list(CATEGORIES[category])
    if len(symbols) < 3:
        pytest.skip(f"{category} has fewer than three units")
    rng = random.Random(f"transitivity-{category}")
    for _ in range(200):
        a, b, c = rng.sample(symbols, 3)
        value = rng.uniform(-1000, 1000)
        assert convert(value, a, c) == pytest.approx(
            convert(convert(value, a, b), b, c), rel=1e-9
        ), f"{value} {a}->{b}->{c}"


@pytest.mark.parametrize("category, symbol", ALL_UNITS, ids=lambda v: str(v))
def test_identity_conversion_returns_the_value_unchanged(category, symbol):
    assert convert(12.5, symbol, symbol) == 12.5


def test_alias_conversion_equals_canonical_conversion():
    for alias, canonical in ALIASES.items():
        assert convert(3, alias, canonical) == 3.0, alias


# ------------------------------------------------------------------ aliases ---
@pytest.mark.parametrize("spelling, canonical", [
    ("kilometre", "km"), ("kilometer", "km"), ("meters", "m"), ("micron", "um"),
    ("mile", "mi"), ("lbs", "lb"), ("tonne", "t"), ("amu", "u"),
    ("m²", "m2"), ("m^2", "m2"), ("sqft", "ft2"), ("hectare", "ha"),
    ("m³", "m3"), ("cc", "cm3"), ("litre", "L"), ("gal", "gal_us"),
    ("°C", "celsius"), ("degF", "fahrenheit"), ("K", "kelvin"),
    ("hr", "h"), ("KB", "kB"), ("gibibyte", "GiB"), ("°", "deg"),
    ("PS", "hp_metric"), ("HP", "hp"), ("PSI", "psi"), ("Cal", "kcal"),
    ("amps", "A"), ("millivolt", "mV"), ("knots", "kn"), ("kph", "km/h"),
])
def test_alias_resolves_to_canonical(spelling, canonical):
    assert resolve(spelling)[0] == canonical


@pytest.mark.parametrize("ascii_name", ["us", "um", "ug", "uA", "uV", "uW", "uL"])
def test_both_micro_signs_resolve_identically(ascii_name):
    """MICRO SIGN (U+00B5) and GREEK SMALL LETTER MU (U+03BC) look identical."""
    micro_sign = "µ" + ascii_name[1:]
    greek_mu = "μ" + ascii_name[1:]
    assert resolve(micro_sign)[0] == ascii_name
    assert resolve(greek_mu)[0] == ascii_name
    assert micro_sign != greek_mu  # genuinely different strings


def test_bare_u_is_the_atomic_mass_unit_not_a_micro_prefix():
    assert resolve("u")[1] == "mass"


# --------------------------------------------------------- case sensitivity ---
@pytest.mark.parametrize("small, large, ratio", [
    ("mW", "MW", 1e9),
    ("mHz", "MHz", 1e9),
    ("mV", "MV", 1e9),
])
def test_milli_and_mega_stay_distinct(small, large, ratio):
    assert convert(1, large, small) == pytest.approx(ratio, rel=1e-12)


def test_decimal_and_binary_storage_prefixes_differ():
    assert convert(1, "KiB", "kB") == 1.024
    assert convert(1, "kB", "B") == 1000.0
    assert convert(1, "KiB", "B") == 1024.0


def test_picosecond_and_metric_horsepower_are_different_categories():
    assert pyconvert.category_of("ps") == "time"
    assert pyconvert.category_of("PS") == "power"


# ------------------------------------------------------------- convenience ---
def test_convert_all_matches_convert():
    values = [0, 100, 37, -40]
    assert convert_all(values, "celsius", "fahrenheit") == [
        convert(v, "celsius", "fahrenheit") for v in values
    ]


def test_convert_all_accepts_any_iterable():
    assert convert_all(range(3), "m", "cm") == [0.0, 100.0, 200.0]
    assert convert_all([], "m", "cm") == []


@pytest.mark.parametrize("source, target, expected", [
    ("km", "mi", True), ("km", "furlong", True), ("celsius", "kelvin", True),
    ("km", "kg", False), ("B", "bit", True), ("B", "Hz", False),
    ("km", "nonsense", False), ("nonsense", "km", False), (None, "km", False),
])
def test_is_convertible(source, target, expected):
    assert pyconvert.is_convertible(source, target) is expected


# ---------------------------------------------------------- introspection ----
def test_list_categories_covers_the_registry():
    assert pyconvert.list_categories() == sorted(CATEGORIES)
    assert len(pyconvert.list_categories()) == 15


def test_list_units_for_one_category_and_for_all():
    assert pyconvert.list_units("temperature") == [
        "celsius", "fahrenheit", "kelvin", "rankine"
    ]
    assert len(pyconvert.list_units()) == sum(len(t) for t in CATEGORIES.values())


@pytest.mark.parametrize("category", sorted(CATEGORIES))
def test_base_unit_belongs_to_its_category(category):
    base = pyconvert.base_unit(category)
    assert base in CATEGORIES[category]
    assert pyconvert.category_of(base) == category


def test_units_submodule_is_not_shadowed_by_a_function():
    """Re-exporting a function named ``units`` would hide ``pyconvert.units``."""
    import types

    import pyconvert.units

    assert isinstance(pyconvert.units, types.ModuleType)
    assert callable(pyconvert.list_units)


# ------------------------------------------------------- registry integrity ---
def test_registry_is_internally_consistent():
    _, problems = build_index(CATEGORIES, ALIASES, BASE_UNITS)
    assert problems == []


def test_no_symbol_is_claimed_by_two_categories():
    seen = {}
    for category, table in CATEGORIES.items():
        for symbol in table:
            assert symbol not in seen, (
                f"{symbol!r} in both {seen.get(symbol)!r} and {category!r}"
            )
            seen[symbol] = category


def test_no_alias_shadows_a_canonical_symbol():
    canonical = {s for table in CATEGORIES.values() for s in table}
    assert not (set(ALIASES) & canonical)


def test_every_alias_points_at_a_real_unit():
    canonical = {s for table in CATEGORIES.values() for s in table}
    assert not (set(ALIASES.values()) - canonical)


def test_deliberately_ambiguous_spellings_are_not_valid_units():
    """Nothing in AMBIGUOUS may also be resolvable, or the hint is unreachable."""
    for spelling in pyconvert.AMBIGUOUS:
        assert spelling not in ALIASES
        assert not any(spelling in table for table in CATEGORIES.values())


@pytest.mark.parametrize("category", sorted(CATEGORIES))
def test_base_unit_has_unit_scale_and_zero_offset(category):
    from pyconvert.registry import as_affine

    scale, offset = as_affine(CATEGORIES[category][BASE_UNITS[category]])
    assert scale == 1
    assert offset == 0


@pytest.mark.parametrize("category", sorted(MULTIPLICATIVE))
def test_multiplicative_factors_are_positive_and_finite(category):
    import math

    for symbol, entry in MULTIPLICATIVE[category].items():
        assert not isinstance(entry, tuple), f"{symbol} unexpectedly affine"
        assert entry > 0, f"{symbol} has non-positive factor {entry}"
        assert math.isfinite(entry), f"{symbol} is not finite"


# --------------------------------------------------------- docs stay in sync ---
def test_every_unit_is_documented_in_the_readme():
    """Adding a unit without listing it in the README should fail the build.

    The README's unit table is generated from this registry, so this catches a
    unit added later by hand without regenerating it.
    """
    import pathlib

    readme = pathlib.Path(__file__).resolve().parent.parent / "README.md"
    if not readme.exists():  # installed sdist without the README alongside
        pytest.skip("README.md is not present in this checkout")
    text = readme.read_text(encoding="utf-8")
    missing = [symbol for _, symbol in ALL_UNITS if f"`{symbol}`" not in text]
    assert not missing, f"units missing from README.md: {missing}"


def test_every_category_is_documented_in_the_readme():
    import pathlib

    readme = pathlib.Path(__file__).resolve().parent.parent / "README.md"
    if not readme.exists():
        pytest.skip("README.md is not present in this checkout")
    text = readme.read_text(encoding="utf-8").lower()
    missing = [c for c in CATEGORIES if c not in text]
    assert not missing, f"categories missing from README.md: {missing}"
