"""Exception hierarchy for PyConvert.

Every error raised by this library derives from :class:`PyConvertError`, so a
caller who does not care about the distinction can write::

    try:
        pyconvert.convert(1, "kg", "m")
    except pyconvert.PyConvertError as exc:
        print(exc)
"""

from __future__ import annotations

import difflib

__all__ = [
    "IncompatibleUnitsError",
    "InvalidBaseError",
    "InvalidDigitError",
    "PyConvertError",
    "RegistryError",
    "UnknownCategoryError",
    "UnknownUnitError",
]


class PyConvertError(Exception):
    """Base class for every error raised by PyConvert."""


class UnknownUnitError(PyConvertError, KeyError):
    """A unit symbol is not present in the registry.

    Also inherits :class:`KeyError` so that code written against a plain dict
    lookup keeps working.
    """

    def __init__(
        self,
        unit: object,
        known: list[str] | None = None,
        hint: str | None = None,
    ) -> None:
        self.unit = unit
        self.hint = hint
        self.suggestions: list[str] = []
        message = f"unknown unit {unit!r}"

        if hint:
            # A spelling the registry refuses on purpose, because it is
            # ambiguous. Say what to write instead; skip fuzzy matching, which
            # would only offer something unrelated that happens to look close.
            super().__init__(f"{message}: {hint}")
            return

        if known and isinstance(unit, str):
            # Case-insensitive near misses first: "KM" -> "km" is the single
            # most common mistake, and a case-sensitive ratio misses it.
            lowered = {k.lower(): k for k in known}
            if unit.lower() in lowered and lowered[unit.lower()] != unit:
                self.suggestions = [lowered[unit.lower()]]
            else:
                self.suggestions = difflib.get_close_matches(
                    unit, known, n=3, cutoff=0.6
                )

        if self.suggestions:
            offered = " or ".join(repr(s) for s in self.suggestions)
            message += f" (did you mean {offered}?)"

        super().__init__(message)

    def __str__(self) -> str:  # KeyError.__str__ would re-quote the message
        return self.args[0]


class UnknownCategoryError(PyConvertError, KeyError):
    """A category name is not one of the registry's categories."""

    def __init__(self, category: object, known: list[str] | None = None) -> None:
        self.category = category
        message = f"unknown category {category!r}"
        if known:
            message += " (available: " + ", ".join(sorted(known)) + ")"
        super().__init__(message)

    def __str__(self) -> str:
        return self.args[0]


class IncompatibleUnitsError(PyConvertError):
    """Two units are both valid but measure different kinds of quantity."""

    def __init__(
        self,
        source: str,
        target: str,
        source_category: str,
        target_category: str,
    ) -> None:
        self.source = source
        self.target = target
        self.source_category = source_category
        self.target_category = target_category
        super().__init__(
            f"cannot convert {source!r} to {target!r}: "
            f"{source!r} measures {source_category}, "
            f"{target!r} measures {target_category}"
        )


class InvalidBaseError(PyConvertError, ValueError):
    """A numeric base is outside the supported range."""

    def __init__(self, base: object, low: int = 2, high: int = 36) -> None:
        self.base = base
        super().__init__(f"base must be an integer from {low} to {high}, got {base!r}")


class InvalidDigitError(PyConvertError, ValueError):
    """A digit in the input is not valid for the base it was given in."""

    def __init__(self, digit: str, base: int, number: object = None) -> None:
        self.digit = digit
        self.base = base
        self.number = number
        if not digit:
            super().__init__(f"no digits to convert in {number!r}")
        else:
            super().__init__(f"{digit!r} is not a valid digit in base {base}")


class RegistryError(PyConvertError, RuntimeError):
    """The unit registry itself is inconsistent.

    Raised at import time, not at call time: it means two categories claim the
    same symbol, or an alias points at a unit that does not exist. This is a bug
    in PyConvert (or in a locally edited registry), never in user input.
    """
