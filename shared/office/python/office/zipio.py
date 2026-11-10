"""Unpack and pack OOXML files with Python zipfile (Windows and Unix).

Usage (from a skill directory, or via the per-skill launcher):

    python scripts/office/zipio.py unpack input.docx unpacked/
    python scripts/office/zipio.py pack unpacked/ output.docx

Do not use Expand-Archive for Office files: it does not preserve OOXML
entry names or compression, and is not a sufficient substitute.
Symlink archive entries are rejected — files from external parties are
untrusted.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from helpers import rezip, safe_extract
import zipfile


def unpack_office(archive: Path, dest: Path) -> None:
    archive = Path(archive)
    dest = Path(dest)
    if not archive.is_file():
        raise FileNotFoundError(f"{archive} is not a file")
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zf:
        safe_extract(zf, dest)


def pack_office(src_dir: Path, out_path: Path) -> None:
    src_dir = Path(src_dir)
    out_path = Path(out_path)
    if not src_dir.is_dir():
        raise FileNotFoundError(f"{src_dir} is not a directory")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rezip(src_dir, out_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Unpack or pack an Office (OOXML) file with zipfile. "
        "Refuses symlink entries. Do not use Expand-Archive for these files."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    unpack_p = sub.add_parser("unpack", help="Extract an Office file into a directory")
    unpack_p.add_argument("archive")
    unpack_p.add_argument("dest")

    pack_p = sub.add_parser("pack", help="Repack a directory into an Office file")
    pack_p.add_argument("src_dir")
    pack_p.add_argument("out_path")

    args = parser.parse_args(argv)
    try:
        if args.command == "unpack":
            unpack_office(Path(args.archive), Path(args.dest))
        else:
            pack_office(Path(args.src_dir), Path(args.out_path))
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
