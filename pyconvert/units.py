"""Unit conversion: the engine that turns registry factors into answers.

The public entry point is :func:`convert`::

    >>> convert(100, "km", "mi")
    62.13711922373339
    >>> convert(100, "celsius", "fahrenheit")
    212.0
    >>> convert(1024, "MiB", "GiB")
    1.0

There is no category argument. Every unit symbol is unique across the whole
registry, so the category is looked up rather than supplied -- and converting
between two categories is an error rather than a meaningless number.
"""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
from numbers import Real

from .exceptions import IncompatibleUnitsError
from .registry import (
    BASE_UNITS,
    CATEGORIES,
    as_affine,
    category_of,
    resolve,
    units_in,
)

__all__ = [
    "base_unit",
    "category_of",
    "convert",
    "convert_all",
    "is_convertible",
    "list_categories",
    "list_units",
]


def _as_number(value: object, argument: str = "value"):
    """Validate and normalise a numeric input before any arithmetic.

    ``bool`` is rejected on purpose: it is a subclass of ``int``, so
    ``convert(True, "m", "cm")`` would otherwise quietly mean one metre.

    ``Decimal`` is accepted but converted, because it is not a
    ``numbers.Real`` and refuses to be multiplied by a ``float`` -- it would
    fail deep inside the arithmetic rather than here. ``Fraction(Decimal)`` is
    lossless, so nothing is given up by normalising it.
    """
    if isinstance(value, bool):
        raise TypeError(f"{argument} must be a real number, got bool")
    if isinstance(value, Decimal):
        return Fraction(value) if value.is_finite() else float(value)
    if not isinstance(value, Real):
        raise TypeError(
            f"{argument} must be a real number, got {type(value).__name__}"
        )
    return value


def _to_fraction(value) -> Fraction:
    """Convert a value to an exact ``Fraction``.

    Goes via ``str`` for floats so that 0.1 becomes 1/10 -- the decimal the
    caller wrote -- rather than the binary approximation they did not.
    """
    if isinstance(value, Fraction):
        return value
    return Fraction(str(value))


def convert(value: Real, from_unit: str, to_unit: str) -> float:
    """Convert *value* from one unit to another and return a ``float``.

    Both units must belong to the same category; the category itself is never
    passed in, it is looked up from the symbols.

    >>> convert(100, "km", "mi")
    62.13711922373339
    >>> convert(1, "gal_us", "L")
    3.785411784
    >>> convert(-40, "celsius", "fahrenheit")
    -40.0

    Spellings are flexible -- long names, plurals and the typeable forms of
    symbols all work:

    >>> convert(1, "mile", "kilometre")
    1.609344
    >>> convert(5000, "m²", "hectare")
    0.5

    Mixing categories is refused rather than guessed:

    >>> convert(1, "kg", "m")
    Traceback (most recent call last):
        ...
    pyconvert.exceptions.IncompatibleUnitsError: cannot convert 'kg' to 'm': \
'kg' measures mass, 'm' measures length

    :raises TypeError: if *value* is not a real number.
    :raises UnknownUnitError: if either unit is not in the registry.
    :raises IncompatibleUnitsError: if the two units measure different things.
    """
    value = _as_number(value)
    src, src_category, src_entry = resolve(from_unit)
    dst, dst_category, dst_entry = resolve(to_unit)

    if src_category != dst_category:
        raise IncompatibleUnitsError(src, dst, src_category, dst_category)

    # Identity: skip the arithmetic so the value cannot pick up rounding noise
    # on the way through (this also makes convert(x, u, u) == float(x) exactly).
    if src == dst:
        return float(value)

    src_scale, src_offset = as_affine(src_entry)
    dst_scale, dst_offset = as_affine(dst_entry)

    # Exact path -- taken whenever either unit is stored as an affine
    # ``(scale, offset)`` entry, which today means temperature. The test is the
    # entry's shape rather than a non-zero offset, deliberately: rankine's
    # offset IS zero, so an offset test would send kelvin->rankine down the
    # float path and make it the one temperature pair carrying rounding error.
    # In plain floats, 100 celsius to fahrenheit gives 211.99999999999997
    # because 5/9 has no finite binary form; here the division by 9 stays a
    # ratio until the single float() at the end.
    if isinstance(src_entry, tuple) or isinstance(dst_entry, tuple):
        try:
            exact = _to_fraction(value)
        except (ValueError, OverflowError):
            pass  # infinity or NaN: no rational form, so use the float path
        else:
            return float(
                (
                    exact * Fraction(src_scale)
                    + Fraction(src_offset)
                    - Fraction(dst_offset)
                )
                / Fraction(dst_scale)
            )

    # Ratio path -- no offsets anywhere, so the conversion is a single ratio.
    # This is every category except temperature, and it is what keeps the
    # common case around ten times faster than exact arithmetic.
    return float(value * src_scale / dst_scale)


def convert_all(values, from_unit: str, to_unit: str) -> list[float]:
    """Convert an iterable of values between the same pair of units.

    The units are resolved once instead of once per value.

    >>> convert_all([0, 100, 37], "celsius", "fahrenheit")
    [32.0, 212.0, 98.6]
    """
    values = list(values)
    for value in values:
        _as_number(value, "every value")
    src, src_category, _ = resolve(from_unit)
    dst, dst_category, _ = resolve(to_unit)
    if src_category != dst_category:
        raise IncompatibleUnitsError(src, dst, src_category, dst_category)
    return [convert(value, src, dst) for value in values]


def is_convertible(from_unit: str, to_unit: str) -> bool:
    """Return whether two units can be converted between each other.

    Unknown units give ``False`` rather than raising, so this is safe to use
    as a test.

    >>> is_convertible("km", "mi"), is_convertible("km", "kg")
    (True, False)
    >>> is_convertible("km", "furlong"), is_convertible("km", "nonsense")
    (True, False)
    """
    try:
        return resolve(from_unit)[1] == resolve(to_unit)[1]
    except Exception:
        return False


def list_categories() -> list[str]:
    """Return the names of every category, sorted.

    >>> list_categories()[:4]
    ['angle', 'area', 'current', 'energy']
    """
    return sorted(CATEGORIES)


def list_units(category: str | None = None) -> list[str]:
    """Return canonical unit symbols -- for one category, or all of them.

    Named ``list_units`` rather than ``units`` so that it does not shadow the
    ``pyconvert.units`` module when re-exported at package level.

    >>> list_units("temperature")
    ['celsius', 'fahrenheit', 'kelvin', 'rankine']
    >>> len(list_units()) > 150
    True
    """
    if category is None:
        return sorted(symbol for table in CATEGORIES.values() for symbol in table)
    return units_in(category)


def base_unit(category: str) -> str:
    """Return the unit a category's factors are expressed relative to.

    >>> base_unit("pressure"), base_unit("storage")
    ('Pa', 'B')
    """
    units_in(category)  # validates the category name, raising if unknown
    return BASE_UNITS[category]
