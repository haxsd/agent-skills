"""Launcher for `python scripts/office/validate.py`. Implementation is shared."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

# When this file is run as a script, sys.path[0] is scripts/office, so
# `_path` is a sibling module — not `office._path`.
from _path import prepare_sys_path

if __name__ == "__main__":
    impl = prepare_sys_path()
    sys.argv[0] = str(impl / "validate.py")
    runpy.run_path(str(impl / "validate.py"), run_name="__main__")
