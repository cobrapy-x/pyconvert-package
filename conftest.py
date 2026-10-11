"""Make the repository root importable so ``import pyconvert`` works in tests.

pytest adds a test file's own directory to ``sys.path``, not the project root,
so without this a source checkout would need ``pip install -e .`` before the
suite could run. A root-level ``conftest.py`` puts the root on the path, which
is the conventional fix.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
