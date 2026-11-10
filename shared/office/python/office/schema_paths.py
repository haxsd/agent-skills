"""Locate the shared OOXML XSD directory used by the Office skill validators."""

from __future__ import annotations

import os
from pathlib import Path

MARKER = "ISO-IEC29500-4_2016"


def _is_schemas_dir(path: Path) -> bool:
    return path.is_dir() and (path / MARKER).is_dir()


def resolve_schemas_dir(start: Path | None = None) -> Path:
    env = os.environ.get("AGENT_SKILLS_OFFICE_SCHEMAS") or os.environ.get("OFFICE_SCHEMAS_DIR")
    if env:
        candidate = Path(env).expanduser()
        if _is_schemas_dir(candidate):
            return candidate.resolve()
        raise FileNotFoundError(
            f"Office schemas env points to {candidate}, but {MARKER} was not found"
        )

    start = Path(start or __file__).resolve()
    here = start.parent if start.is_file() else start
    for adj in (here / "schemas", here.parent / "schemas"):
        if _is_schemas_dir(adj):
            return adj.resolve()

    for parent in [here, *here.parents]:
        # shared/office/python/office -> shared/office/schemas
        # and leftover skill-local scripts/office/schemas
        if _is_schemas_dir(parent / "schemas"):
            return (parent / "schemas").resolve()
        candidate = parent / "shared" / "office" / "schemas"
        if _is_schemas_dir(candidate):
            return candidate.resolve()

    home_shared = Path.home() / "tools" / "shared" / "office" / "schemas"
    if _is_schemas_dir(home_shared):
        return home_shared.resolve()

    raise FileNotFoundError(
        "Shared OOXML schemas not found. Expected repo shared/office/schemas "
        "or ~/tools/shared/office/schemas after install.ps1, "
        "or set AGENT_SKILLS_OFFICE_SCHEMAS."
    )
