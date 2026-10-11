"""Central conversion registry: the data PyConvert converts with.

Every unit is stored as its size **relative to its category's base unit**, so a
conversion is a single ratio::

    y = x * f_source / f_target

A registry entry is either

* a plain ``float`` -- a purely multiplicative unit (14 of the 15 categories), or
* a ``(scale, offset)`` tuple -- an affine unit, where
  ``base_value = x * scale + offset``.

Only temperature needs offsets. Its scale and offset are written as
:class:`fractions.Fraction` so that ``5/9`` stays an exact ratio and
``100 celsius -> fahrenheit`` returns exactly ``212.0`` rather than
``211.99999999999997``. See :mod:`pyconvert.units` for the two code paths.

**On accuracy.** Many of these factors are exact by international definition
(one inch *is* 25.4 mm; it is not a measurement). Those definitions are written
below as exact rationals and rounded to ``float`` exactly once, at the end. The
difference is small but real: computing the US gallon as ``231 * 0.0254 ** 3``
in floating point yields ``0.0037854117839999997``, three steps of rounding
away from the correctly rounded ``0.003785411784``. Factors that genuinely are
measurements (particle masses, the solar mass) are marked as such.
"""

from __future__ import annotations

from fractions import Fraction
from math import pi

from .exceptions import RegistryError, UnknownCategoryError, UnknownUnitError

__all__ = [
    "ALIASES",
    "AMBIGUOUS",
    "BASE_UNITS",
    "CATEGORIES",
    "all_units",
    "build_index",
    "category_of",
    "resolve",
    "units_in",
]

# --------------------------------------------------------------------------
# Exact defined constants, as rationals, shared so they cannot disagree.
# The ``_Q`` suffix marks an exact quantity; ``float()`` is applied once, where
# the value enters a table.
# --------------------------------------------------------------------------
_IN_Q = Fraction(254, 10_000)                      # inch -> metre
_FT_Q = 12 * _IN_Q                                 # foot -> metre
_YD_Q = 3 * _FT_Q                                  # yard -> metre
_MI_Q = 1760 * _YD_Q                               # statute mile -> metre
_LB_Q = Fraction(45_359_237, 100_000_000)          # pound -> kilogram
_LBF_Q = Fraction(44_482_216_152_605, 10 ** 13)    # pound-force -> newton
_GAL_US_Q = 231 * _IN_Q ** 3                       # US liquid gallon -> m3
_GAL_IMP_Q = Fraction(454_609, 100_000_000)        # imperial gallon -> m3
_BTU_Q = Fraction(105_505_585_262, 100_000_000)    # BTU_IT -> joule
_MMHG_Q = Fraction(133_322_387_415, 10 ** 9)       # mmHg -> pascal (conventional)
_HP_Q = 550 * _FT_Q * _LBF_Q                       # mechanical horsepower -> watt

# --------------------------------------------------------------------------
# 1. Length -- base: metre
# --------------------------------------------------------------------------
LENGTH = {
    "m": 1.0,
    "km": 1000.0,
    "hm": 100.0,
    "dam": 10.0,
    "dm": 0.1,
    "cm": 0.01,
    "mm": 1e-3,
    "um": 1e-6,
    "nm": 1e-9,
    "pm": 1e-12,
    "angstrom": 1e-10,                        # exact
    "in": float(_IN_Q),                       # exact
    "ft": float(_FT_Q),                       # exact
    "yd": float(_YD_Q),                       # exact
    "mi": float(_MI_Q),                       # exact
    "nmi": 1852.0,                            # exact (nautical mile)
    "thou": float(_IN_Q / 1000),              # exact
    "fathom": float(6 * _FT_Q),               # exact
    "rod": float(Fraction(33, 2) * _FT_Q),    # exact (16.5 ft)
    "chain": float(66 * _FT_Q),               # exact
    "furlong": float(660 * _FT_Q),            # exact
    "ly": float(299_792_458 * Fraction(36_525, 100) * 86_400),  # exact: c * Julian year
    "au": 149_597_870_700.0,                  # exact (IAU 2012)
    "pc": 648_000 / pi * 149_597_870_700.0,   # exact definition, irrational value
}

