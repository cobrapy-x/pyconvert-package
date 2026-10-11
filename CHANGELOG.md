# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-10-11

The first release that actually works. Version 0.1.0 could not be imported at
all (see below), so although this is a complete rewrite of the public API,
nothing can have depended on the old one.

Published on PyPI as **`pyconvertx`**; the import name remains `pyconvert`.

### Added

- 182 units across 15 categories: length, mass, speed, area, volume, energy,
  power, temperature, time, pressure, frequency, digital storage, angle,
  electric current and electric potential. Temperature, time, pressure,
  frequency, storage, angle, current and potential are all new.
- 390 aliases, so long names, plurals and typeable forms of awkward symbols
  resolve to the same unit (`kilometre`, `kilometer`, `km`; `m2`, `m²`;
  `degC`, `°C`).
- Both Unicode micro signs — MICRO SIGN (U+00B5) and GREEK SMALL LETTER MU
  (U+03BC) — are mapped onto the ASCII spelling. They are visually identical
  but different characters, so a plain dictionary lookup would accept one
  user's `μs` and reject another's.
- `convert_base(number, from_base, to_base, precision=16)` for bases 2 to 36,
  with support for fractional parts, negative values, mixed-case input and
  underscore separators.
- An exception hierarchy rooted at `PyConvertError`, where each error also
  subclasses the builtin you would expect (`KeyError`, `ValueError`,
  `RuntimeError`).
- Error messages that suggest a fix: wrong case is detected and offered back,
  near misses are fuzzy-matched, and deliberately ambiguous spellings explain
  what to write instead.
- `convert_all`, `is_convertible`, `list_categories`, `list_units`,
  `category_of` and `base_unit`.
- Type hints throughout, with a `py.typed` marker so type checkers use them.
- A test suite of 1072 tests, including every docstring example.

### Changed

- **The conversion API is entirely new.** `convert(value, from_unit, to_unit)`
  replaces `convert(qty, units, value)`. The category argument is gone, and
  unit pairs are no longer expressed as arrow strings:

  ```python
  # 0.1.0
  convert('weight', 'gram-->kilogram', 500)
  # 1.0.0
  convert(500, 'gram', 'kilogram')
  ```

- **Conversion factors are now stored relative to a base unit per category**
  rather than as explicit pairs. Every pair within a category therefore works,
  including ones nobody wrote down. The old design needed one entry per
  direction per pair, which would have required roughly 1,700 entries to cover
  these 15 categories; the registry holds 182.
- `convertnumber(base, number)` is replaced by
  `convert_base(number, from_base, to_base)`, with the value first and both
  bases given explicitly.
- `convert_base` always returns a string, including when the target base is 10.
- The package is now `pyconvert.registry`, `pyconvert.units`,
  `pyconvert.bases` and `pyconvert.exceptions`; the single
  `pyconvert.pyconvert` module is gone.
- Packaging moved from `setup.py` to `pyproject.toml`.

### Fixed

- **The package could not be imported.** `__init__.py` did
  `from .pyconvert import convert, convert_number`, but the function was named
  `convertnumber`, so `import pyconvert` raised `ImportError` for every user of
  0.1.0.
- **`meter-->feet` was inverted.** It held 0.3048, the number of metres in a
  foot, so converting metres to feet divided by 3.28 instead of multiplying.
  The base-relative registry makes this class of mistake impossible to express,
  and a test pins it.
- **`quintal-->kilogram` was 1000.** A quintal is 100 kg, so the factor was
  wrong by a factor of ten.
- Missing reverse conversions: `solarmass-->kilogram` and `amu-->gram` had no
  inverse, so those conversions failed in one direction. All pairs are now
  symmetric by construction.

### Security

- Nothing applicable; the library performs arithmetic on numbers and strings
  and makes no network, filesystem or subprocess calls.

## [0.1.0] - 2025-10-20

Initial release, kept as the `v0.1.0` git tag for history. Never published to
PyPI.

- Unit conversion across length, weight, speed, area, energy, power and volume
  via a dictionary of `from-->to` pairs.
- `convertnumber` for converting a decimal number into any base from 2 to 36.
- **Known broken:** `import pyconvert` raised `ImportError`, so the package was
  unusable as published. See the Fixed section above.

[1.0.0]: https://github.com/cobrapy-x/pyconvert-package/releases/tag/v1.0.0
[0.1.0]: https://github.com/cobrapy-x/pyconvert-package/releases/tag/v0.1.0
