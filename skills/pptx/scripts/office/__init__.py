"""Shim package: implementation lives in shared/office/python/office.

Importing `office` from a skill's `scripts/` directory exposes that single
copy. Path lookup covers the repository tree and `~/tools/shared` after
install.ps1 links `shared/`.
"""

from ._path import locate_office_python, prepare_sys_path

_IMPL = prepare_sys_path()
__path__ = [str(_IMPL)]