# --------------------------------------------------------------------------
# 2. Mass -- base: kilogram
# --------------------------------------------------------------------------
MASS = {
    "kg": 1.0,
    "g": 1e-3,
    "mg": 1e-6,
    "ug": 1e-9,
    "t": 1000.0,                              # tonne (metric ton), exact
    "quintal": 100.0,                         # exact -- v0.1.0 had 1000, wrong by 10x
    "lb": float(_LB_Q),                       # exact
    "oz": float(_LB_Q / 16),                  # exact -- avoirdupois ounce, NOT fluid
    "st": float(14 * _LB_Q),                  # exact (stone)
    "ton_us": float(2000 * _LB_Q),            # exact (short ton)
    "ton_uk": float(2240 * _LB_Q),            # exact (long ton)
    "grain": float(Fraction(6_479_891, 10 ** 11)),   # exact
    "carat": 2e-4,                            # exact (metric carat)
    "u": 1.66053906892e-27,                   # measured, CODATA 2022
    "m_e": 9.1093837139e-31,                  # measured, CODATA 2022 (electron)
    "m_earth": 5.9722e24,                     # measured, IAU nominal
    "m_sun": 1.98841e30,                      # measured, IAU nominal
}

# --------------------------------------------------------------------------
# 3. Speed -- base: metre per second
# --------------------------------------------------------------------------
SPEED = {
    "m/s": 1.0,
    "km/h": float(Fraction(1000, 3600)),      # exact
    "cm/s": 0.01,
    "mm/s": 1e-3,
    "ft/s": float(_FT_Q),                     # exact
    "mph": float(_MI_Q / 3600),               # exact
    "kn": float(Fraction(1852, 3600)),        # exact (knot)
    "c": 299_792_458.0,                       # exact (speed of light in vacuum)
}

# --------------------------------------------------------------------------
# 4. Area -- base: square metre
# --------------------------------------------------------------------------
AREA = {
    "m2": 1.0,
    "km2": 1e6,
    "cm2": 1e-4,
    "mm2": 1e-6,
    "ha": 1e4,                                # hectare, exact
    "are": 100.0,                             # exact
    "in2": float(_IN_Q ** 2),                 # exact
    "ft2": float(_FT_Q ** 2),                 # exact
    "yd2": float(_YD_Q ** 2),                 # exact
    "mi2": float(_MI_Q ** 2),                 # exact
    "ac": float(4840 * _YD_Q ** 2),           # exact (acre = 4840 square yards)
}

# --------------------------------------------------------------------------
# 5. Volume -- base: cubic metre
# --------------------------------------------------------------------------
VOLUME = {
    "m3": 1.0,
    "cm3": 1e-6,
    "mm3": 1e-9,
    "km3": 1e9,
    "L": 1e-3,                                # exact
    "mL": 1e-6,
    "uL": 1e-9,
    "cL": 1e-5,
    "dL": 1e-4,
    "kL": 1.0,
    "in3": float(_IN_Q ** 3),                 # exact
    "ft3": float(_FT_Q ** 3),                 # exact
    "yd3": float(_YD_Q ** 3),                 # exact
    "gal_us": float(_GAL_US_Q),               # exact (US liquid gallon)
    "qt_us": float(_GAL_US_Q / 4),
    "pt_us": float(_GAL_US_Q / 8),
    "cup_us": float(_GAL_US_Q / 16),
    "floz_us": float(_GAL_US_Q / 128),
    "tbsp_us": float(_GAL_US_Q / 256),
    "tsp_us": float(_GAL_US_Q / 768),
    "gal_imp": float(_GAL_IMP_Q),             # exact (imperial gallon)
    "qt_imp": float(_GAL_IMP_Q / 4),
    "pt_imp": float(_GAL_IMP_Q / 8),
    "floz_imp": float(_GAL_IMP_Q / 160),
    "bbl": float(42 * _GAL_US_Q),             # exact (oil barrel)
}

# --------------------------------------------------------------------------
# 6. Energy -- base: joule
# --------------------------------------------------------------------------
ENERGY = {
    "J": 1.0,
    "mJ": 1e-3,
    "kJ": 1e3,
    "MJ": 1e6,
    "GJ": 1e9,
    "cal": 4.184,                             # exact (thermochemical calorie)
    "kcal": 4184.0,                           # exact
    "cal_it": 4.1868,                         # exact (International Table calorie)
    "Wh": 3600.0,                             # exact
    "kWh": 3.6e6,                             # exact
    "MWh": 3.6e9,                             # exact
    "eV": 1.602176634e-19,                    # exact since the 2019 SI redefinition
    "keV": 1.602176634e-16,
    "MeV": 1.602176634e-13,
    "GeV": 1.602176634e-10,
    "erg": 1e-7,                              # exact
    "BTU": float(_BTU_Q),                     # exact (BTU_IT)
    "therm": 1.054804e8,                      # exact (US therm)
    "ft_lbf": float(_FT_Q * _LBF_Q),          # exact
}

