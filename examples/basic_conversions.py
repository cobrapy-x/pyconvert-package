"""Unit conversion, from the obvious to the slightly surprising.

Run it with::

    python examples/basic_conversions.py
"""

import pyconvert
from pyconvert import IncompatibleUnitsError, UnknownUnitError, convert


def show(value, source, target, note=""):
    result = convert(value, source, target)
    comment = f"   # {note}" if note else ""
    print(f"  {value:>12g} {source:<10} = {result:<22g} {target:<10}{comment}")


def main():
    print("\n--- everyday conversions ---")
    show(100, "km", "mi")
    show(5, "ft", "cm")
    show(70, "kg", "lb")
    show(2, "L", "cup_us")
    show(60, "mph", "km/h")

    print("\n--- temperature, computed exactly ---")
    for celsius in (-40, 0, 37, 100):
        fahrenheit = convert(celsius, "celsius", "fahrenheit")
        kelvin = convert(celsius, "celsius", "kelvin")
        print(f"  {celsius:>5}degC = {fahrenheit:>8}degF = {kelvin:>8} K")
    print("  note: 212.0 and 32.0 exactly, not 211.99999999999997")

    print("\n--- data sizes: decimal and binary prefixes are not the same ---")
    show(1, "GB", "GiB", "what a 1 GB drive shows as in GiB")
    show(1, "GiB", "MiB")
    show(1, "B", "bit")
    show(500, "Mbit", "MB", "a 500 Mbit/s line in megabytes")

    print("\n--- pairs nobody wrote down, but which work anyway ---")
    show(1, "furlong", "nmi")
    show(1, "therm", "kWh")
    show(1, "solar_mass", "t")
    show(1, "ly", "au")
    show(1, "atm", "psi")
    show(1, "acre", "ha")

    print("\n--- alternative spellings, all the same unit ---")
    for spelling in ("km", "kilometre", "kilometer", "kilometers"):
        print(f"  {spelling:<12} -> {convert(1, spelling, 'm')} m")
    for spelling in ("us", "µs", "μs", "microsecond"):
        print(f"  {spelling:<12} -> {convert(1, spelling, 'ms')} ms")

    print("\n--- introspection ---")
    print(f"  {len(pyconvert.list_categories())} categories, "
          f"{len(pyconvert.list_units())} units")
    print(f"  pressure units: {', '.join(pyconvert.list_units('pressure'))}")
    print(f"  category_of('psi')   -> {pyconvert.category_of('psi')}")
    print(f"  base_unit('pressure')-> {pyconvert.base_unit('pressure')}")

    print("\n--- errors that explain themselves ---")
    for value, source, target in [(1, "kg", "m"), (1, "KM", "mi"), (1, "ton", "kg")]:
        try:
            convert(value, source, target)
        except (IncompatibleUnitsError, UnknownUnitError) as error:
            print(f"  convert({value}, {source!r}, {target!r})")
            print(f"    -> {type(error).__name__}: {error}")
    print()


if __name__ == "__main__":
    main()
