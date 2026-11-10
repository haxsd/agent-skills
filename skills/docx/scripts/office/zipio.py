"""Launcher for `python scripts/office/zipio.py`. Implementation is shared."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

from _path import prepare_sys_path

if __name__ == "__main__":
    impl = prepare_sys_path()
    sys.argv[0] = str(impl / "zipio.py")
    runpy.run_path(str(impl / "zipio.py"), run_name="__main__")
