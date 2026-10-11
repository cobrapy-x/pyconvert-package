"""Number-base conversion between any two bases from 2 to 36.

Run it with::

    python examples/number_systems.py
"""

from pyconvert import DIGITS, InvalidBaseError, InvalidDigitError, convert_base


def main():
    print("\n--- the number 255 in several bases ---")
    for base in (2, 8, 10, 16, 36):
        print(f"  base {base:<3} {convert_base(255, 10, base)}")

    print("\n--- between non-decimal bases directly ---")
    for number, source, target in [
        ("10101111", 2, 16),
        ("FF", 16, 2),
        ("777", 8, 16),
        ("ZZ", 36, 10),
        ("1101", 2, 3),
    ]:
        print(f"  {number:>10} (base {source:>2}) -> "
              f"{convert_base(number, source, target):>12} (base {target})")

    print("\n--- input is forgiving ---")
    for number, source in [("ff", 16), ("FF", 16), ("1111_1111", 2), ("  FF  ", 16)]:
        decimal = convert_base(number, source, 10)
        print(f"  {number!r:<14} base {source:<3} -> {decimal}")

    print("\n--- negatives and zero ---")
    for number in (-255, 0, -1):
        print(f"  {number:>5} -> base 16: {convert_base(number, 10, 16)}")

    print("\n--- fractions, exact where they terminate ---")
    for number, source, target in [
        ("0.5", 10, 2),
        ("0.25", 10, 2),
        ("A.8", 16, 10),
        ("0.4", 16, 10),
    ]:
        print(f"  {number:>6} (base {source:>2}) -> "
              f"{convert_base(number, source, target)} (base {target})")

    print("\n--- and truncated where they do not ---")
    print(f"  0.1 decimal in binary          : {convert_base('0.1', 10, 2)}")
    print(f"  the same, to 4 places          : {convert_base('0.1', 10, 2, 4)}")
    print(f"  the same, to 40 places         : {convert_base('0.1', 10, 2, 40)}")
    print("  one tenth has no finite binary form, so it is cut off, not wrong")

    print("\n--- counting in base 36 uses the whole alphabet ---")
    print(f"  digits: {DIGITS}")
    print("  " + "  ".join(f"{n}={convert_base(n, 10, 36)}" for n in range(33, 40)))

    print("\n--- the result is always a string ---")
    result = convert_base("FF", 16, 10)
    print(f"  convert_base('FF', 16, 10) -> {result!r}  (type {type(result).__name__})")
    print(f"  int(result) + 1            -> {int(result) + 1}")

    print("\n--- errors ---")
    for args in [(1, 10, 64), ("G", 16, 10), ("", 10, 2), (10.5, 10, 2)]:
        try:
            convert_base(*args)
        except (InvalidBaseError, InvalidDigitError, TypeError) as error:
            print(f"  convert_base{args}")
            print(f"    -> {type(error).__name__}: {error}")
    print()


if __name__ == "__main__":
    main()
