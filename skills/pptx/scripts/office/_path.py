"""Locate the single shared Office Python package (not a skill-local copy)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_MARKER = "soffice.py"


def _is_python_root(path: Path) -> bool:
    return (path / "office" / _MARKER).is_file()


def _is_package_dir(path: Path) -> bool:
    return (path / _MARKER).is_file() and path.name == "office"


def locate_office_python() -> Path:
    """Return `shared/office/python` (the directory that contains the `office` package)."""
    env = os.environ.get("AGENT_SKILLS_OFFICE_PYTHON")
    if env:
        candidate = Path(env).expanduser()
        if _is_python_root(candidate):
            return candidate.resolve()
        if _is_package_dir(candidate):
            return candidate.parent.resolve()
        raise FileNotFoundError(
            f"AGENT_SKILLS_OFFICE_PYTHON points to {candidate}, but "
            "shared/office/python/office/soffice.py was not found"
        )

    here = Path(__file__).resolve().parent
    for parent in [here, *here.parents]:
        candidate = parent / "shared" / "office" / "python"
        if _is_python_root(candidate):
            return candidate.resolve()

    home = Path.home() / "tools" / "shared" / "office" / "python"
    if _is_python_root(home):
        return home.resolve()

    raise FileNotFoundError(
        "Shared Office Python package not found. Expected repo "
        "shared/office/python/office or ~/tools/shared/office/python/office "
        "after install.ps1, or set AGENT_SKILLS_OFFICE_PYTHON."
    )


def prepare_sys_path() -> Path:
    """Put the shared package on sys.path and return `.../python/office`."""
    python_root = locate_office_python()
    impl = python_root / "office"
    for path in (str(python_root), str(impl)):
        if path in sys.path:
            sys.path.remove(path)
        sys.path.insert(0, path)
    return impl