# --------------------------------------------------------------------------
# 7. Power -- base: watt
# --------------------------------------------------------------------------
POWER = {
    "W": 1.0,
    "uW": 1e-6,
    "mW": 1e-3,                               # milliwatt -- lowercase m
    "kW": 1e3,
    "MW": 1e6,                                # megawatt -- uppercase M
    "GW": 1e9,
    "TW": 1e12,
    "hp": float(_HP_Q),                       # exact (mechanical/imperial horsepower)
    "hp_metric": 735.49875,                   # exact (metric horsepower, a.k.a. PS)
    "BTU/h": float(_BTU_Q / 3600),            # exact
}

# --------------------------------------------------------------------------
# 8. Temperature -- base: kelvin.  The only affine category.
#
# Entries are ``(scale, offset)`` with ``kelvin = x * scale + offset``, written
# as exact rationals. Fahrenheit's offset is 273.15 - 32 * 5/9, i.e. the kelvin
# value of 0 degrees Fahrenheit, kept as the arithmetic that defines it.
# --------------------------------------------------------------------------
TEMPERATURE = {
    "kelvin": (Fraction(1), Fraction(0)),
    "celsius": (Fraction(1), Fraction(27315, 100)),
    "fahrenheit": (Fraction(5, 9), Fraction(27315, 100) - 32 * Fraction(5, 9)),
    "rankine": (Fraction(5, 9), Fraction(0)),
}

# --------------------------------------------------------------------------
# 9. Time -- base: second
# --------------------------------------------------------------------------
TIME = {
    "s": 1.0,
    "ms": 1e-3,
    "us": 1e-6,
    "ns": 1e-9,
    "ps": 1e-12,                              # picosecond -- lowercase; see "PS" alias
    "min": 60.0,
    "h": 3600.0,
    "d": 86_400.0,
    "week": 604_800.0,
    "fortnight": 1_209_600.0,
    "yr": 31_557_600.0,                       # Julian year, exactly 365.25 days
}

# --------------------------------------------------------------------------
# 10. Pressure -- base: pascal
# --------------------------------------------------------------------------
PRESSURE = {
    "Pa": 1.0,
    "hPa": 100.0,
    "kPa": 1e3,
    "MPa": 1e6,
    "GPa": 1e9,
    "bar": 1e5,                               # exact
    "mbar": 100.0,                            # exact
    "atm": 101_325.0,                         # exact
    "torr": float(Fraction(101_325, 760)),    # exact (1/760 atm)
    "mmHg": float(_MMHG_Q),                   # exact by convention
    "inHg": float(_MMHG_Q * _IN_Q / Fraction(1, 1000)),   # 25.4 mmHg, exact
    "psi": float(_LBF_Q / _IN_Q ** 2),        # exact
}

# --------------------------------------------------------------------------
# 11. Frequency -- base: hertz
# --------------------------------------------------------------------------
FREQUENCY = {
    "Hz": 1.0,
    "mHz": 1e-3,                              # millihertz -- lowercase m
    "kHz": 1e3,
    "MHz": 1e6,                               # megahertz -- uppercase M
    "GHz": 1e9,
    "THz": 1e12,
    "rpm": float(Fraction(1, 60)),            # exact (revolutions per minute)
}

# --------------------------------------------------------------------------
# 12. Digital storage -- base: byte
#
# Decimal prefixes are powers of 1000 (kB, MB, ...); binary prefixes are powers
# of 1024 (KiB, MiB, ...). Both are present and they are NOT interchangeable.
# Bit units are spelled out ("kbit", not "kb") so they can never be confused
# with byte units by case alone.
# --------------------------------------------------------------------------
STORAGE = {
    "B": 1.0,
    "bit": 0.125,                             # exact
    "kB": 1e3,
    "MB": 1e6,
    "GB": 1e9,
    "TB": 1e12,
    "PB": 1e15,
    "KiB": 1024.0,
    "MiB": 1024.0 ** 2,
    "GiB": 1024.0 ** 3,
    "TiB": 1024.0 ** 4,
    "PiB": 1024.0 ** 5,
    "kbit": 125.0,                            # 1000 bits
    "Mbit": 1.25e5,
    "Gbit": 1.25e8,
}

