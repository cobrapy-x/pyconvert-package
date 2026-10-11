"""Number-base conversion between any two bases from 2 to 36.

The public entry point is :func:`convert_base`::

    >>> convert_base(100, 10, 2)
    '1100100'
    >>> convert_base("10101111", 2, 16)
    'AF'
    >>> convert_base("FF", 16, 10)
    '255'
    >>> convert_base(1000, 10, 36)
    'RS'

The result is always a string, including when the target base is 10. A base-10
result is a string too because that is the only answer type that is true for
every base: once ``'AF'`` and ``'1100100'`` are strings, returning an ``int``
for base 10 alone would make the return type depend on an argument's value.
Call ``int(...)`` on it if you want a number back.

This module is named ``bases`` rather than ``numbers`` because Python's standard
library already has a ``numbers`` module -- the one holding ``numbers.Real``,
which :mod:`pyconvert.units` imports.
"""

from __future__ import annotations

from fractions import Fraction

from .exceptions import InvalidBaseError, InvalidDigitError

__all__ = ["DIGITS", "MAX_BASE", "MIN_BASE", "convert_base"]

#: The digit alphabet: 0-9 then A-Z, which is what caps the base at 36.
DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

MIN_BASE = 2
MAX_BASE = 36

#: Digit character -> value, accepting either case on input.
_VALUES = {character: value for value, character in enumerate(DIGITS)}
_VALUES.update({character.lower(): value for value, character in enumerate(DIGITS)})

#: Default number of fractional digits produced for a non-terminating result.
DEFAULT_PRECISION = 16


def _check_base(base: object, argument: str) -> int:
    """Validate a base, rejecting bools along with everything else non-integer."""
    if isinstance(base, bool) or not isinstance(base, int):
        raise InvalidBaseError(base, MIN_BASE, MAX_BASE)
    if not MIN_BASE <= base <= MAX_BASE:
        raise InvalidBaseError(base, MIN_BASE, MAX_BASE)
    return base


def _parse(number: object, base: int) -> Fraction:
    """Read *number* in *base* and return its exact value as a ``Fraction``.

    Exact on purpose: a fractional part converted through ``float`` would pick
    up binary rounding error before the output digits are even generated.
    """
    if isinstance(number, str):
        text = number.strip().replace("_", "")
    elif isinstance(number, int) and not isinstance(number, bool):
        # An int is read as its written digits, so convert_base(1100100, 2, 10)
        # treats those digits as binary, matching the string form.
        text = str(number)
    else:
        raise TypeError(
            "number must be an int or a str, got "
            f"{type(number).__name__}"
            + (
                " -- pass a fractional value as a string, e.g. '10.5'"
                if isinstance(number, float)
                else ""
            )
        )

    sign = 1
    if text[:1] in ("+", "-"):
        if text[0] == "-":
            sign = -1
        text = text[1:]

    if text.count(".") > 1:
        raise InvalidDigitError(".", base, number)

    whole_text, _, fraction_text = text.partition(".")
    if not whole_text and not fraction_text:
        raise InvalidDigitError(text, base, number)

    total = Fraction(0)
    for character in whole_text:
        value = _VALUES.get(character)
        if value is None or value >= base:
            raise InvalidDigitError(character, base, number)
        total = total * base + value

    if fraction_text:
        place = Fraction(1)
        for character in fraction_text:
            value = _VALUES.get(character)
            if value is None or value >= base:
                raise InvalidDigitError(character, base, number)
            place /= base
            total += value * place

    return sign * total


def _format(quantity: Fraction, base: int, precision: int) -> str:
    """Render an exact *quantity* in *base*, to at most *precision* fraction digits."""
    sign = "-" if quantity < 0 else ""
    quantity = abs(quantity)

    whole = quantity.numerator // quantity.denominator
    remainder = quantity - whole

    if whole == 0:
        digits = "0"
    else:
        collected = []
        while whole:
            whole, digit = divmod(whole, base)
            collected.append(DIGITS[digit])
        digits = "".join(reversed(collected))

    if remainder:
        collected = []
        for _ in range(precision):
            remainder *= base
            digit = remainder.numerator // remainder.denominator
            collected.append(DIGITS[digit])
            remainder -= digit
            if remainder == 0:
                break
        fraction_digits = "".join(collected).rstrip("0")
        if fraction_digits:
            digits += "." + fraction_digits

    return sign + digits


def convert_base(
    number: int | str,
    from_base: int,
    to_base: int,
    precision: int = DEFAULT_PRECISION,
) -> str:
    """Convert *number* from one base to another and return a string.

    *number* is an ``int`` or a ``str``. Input digits may be either case;
    output digits are always uppercase. Underscores are allowed as separators,
    as in Python's own numeric literals.

    >>> convert_base(100, 10, 2)
    '1100100'
    >>> convert_base("10101111", 2, 16)
    'AF'
    >>> convert_base("FF", 16, 10)
    '255'
    >>> convert_base(1000, 10, 36)
    'RS'

    Lowercase input and separators are fine, and so are negatives:

    >>> convert_base("ff", 16, 2)
    '11111111'
    >>> convert_base("1111_1111", 2, 16)
    'FF'
    >>> convert_base(-255, 10, 16)
    '-FF'

    Fractional parts are converted too, exactly where the result terminates:

    >>> convert_base("0.5", 10, 2)
    '0.1'
    >>> convert_base("A.8", 16, 10)
    '10.5'
    >>> convert_base("0.1", 10, 2)
    '0.0001100110011001'

    That last result is truncated, not wrong: one tenth has no finite binary
    form, so it runs to *precision* digits and stops.

    >>> convert_base("0.1", 10, 2, precision=4)
    '0.0001'

    :param precision: maximum fractional digits for a non-terminating result.
    :raises InvalidBaseError: if either base is not an integer from 2 to 36.
    :raises InvalidDigitError: if a digit is not valid in *from_base*.
    :raises TypeError: if *number* is neither an ``int`` nor a ``str``.
    """
    _check_base(from_base, "from_base")
    _check_base(to_base, "to_base")
    if isinstance(precision, bool) or not isinstance(precision, int) or precision < 0:
        raise ValueError(f"precision must be a non-negative integer, got {precision!r}")

    return _format(_parse(number, from_base), to_base, precision)
