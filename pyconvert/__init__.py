"""PyConvert -- a lightweight unit and number-base conversion library.

Install as ``pyconvertx``, import as ``pyconvert``::

    pip install pyconvertx

Unit conversion takes a value and two unit symbols. There is no category
argument: every symbol is unique across the registry, so the category is looked
up for you, and converting across categories is an error rather than a wrong
number.

    >>> import pyconvert
    >>> pyconvert.convert(100, "km", "mi")
    62.13711922373339
    >>> pyconvert.convert(100, "celsius", "fahrenheit")
    212.0
    >>> pyconvert.convert(1024, "MiB", "GiB")
    1.0

Number bases go from 2 to 36, and always come back as a string:

    >>> pyconvert.convert_base(100, 10, 2)
    '1100100'
    >>> pyconvert.convert_base("FF", 16, 10)
    '255'

Lookup is case-sensitive, because it has to be -- ``mW`` is a milliwatt and
``MW`` a megawatt, ``KB`` and ``KiB`` differ by 2.4%. Alternative spellings are
handled by aliases instead, so ``kilometre``, ``kilometer`` and ``km`` all work,
as do the typeable forms of awkward symbols (``m2`` for m2, ``degC`` for degC,
``us`` for microseconds).
"""

from __future__ import annotations

from .bases import DIGITS, MAX_BASE, MIN_BASE, convert_base
from .exceptions import (
    IncompatibleUnitsError,
    InvalidBaseError,
    InvalidDigitError,
    PyConvertError,
    RegistryError,
    UnknownCategoryError,
    UnknownUnitError,
)
from .registry import AMBIGUOUS, BASE_UNITS, CATEGORIES
from .units import (
    base_unit,
    category_of,
    convert,
    convert_all,
    is_convertible,
    list_categories,
    list_units,
)

__author__ = "cobrapy-x"
__license__ = "MIT"

__all__ = [
    # unit conversion
    "convert",
    "convert_all",
    "is_convertible",
    # number bases
    "convert_base",
    "MIN_BASE",
    "MAX_BASE",
    "DIGITS",
    # introspection
    "list_categories",
    "list_units",
    "category_of",
    "base_unit",
    "CATEGORIES",
    "BASE_UNITS",
    "AMBIGUOUS",
    # errors
    "PyConvertError",
    "UnknownUnitError",
    "UnknownCategoryError",
    "IncompatibleUnitsError",
    "InvalidBaseError",
    "InvalidDigitError",
    "RegistryError",
    # metadata
    "__version__",
]


def __getattr__(name: str) -> str:
    """Resolve ``__version__`` on first access rather than at import.

    ``importlib.metadata`` is the only way to read the installed version, but
    importing it costs around 12 ms -- more than half of this package's import
    time -- because it pulls in ``email.message``. Almost nobody reads
    ``__version__``, so it is looked up lazily and then cached in the module
    namespace. See PEP 562 for module-level ``__getattr__``.
    """
    if name == "__version__":
        try:
            from importlib.metadata import version

            resolved = version("pyconvertx")
        except Exception:
            # Running from a source checkout that was never pip-installed.
            resolved = "0.0.0+source"
        globals()["__version__"] = resolved
        return resolved
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