# --------------------------------------------------------------------------
# 13. Angle -- base: radian
# --------------------------------------------------------------------------
ANGLE = {
    "rad": 1.0,
    "mrad": 1e-3,
    "deg": pi / 180,
    "grad": pi / 200,                         # gradian / gon
    "arcmin": pi / 10_800,
    "arcsec": pi / 648_000,
    "turn": 2 * pi,                           # full revolution
}

# --------------------------------------------------------------------------
# 14. Electric current -- base: ampere
# --------------------------------------------------------------------------
CURRENT = {
    "A": 1.0,
    "kA": 1e3,
    "mA": 1e-3,
    "uA": 1e-6,
    "nA": 1e-9,
    "pA": 1e-12,
}

# --------------------------------------------------------------------------
# 15. Electric potential -- base: volt
# --------------------------------------------------------------------------
POTENTIAL = {
    "V": 1.0,
    "MV": 1e6,
    "kV": 1e3,
    "mV": 1e-3,
    "uV": 1e-6,
    "nV": 1e-9,
}

# --------------------------------------------------------------------------
# Category table and base units
# --------------------------------------------------------------------------
CATEGORIES = {
    "length": LENGTH,
    "mass": MASS,
    "speed": SPEED,
    "area": AREA,
    "volume": VOLUME,
    "energy": ENERGY,
    "power": POWER,
    "temperature": TEMPERATURE,
    "time": TIME,
    "pressure": PRESSURE,
    "frequency": FREQUENCY,
    "storage": STORAGE,
    "angle": ANGLE,
    "current": CURRENT,
    "potential": POTENTIAL,
}

BASE_UNITS = {
    "length": "m",
    "mass": "kg",
    "speed": "m/s",
    "area": "m2",
    "volume": "m3",
    "energy": "J",
    "power": "W",
    "temperature": "kelvin",
    "time": "s",
    "pressure": "Pa",
    "frequency": "Hz",
    "storage": "B",
    "angle": "rad",
    "current": "A",
    "potential": "V",
}

