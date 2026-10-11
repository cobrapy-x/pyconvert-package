# Contributing to PyConvert

Thanks for your interest. This is a small library, so the bar is simple: a
change should be correct, covered by a test, and leave `pytest` and
`ruff check .` green.

## Getting set up

```bash
git clone https://github.com/cobrapy-x/pyconvert-package.git
cd pyconvert-package
python -m pip install -e ".[dev]"

pytest           # 1072 tests, including every docstring example
ruff check .
```

`pytest` with no arguments runs the suite in `tests/` *and* the doctests in
`pyconvert/`, because the examples in the docstrings are the same ones in the
README — they are checked rather than trusted.

## How the library is laid out

| File | Responsibility |
|---|---|
| `pyconvert/registry.py` | The data: all 15 category tables, the aliases, and the index built from them |
| `pyconvert/units.py` | The conversion engine and the introspection helpers |
| `pyconvert/bases.py` | Number-base conversion |
| `pyconvert/exceptions.py` | The error hierarchy |

`bases.py` is named that way rather than `numbers.py` because the standard
library already has a `numbers` module — the one holding `numbers.Real`, which
`units.py` imports.

## Adding a unit

Units are stored as **how big one of them is, in the category's base unit**.
That is the whole trick: a conversion is then one ratio,
`value * f_source / f_target`, and every pair in the category works without
being written down.

1. Add an entry to the right table in `registry.py`. One nautical mile is
   1852 metres, so under `LENGTH` it is `"nmi": 1852.0`.

2. **If the factor is exact by definition, write the definition, not the
   decimal.** An inch *is* 25.4 mm — that is a definition, not a measurement.
   Those are built from exact rationals and rounded to `float` once:

   ```python
   "ac": float(4840 * _YD_Q ** 2),     # an acre is 4840 square yards, exactly
   ```

   Computing the same thing in floating point gives a different answer:
   `231 * 0.0254 ** 3` is `0.0037854117839999997`, three roundings away from
   the correctly rounded `0.003785411784`. Mark genuinely measured values
   (particle masses, the solar mass) with a comment saying so.

3. **Add aliases** for the spellings people will actually type — the long name,
   the plural, and an ASCII form if the symbol needs a character they cannot
   easily reach. Micro-prefixed units get their Unicode variants generated
   automatically; do not add those by hand.

4. **Check the symbol is not already taken.** All 15 categories share one
   namespace. If it collides, `import pyconvert` fails immediately with a
   `RegistryError` naming both categories — that check runs at import, so you
   will know in one second rather than from a bug report.

5. **If the spelling is genuinely ambiguous, do not pick a winner.** Add it to
   `AMBIGUOUS` with a message saying what to use instead. `ton` means three
   masses that differ by up to 12%; `oz` is both a mass and a volume. Returning
   one of them silently is worse than refusing.

6. Add a test. The most valuable kind asserts a relationship fixed by
   definition and independent of the metre or the kilogram:

   ```python
   (1, "mi", "ft", 5280),
   (1, "gal_us", "in3", 231),
   ```

   An inverted factor still round-trips perfectly, so a round-trip test will
   not catch it — but `1 mi == 5280 ft` will. That is exactly the bug that
   shipped in 0.1.0.

## Adding a category

Add the table, add it to `CATEGORIES`, and declare its base unit in
`BASE_UNITS`. The base unit must have scale 1 and offset 0; `build_index`
enforces that at import.

If any unit in the category needs an **offset** rather than just a scale (as
temperature does), store its entry as a `(scale, offset)` tuple of
`Fraction`s, where `base_value = x * scale + offset`. The engine routes any
conversion involving a tuple entry through exact rational arithmetic, which is
what makes `100 °C → °F` return exactly `212.0` instead of
`211.99999999999997`.

## Invariants the suite enforces

These hold for every unit, and the tests will tell you if a change breaks one:

- Every unit round-trips through its category's base unit.
- For every pair `a`, `b` in a multiplicative category,
  `convert(1, a, b) * convert(1, b, a) == 1`.
- Conversion is transitive: `a → c` agrees with `a → b → c`.
- No symbol is claimed by two categories, no alias shadows a canonical symbol,
  and no alias points at a unit that does not exist.
- Every cross-category pair raises `IncompatibleUnitsError`.
- Every spelling in `AMBIGUOUS` is genuinely unresolvable, so its hint is
  reachable.
- Every unit symbol appears in `README.md`.

## Style

`ruff check .` is the whole style guide; its configuration lives in
`pyproject.toml`. Comments are welcome where they explain *why* — a surprising
factor, a definition chosen over an alternative, a deliberate refusal. Prefer
those over comments restating what the code does.

## Submitting

1. Fork the repository and branch off `main`.
2. Make the change, with tests.
3. Run `pytest` and `ruff check .`.
4. Add a line to `CHANGELOG.md` under an `## [Unreleased]` heading.
5. Open a pull request describing what changed and why.

Bug reports are just as useful as patches. For a wrong conversion factor,
please include the units, the result you got, the result you expected, and a
source for the correct value.
