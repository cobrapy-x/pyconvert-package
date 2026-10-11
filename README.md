# PyConvert

A lightweight unit and number-base conversion library for Python, with **no
dependencies** beyond the standard library.

[![Tests](https://github.com/cobrapy-x/pyconvert-package/actions/workflows/tests.yml/badge.svg)](https://github.com/cobrapy-x/pyconvert-package/actions/workflows/tests.yml)
[![PyPI](https://img.shields.io/pypi/v/pyconvertx.svg)](https://pypi.org/project/pyconvertx/)
[![Python versions](https://img.shields.io/pypi/pyversions/pyconvertx.svg)](https://pypi.org/project/pyconvertx/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/cobrapy-x/pyconvert-package/blob/main/LICENSE)

## Install

```bash
pip install pyconvertx
```

> **The install name and the import name differ.**
> Install **`pyconvertx`**, import **`pyconvert`**.
>
> ```python
> import pyconvert          # not "import pyconvertx"
> ```
>
> The name `pyconvert` was already taken on PyPI in 2015 by an unrelated
> XML/JSON library, so this project is distributed under `pyconvertx`. A
> distribution name that differs from the import name is common — `pip install
> beautifulsoup4` gives you `import bs4`, and `pip install pillow` gives you
> `import PIL`.

## Quick start

```python
import pyconvert

pyconvert.convert(100, "km", "mi")                 # 62.13711922373339
pyconvert.convert(100, "celsius", "fahrenheit")    # 212.0
pyconvert.convert(1024, "MiB", "GiB")              # 1.0
pyconvert.convert(1, "gal_us", "L")                # 3.785411784

pyconvert.convert_base(100, 10, 2)                 # '1100100'
pyconvert.convert_base("10101111", 2, 16)          # 'AF'
pyconvert.convert_base("FF", 16, 10)               # '255'
pyconvert.convert_base(1000, 10, 36)               # 'RS'
```

No setup, no classes to instantiate, no unit objects to construct.

## Unit conversion

```python
convert(value, from_unit, to_unit) -> float
```

There is **no category argument**. Every unit symbol is unique across the whole
library, so the category is looked up from the symbols you give. A consequence
worth having: mixing categories is an error rather than a plausible-looking
wrong number.

```python
>>> pyconvert.convert(1, "kg", "m")
IncompatibleUnitsError: cannot convert 'kg' to 'm': 'kg' measures mass, 'm' measures length
```

### Supported units

182 units across 15 categories. Factors are stored relative to
each category's base unit, so **every pair within a category works**, including
combinations nobody thought to write down (`furlong` to `nmi`, `therm` to `eV`).

| Category | Base | Units | Count |
|---|---|---|---|
| **Length** | `m` | `angstrom`, `au`, `chain`, `cm`, `dam`, `dm`, `fathom`, `ft`, `furlong`, `hm`, `in`, `km`, `ly`, `m`, `mi`, `mm`, `nm`, `nmi`, `pc`, `pm`, `rod`, `thou`, `um`, `yd` | 24 |
| **Mass** | `kg` | `carat`, `g`, `grain`, `kg`, `lb`, `m_e`, `m_earth`, `m_sun`, `mg`, `oz`, `quintal`, `st`, `t`, `ton_uk`, `ton_us`, `u`, `ug` | 17 |
| **Speed** | `m/s` | `c`, `cm/s`, `ft/s`, `km/h`, `kn`, `m/s`, `mm/s`, `mph` | 8 |
| **Area** | `m2` | `ac`, `are`, `cm2`, `ft2`, `ha`, `in2`, `km2`, `m2`, `mi2`, `mm2`, `yd2` | 11 |
| **Volume** | `m3` | `bbl`, `cL`, `cm3`, `cup_us`, `dL`, `floz_imp`, `floz_us`, `ft3`, `gal_imp`, `gal_us`, `in3`, `kL`, `km3`, `L`, `m3`, `mL`, `mm3`, `pt_imp`, `pt_us`, `qt_imp`, `qt_us`, `tbsp_us`, `tsp_us`, `uL`, `yd3` | 25 |
| **Energy** | `J` | `BTU`, `cal`, `cal_it`, `erg`, `eV`, `ft_lbf`, `GeV`, `GJ`, `J`, `kcal`, `keV`, `kJ`, `kWh`, `MeV`, `MJ`, `mJ`, `MWh`, `therm`, `Wh` | 19 |
| **Power** | `W` | `BTU/h`, `GW`, `hp`, `hp_metric`, `kW`, `MW`, `mW`, `TW`, `uW`, `W` | 10 |
| **Temperature** | `kelvin` | `celsius`, `fahrenheit`, `kelvin`, `rankine` | 4 |
| **Time** | `s` | `d`, `fortnight`, `h`, `min`, `ms`, `ns`, `ps`, `s`, `us`, `week`, `yr` | 11 |
| **Pressure** | `Pa` | `atm`, `bar`, `GPa`, `hPa`, `inHg`, `kPa`, `mbar`, `mmHg`, `MPa`, `Pa`, `psi`, `torr` | 12 |
| **Frequency** | `Hz` | `GHz`, `Hz`, `kHz`, `MHz`, `mHz`, `rpm`, `THz` | 7 |
| **Digital storage** | `B` | `B`, `bit`, `GB`, `Gbit`, `GiB`, `kB`, `kbit`, `KiB`, `MB`, `Mbit`, `MiB`, `PB`, `PiB`, `TB`, `TiB` | 15 |
| **Angle** | `rad` | `arcmin`, `arcsec`, `deg`, `grad`, `mrad`, `rad`, `turn` | 7 |
| **Electric current** | `A` | `A`, `kA`, `mA`, `nA`, `pA`, `uA` | 6 |
| **Electric potential** | `V` | `kV`, `MV`, `mV`, `nV`, `uV`, `V` | 6 |

### Alternative spellings

Long names, plurals and typeable forms of awkward symbols all resolve to the
same unit — 390 aliases in total:

```python
pyconvert.convert(1, "kilometre", "mile")   # British or American spelling
pyconvert.convert(1, "meters", "feet")      # plurals
pyconvert.convert(5000, "m2", "hectare")    # ASCII for m^2
pyconvert.convert(5000, "m²", "hectare")    # or the real character
pyconvert.convert(100, "degC", "degF")      # ASCII for °C
pyconvert.convert(100, "°C", "°F")          # or the real character
pyconvert.convert(500, "μs", "ms")          # either Unicode micro sign
```

That last one matters more than it looks. The micro prefix is written two ways
that are visually identical: MICRO SIGN (U+00B5), which is what a Mac's
`Option-M` produces, and GREEK SMALL LETTER MU (U+03BC). They are different
characters, so a dictionary treats them as different keys. Both map to the ASCII
spelling (`us`, `um`, `ug`, `uA`, `uV`, `uW`, `uL`), as does the plain ASCII form.

### Lookup is case-sensitive

It has to be. These pairs are standard notation and differ only by case:

| | | |
|---|---|---|
| `mW` milliwatt | `MW` megawatt | factor of 10⁹ |
| `mHz` millihertz | `MHz` megahertz | factor of 10⁹ |
| `mV` millivolt | `MV` megavolt | factor of 10⁹ |
| `kB` kilobyte (1000) | `KiB` kibibyte (1024) | 2.4% apart |
| `ps` picosecond | `PS` metric horsepower | different categories |

Folding case would make those indistinguishable. Wrong case is caught and
suggested back instead:

```python
>>> pyconvert.convert(1, "KM", "mi")
UnknownUnitError: unknown unit 'KM' (did you mean 'km'?)
```

### Units this library refuses on purpose

Some spellings have more than one real meaning, and resolving them to one
arbitrary choice would return a confidently wrong number. These raise with the
fix in the message rather than guessing:

| Spelling | Why, and what to use |
|---|---|
| `C` | use 'celsius' or 'degC' (bare 'C' is the SI symbol for coulomb) |
| `F` | use 'fahrenheit' or 'degF' (bare 'F' is the SI symbol for farad) |
| `R` | use 'rankine' or 'degR' (bare 'R' is the symbol for roentgen) |
| `b` | use 'bit' or 'B' (byte) -- 'b' and 'B' differ only by case |
| `cal_cap` | use 'kcal' for the food Calorie, or 'cal' for the gram calorie |
| `fl_ounce` | use 'floz_us' or 'floz_imp' |
| `gb` | use 'Gbit' (10**9 bits) or 'GB' (10**9 bytes) |
| `hp_imp` | use 'hp' (mechanical) or 'hp_metric' (PS) |
| `kb` | use 'kbit' (1000 bits) or 'kB' (1000 bytes) |
| `mb` | use 'Mbit' (10**6 bits) or 'MB' (10**6 bytes) |
| `pt` | 'pt' is both point and pint: use 'pt_us' or 'pt_imp' for pints |
| `tb` | use 'TB' (10**12 bytes) or 'TiB' (2**40 bytes) |
| `ton` | 'ton' means three different masses: use 't' (tonne, 1000 kg), 'ton_us' (short, 907.18474 kg) or 'ton_uk' (long, 1016.0469088 kg) |
| `tons` | see 'ton': use 't', 'ton_us' or 'ton_uk' |

`C`, `F` and `R` are also kept free so that charge, capacitance and radiation
can be added later without a breaking change.

One default *is* chosen: bare `gal`, `gallon`, `quart`, `pint`, `cup`, `floz`,
`tbsp` and `tsp` mean the **US** measures. The imperial ones are available
explicitly as `gal_imp`, `qt_imp`, `pt_imp` and `floz_imp`.

Where a unit has competing definitions, the one picked is documented:

| Unit | This library uses | Also available |
|---|---|---|
| `cal` | thermochemical, 4.184 J exactly | `cal_it` (4.1868 J) |
| `hp` | mechanical, 745.6998… W | `hp_metric` / `PS` (735.49875 W) |
| `BTU` | International Table, 1055.05585262 J | — |
| `yr` | Julian year, exactly 365.25 days | — |
| `t` | tonne, 1000 kg | `ton_us`, `ton_uk` |

## Number bases

```python
convert_base(number, from_base, to_base, precision=16) -> str
```

Bases 2 to 36. Input may be an `int` or a `str`, in either case, with
underscores allowed as separators. Output digits are always uppercase.

```python
pyconvert.convert_base("ff", 16, 2)          # '11111111'
pyconvert.convert_base("1111_1111", 2, 16)   # 'FF'
pyconvert.convert_base(-255, 10, 16)         # '-FF'
pyconvert.convert_base(1100100, 2, 10)       # '100'  (an int is read as its digits)
```

Fractional parts are converted exactly where the result terminates:

```python
pyconvert.convert_base("0.5", 10, 2)         # '0.1'
pyconvert.convert_base("A.8", 16, 10)        # '10.5'
pyconvert.convert_base("0.1", 10, 2)         # '0.0001100110011001'
```

That last result is truncated, not wrong — one tenth has no finite binary form,
so it runs to `precision` digits and stops. Pass `precision` to change that.

**The result is always a string**, including when the target base is 10. Once
`'AF'` is a string, returning an `int` for base 10 alone would make the return
*type* depend on an argument's *value*. Call `int(result)` when you want a
number back.

## Accuracy

Factors that are exact by international definition are stored as exact rationals
and rounded to `float` once, rather than being computed in floating point. The
difference is small but real: `231 * 0.0254 ** 3` gives
`0.0037854117839999997`, three roundings away from the correctly rounded
`0.003785411784`.

**Temperature is computed in exact rational arithmetic**, because it is the one
category with an offset, and 5/9 has no finite binary form. In plain floats,
`100 °C → °F` returns `211.99999999999997`. Here:

```python
pyconvert.convert(100, "celsius", "fahrenheit")    # 212.0  exactly
pyconvert.convert(0,   "celsius", "fahrenheit")    # 32.0   exactly
pyconvert.convert(-40, "celsius", "fahrenheit")    # -40.0  exactly
pyconvert.convert(0,   "kelvin",  "fahrenheit")    # -459.67 exactly
```

Everything else uses a single float ratio, which is about ten times faster and
is what nearly every conversion needs. Results are ordinary IEEE-754 doubles, so
between two non-base units you can still see a last-digit artefact:
`convert(1, "gal_imp", "L")` is `4.5460899999999995` rather than `4.54609`.
Conversions *to* a category's base unit are exact.

## Errors

Everything this library raises derives from `PyConvertError`, so one `except`
catches all of it. Each error also subclasses the builtin you would expect, so
existing `except KeyError` or `except ValueError` code keeps working.

```
PyConvertError
├── UnknownUnitError        (also KeyError)    unit not in the registry
├── UnknownCategoryError    (also KeyError)    no such category
├── IncompatibleUnitsError                     the two units measure different things
├── InvalidBaseError        (also ValueError)  base outside 2-36
├── InvalidDigitError       (also ValueError)  digit invalid for its base
└── RegistryError           (also RuntimeError) the registry itself is inconsistent
```

`RegistryError` is raised at import time, never from a call. It means two
categories claim the same symbol, or an alias points at a unit that does not
exist — a bug in the library, not in your input.

## Introspection

```python
pyconvert.list_categories()          # ['angle', 'area', 'current', ...]
pyconvert.list_units("temperature")  # ['celsius', 'fahrenheit', 'kelvin', 'rankine']
pyconvert.list_units()               # all 182 canonical symbols
pyconvert.category_of("psi")         # 'pressure'
pyconvert.base_unit("pressure")      # 'Pa'
pyconvert.is_convertible("km", "kg") # False
pyconvert.convert_all([0, 100], "celsius", "fahrenheit")   # [32.0, 212.0]
```

## Requirements

Python 3.9 or newer. No third-party dependencies.

## Development

```bash
git clone https://github.com/cobrapy-x/pyconvert-package.git
cd pyconvert-package
pip install -e ".[dev]"

pytest          # 1072 tests, including the docstring examples
ruff check .
```

See [CONTRIBUTING.md](https://github.com/cobrapy-x/pyconvert-package/blob/main/CONTRIBUTING.md) for how to add a unit, and the
invariants the test suite enforces.

## License

MIT — see [LICENSE](https://github.com/cobrapy-x/pyconvert-package/blob/main/LICENSE).