# --------------------------------------------------------------------------
# Aliases: alternative spellings that resolve to a canonical symbol.
#
# Lookup is case-sensitive, because it has to be: mW is a milliwatt and MW a
# megawatt, mHz is a millihertz and MHz a megahertz, and KB and KiB differ by
# 2.4%. Folding case would make those indistinguishable. Aliases below cover
# the spellings people actually type instead.
#
# Deliberately absent: bare "C", "F" and "R" (they are the SI symbols for
# coulomb, farad and roentgen, so claiming them for temperature would block
# those categories later); bare "pt" (point or pint); bare "ton" (three
# different tons differing by up to 12%). Those must be spelled out.
# --------------------------------------------------------------------------
ALIASES = {
    # -- length ----------------------------------------------------------
    "metre": "m", "meter": "m", "metres": "m", "meters": "m",
    "kilometre": "km", "kilometer": "km", "kilometres": "km", "kilometers": "km",
    "centimetre": "cm", "centimeter": "cm", "centimetres": "cm", "centimeters": "cm",
    "millimetre": "mm", "millimeter": "mm",
    "micrometre": "um", "micrometer": "um", "micron": "um",
    "nanometre": "nm", "nanometer": "nm", "picometre": "pm", "picometer": "pm",
    "decimetre": "dm", "decimeter": "dm", "hectometre": "hm", "hectometer": "hm",
    "decametre": "dam", "decameter": "dam",
    "inch": "in", "inches": "in",
    "foot": "ft", "feet": "ft",
    "yard": "yd", "yards": "yd",
    "mile": "mi", "miles": "mi",
    "nautical_mile": "nmi", "nautical_miles": "nmi",
    "mil": "thou",
    "fathoms": "fathom", "rods": "rod", "chains": "chain", "furlongs": "furlong",
    "lightyear": "ly", "light_year": "ly", "lightyears": "ly", "light_years": "ly",
    "astronomical_unit": "au", "parsec": "pc", "parsecs": "pc",
    "Å": "angstrom", "angstroms": "angstrom",

    # -- mass ------------------------------------------------------------
    "kilogram": "kg", "kilogramme": "kg", "kilograms": "kg", "kgs": "kg",
    "gram": "g", "gramme": "g", "grams": "g",
    "milligram": "mg", "milligrams": "mg", "microgram": "ug", "micrograms": "ug",
    "tonne": "t", "tonnes": "t", "metric_ton": "t", "metric_tonne": "t",
    "quintals": "quintal",
    "pound": "lb", "pounds": "lb", "lbs": "lb",
    "ounce": "oz", "ounces": "oz",
    "stone": "st", "stones": "st",
    "short_ton": "ton_us", "us_ton": "ton_us",
    "long_ton": "ton_uk", "imperial_ton": "ton_uk", "uk_ton": "ton_uk",
    "grains": "grain", "carats": "carat",
    "amu": "u", "dalton": "u", "Da": "u", "atomic_mass_unit": "u",
    "electron_mass": "m_e",
    "earth_mass": "m_earth", "earthmass": "m_earth",
    "solar_mass": "m_sun", "solarmass": "m_sun", "solar_masses": "m_sun",

    # -- speed -----------------------------------------------------------
    "mps": "m/s", "m_s": "m/s", "meters_per_second": "m/s", "metres_per_second": "m/s",
    "kmh": "km/h", "kph": "km/h", "km_h": "km/h",
    "kilometers_per_hour": "km/h", "kilometres_per_hour": "km/h",
    "mi/h": "mph", "miles_per_hour": "mph",
    "fps": "ft/s", "ft_s": "ft/s", "feet_per_second": "ft/s",
    "knot": "kn", "knots": "kn",
    "speed_of_light": "c",

    # -- area ------------------------------------------------------------
    "m^2": "m2", "m²": "m2", "sqm": "m2", "square_meter": "m2", "square_metre": "m2",
    "km^2": "km2", "km²": "km2", "square_kilometer": "km2", "square_kilometre": "km2",
    "cm^2": "cm2", "cm²": "cm2", "square_centimeter": "cm2", "square_centimetre": "cm2",
    "mm^2": "mm2", "mm²": "mm2",
    "in^2": "in2", "in²": "in2", "sqin": "in2", "square_inch": "in2",
    "ft^2": "ft2", "ft²": "ft2", "sqft": "ft2",
    "square_foot": "ft2", "square_feet": "ft2",
    "yd^2": "yd2", "yd²": "yd2", "square_yard": "yd2",
    "mi^2": "mi2", "mi²": "mi2", "square_mile": "mi2",
    "hectare": "ha", "hectares": "ha",
    "acre": "ac", "acres": "ac",
    "ares": "are",

    # -- volume ----------------------------------------------------------
    "m^3": "m3", "m³": "m3", "cubic_meter": "m3", "cubic_metre": "m3",
    "cm^3": "cm3", "cm³": "cm3", "cc": "cm3", "cubic_centimeter": "cm3",
    "mm^3": "mm3", "mm³": "mm3", "km^3": "km3", "km³": "km3",
    "in^3": "in3", "in³": "in3", "cubic_inch": "in3",
    "ft^3": "ft3", "ft³": "ft3", "cuft": "ft3",
    "cubic_foot": "ft3", "cubic_feet": "ft3",
    "yd^3": "yd3", "yd³": "yd3", "cubic_yard": "yd3",
    "l": "L", "liter": "L", "litre": "L", "liters": "L", "litres": "L",
    "ml": "mL", "milliliter": "mL", "millilitre": "mL",
    "cl": "cL", "centiliter": "cL", "dl": "dL", "deciliter": "dL",
    "kl": "kL", "kiloliter": "kL", "ul": "uL", "microliter": "uL", "microlitre": "uL",
    "gal": "gal_us", "gallon": "gal_us", "gallons": "gal_us", "gallon_us": "gal_us",
    "quart": "qt_us", "quarts": "qt_us",
    "pint": "pt_us", "pints": "pt_us",
    "cup": "cup_us", "cups": "cup_us",
    "floz": "floz_us", "fluid_ounce": "floz_us", "fl_oz": "floz_us",
    "tbsp": "tbsp_us", "tablespoon": "tbsp_us",
    "tsp": "tsp_us", "teaspoon": "tsp_us",
    "gallon_imp": "gal_imp", "imperial_gallon": "gal_imp",
    "imperial_pint": "pt_imp", "imperial_quart": "qt_imp",
    "imperial_fluid_ounce": "floz_imp",
    "barrel": "bbl", "barrels": "bbl", "oil_barrel": "bbl",

    # -- energy ----------------------------------------------------------
    "joule": "J", "joules": "J",
    "kilojoule": "kJ", "megajoule": "MJ", "gigajoule": "GJ", "millijoule": "mJ",
    "calorie": "cal", "calories": "cal",
    "kilocalorie": "kcal", "kilocalories": "kcal", "Cal": "kcal",
    "watt_hour": "Wh", "watthour": "Wh",
    "kilowatt_hour": "kWh", "kilowatthour": "kWh", "kwh": "kWh",
    "megawatt_hour": "MWh",
    "electronvolt": "eV", "electron_volt": "eV",
    "ergs": "erg",
    "btu": "BTU", "Btu": "BTU", "british_thermal_unit": "BTU",
    "therms": "therm",
    "foot_pound": "ft_lbf", "ft_lb": "ft_lbf", "ftlb": "ft_lbf",

    # -- power -----------------------------------------------------------
    "watt": "W", "watts": "W",
    "kilowatt": "kW", "megawatt": "MW", "gigawatt": "GW", "terawatt": "TW",
    "milliwatt": "mW", "microwatt": "uW",
    "horsepower": "hp", "HP": "hp", "mechanical_horsepower": "hp",
    "PS": "hp_metric", "cv": "hp_metric", "metric_horsepower": "hp_metric",
    "btu/h": "BTU/h", "BTU/hr": "BTU/h", "btu_per_hour": "BTU/h",

    # -- temperature -----------------------------------------------------
    "°C": "celsius", "degC": "celsius", "deg_c": "celsius", "centigrade": "celsius",
    "°F": "fahrenheit", "degF": "fahrenheit", "deg_f": "fahrenheit",
    "K": "kelvin", "°K": "kelvin", "kelvins": "kelvin",
    "°R": "rankine", "degR": "rankine", "deg_r": "rankine",

    # -- time ------------------------------------------------------------
    "sec": "s", "secs": "s", "second": "s", "seconds": "s",
    "msec": "ms", "millisecond": "ms", "milliseconds": "ms",
    "usec": "us", "microsecond": "us", "microseconds": "us",
    "nsec": "ns", "nanosecond": "ns", "picosecond": "ps",
    "minute": "min", "minutes": "min", "mins": "min",
    "hour": "h", "hours": "h", "hr": "h", "hrs": "h",
    "day": "d", "days": "d",
    "weeks": "week", "fortnights": "fortnight",
    "year": "yr", "years": "yr", "julian_year": "yr",

    # -- pressure --------------------------------------------------------
    "pascal": "Pa", "pascals": "Pa",
    "kilopascal": "kPa", "megapascal": "MPa", "gigapascal": "GPa",
    "hectopascal": "hPa",
    "bars": "bar", "millibar": "mbar", "millibars": "mbar",
    "atmosphere": "atm", "atmospheres": "atm",
    "Torr": "torr",
    "mmhg": "mmHg", "mm_hg": "mmHg",
    "inhg": "inHg", "in_hg": "inHg",
    "PSI": "psi", "lbf/in2": "psi", "pounds_per_square_inch": "psi",

    # -- frequency -------------------------------------------------------
    "hertz": "Hz", "hz": "Hz",
    "kilohertz": "kHz", "megahertz": "MHz", "gigahertz": "GHz",
    "terahertz": "THz", "millihertz": "mHz",
    "RPM": "rpm", "rev/min": "rpm", "revolutions_per_minute": "rpm",

    # -- storage ---------------------------------------------------------
    "byte": "B", "bytes": "B", "bits": "bit",
    "KB": "kB", "kilobyte": "kB", "kilobytes": "kB",
    "megabyte": "MB", "megabytes": "MB",
    "gigabyte": "GB", "gigabytes": "GB",
    "terabyte": "TB", "terabytes": "TB", "petabyte": "PB", "petabytes": "PB",
    "kibibyte": "KiB", "mebibyte": "MiB", "gibibyte": "GiB",
    "tebibyte": "TiB", "pebibyte": "PiB",
    "kilobit": "kbit", "megabit": "Mbit", "gigabit": "Gbit",

    # -- angle -----------------------------------------------------------
    "°": "deg", "degree": "deg", "degrees": "deg",
    "radian": "rad", "radians": "rad", "milliradian": "mrad",
    "gradian": "grad", "gradians": "grad", "gon": "grad",
    "arcminute": "arcmin", "arcminutes": "arcmin",
    "arcsecond": "arcsec", "arcseconds": "arcsec",
    "revolution": "turn", "revolutions": "turn", "rev": "turn", "turns": "turn",

    # -- current ---------------------------------------------------------
    "ampere": "A", "amperes": "A", "amp": "A", "amps": "A",
    "kiloampere": "kA", "milliampere": "mA", "microampere": "uA",
    "nanoampere": "nA", "picoampere": "pA",

    # -- potential -------------------------------------------------------
    "volt": "V", "volts": "V",
    "megavolt": "MV", "kilovolt": "kV",
    "millivolt": "mV", "microvolt": "uV", "nanovolt": "nV",
}

# --------------------------------------------------------------------------
# Micro-sign aliases, generated rather than typed.
#
# "u" is written two ways that look identical on screen: MICRO SIGN (U+00B5),
# which is what a Mac's Option-M produces, and GREEK SMALL LETTER MU (U+03BC).
# A dict treats them as different keys, so "microseconds" typed by one user
# would silently fail for another. Both map to the ASCII spelling.
# Generated, so a new micro-prefixed unit picks this up automatically.
# --------------------------------------------------------------------------
_MICRO_SIGNS = ("\u00b5", "\u03bc")


def add_micro_aliases(categories: dict, aliases: dict) -> None:
    """Map both micro signs onto the ASCII ``u`` spelling of each unit.

    ``len > 1`` excludes ``"u"`` itself, the atomic mass unit, which is a unit
    and not a prefix.
    """
    for table in categories.values():
        for symbol in table:
            if len(symbol) > 1 and symbol.startswith("u"):
                for sign in _MICRO_SIGNS:
                    aliases.setdefault(sign + symbol[1:], symbol)


def build_index(
    categories: dict, aliases: dict, base_units: dict
) -> tuple[dict, list[str]]:
    """Build the symbol index and collect every inconsistency found.

    Returns ``(index, problems)``, where ``index`` maps a canonical symbol to
    ``(category, entry)`` and ``problems`` is empty when the registry is sound.
    Problems are collected rather than raised one at a time, so editing the
    registry surfaces every mistake in a single run.

    The inputs are arguments rather than module globals on purpose: that is what
    lets a test hand it a deliberately broken registry and assert on the report.

    >>> build_index({"a": {"x": 1.0}, "b": {"x": 1.0}},
    ...             {}, {"a": "x", "b": "x"})[1]
    ["symbol 'x' is defined in both 'a' and 'b'"]
    >>> build_index({"a": {"x": 1.0}}, {"q": "nope"}, {"a": "x"})[1]
    ["alias 'q' points at unknown unit 'nope'"]
    """
    index: dict[str, tuple[str, object]] = {}
    problems: list[str] = []

    for category, table in categories.items():
        for symbol, entry in table.items():
            if symbol in index:
                problems.append(
                    f"symbol {symbol!r} is defined in both "
                    f"{index[symbol][0]!r} and {category!r}"
                )
            index[symbol] = (category, entry)

    for alias, target in aliases.items():
        if alias in index:
            problems.append(
                f"alias {alias!r} shadows the canonical symbol {alias!r} "
                f"in {index[alias][0]!r}"
            )
        if target not in index:
            problems.append(f"alias {alias!r} points at unknown unit {target!r}")

    for category, base in base_units.items():
        if category not in categories:
            problems.append(f"BASE_UNITS has category {category!r} with no table")
        elif base not in categories[category]:
            problems.append(f"base unit {base!r} is not present in {category!r}")

    for category in categories:
        if category not in base_units:
            problems.append(f"category {category!r} has no declared base unit")
            continue
        base = base_units[category]
        if base not in categories[category]:
            continue  # already reported by the loop above; don't crash on it
        entry = categories[category][base]
        scale, offset = entry if isinstance(entry, tuple) else (entry, 0)
        if scale != 1 or offset != 0:
            problems.append(
                f"base unit {base!r} of {category!r} must have "
                f"scale 1 and offset 0, has {entry!r}"
            )

    return index, problems


add_micro_aliases(CATEGORIES, ALIASES)
_INDEX, _problems = build_index(CATEGORIES, ALIASES, BASE_UNITS)

if _problems:
    raise RegistryError(
        "the unit registry is inconsistent:\n  - " + "\n  - ".join(_problems)
    )

del _problems

#: Every spelling the registry accepts: canonical symbols plus aliases.
_SPELLINGS = sorted(set(_INDEX) | set(ALIASES))


# --------------------------------------------------------------------------
# Lookup API
# --------------------------------------------------------------------------
#: Spellings the registry refuses on purpose, each with the fix.
#:
#: These are not typos, they are genuinely ambiguous: resolving them to one
#: arbitrary meaning would return a confidently wrong number. Fuzzy matching is
#: no help here either -- it answers "C" with "c", the speed of light -- so each
#: one carries an explicit message instead.
AMBIGUOUS = {
    "C": "use 'celsius' or 'degC' (bare 'C' is the SI symbol for coulomb)",
    "F": "use 'fahrenheit' or 'degF' (bare 'F' is the SI symbol for farad)",
    "R": "use 'rankine' or 'degR' (bare 'R' is the symbol for roentgen)",
    "ton": (
        "'ton' means three different masses: use 't' (tonne, 1000 kg), "
        "'ton_us' (short, 907.18474 kg) or 'ton_uk' (long, 1016.0469088 kg)"
    ),
    "tons": "see 'ton': use 't', 'ton_us' or 'ton_uk'",
    "pt": "'pt' is both point and pint: use 'pt_us' or 'pt_imp' for pints",
    "b": "use 'bit' or 'B' (byte) -- 'b' and 'B' differ only by case",
    "kb": "use 'kbit' (1000 bits) or 'kB' (1000 bytes)",
    "mb": "use 'Mbit' (10**6 bits) or 'MB' (10**6 bytes)",
    "gb": "use 'Gbit' (10**9 bits) or 'GB' (10**9 bytes)",
    "tb": "use 'TB' (10**12 bytes) or 'TiB' (2**40 bytes)",
    "cal_cap": "use 'kcal' for the food Calorie, or 'cal' for the gram calorie",
    "fl_ounce": "use 'floz_us' or 'floz_imp'",
    "hp_imp": "use 'hp' (mechanical) or 'hp_metric' (PS)",
}


def as_affine(entry: object) -> tuple[object, object]:
    """Return ``(scale, offset)`` for a registry entry.

    Plain numeric entries are purely multiplicative, so their offset is zero.
    """
    if isinstance(entry, tuple):
        return entry
    return entry, 0


def resolve(unit: object) -> tuple[str, str, object]:
    """Resolve any accepted spelling to ``(symbol, category, entry)``.

    >>> resolve("kilometre")[:2]
    ('km', 'length')
    >>> resolve("MiB")[:2]
    ('MiB', 'storage')

    Raises :class:`~pyconvert.exceptions.UnknownUnitError` otherwise, with a
    suggestion where one is close enough to be useful.
    """
    if not isinstance(unit, str):
        raise UnknownUnitError(unit, _SPELLINGS)
    symbol = ALIASES.get(unit, unit)
    try:
        category, entry = _INDEX[symbol]
    except KeyError:
        if unit in AMBIGUOUS:
            raise UnknownUnitError(unit, hint=AMBIGUOUS[unit]) from None
        raise UnknownUnitError(unit, _SPELLINGS) from None
    return symbol, category, entry


def category_of(unit: object) -> str:
    """Return the category a unit belongs to.

    >>> category_of("psi")
    'pressure'
    """
    return resolve(unit)[1]


def units_in(category: str) -> list[str]:
    """Return the canonical symbols of one category, sorted.

    >>> units_in("temperature")
    ['celsius', 'fahrenheit', 'kelvin', 'rankine']
    """
    try:
        table = CATEGORIES[category]
    except KeyError:
        raise UnknownCategoryError(category, list(CATEGORIES)) from None
    return sorted(table)


def all_units(include_aliases: bool = False) -> list[str]:
    """Return every canonical symbol, sorted; with aliases if asked."""
    if include_aliases:
        return list(_SPELLINGS)
    return sorted(_INDEX)
