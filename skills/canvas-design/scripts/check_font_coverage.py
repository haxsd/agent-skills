#!/usr/bin/env python3
"""Check whether font files cover every non-whitespace character in text.

Usage:
    python check_font_coverage.py FONT [FONT ...] --text TEXT [--json]
    python check_font_coverage.py FONT [FONT ...] --text-file PATH [--json]

Exit codes: 0 all characters covered; 1 missing characters; 2 invalid input.
The checker parses cmap tables only and never executes font code.
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

MAX_FONT_BYTES = 64 * 1024 * 1024
MAX_TEXT_BYTES = 1024 * 1024
MAX_TABLE_COUNT = 4096
MAX_CMAP_RECORDS = 1024
MAX_SEGMENTS = 8192
MAX_GROUPS = 100000
SFNT_TAGS = (b"\x00\x01\x00\x00", b"OTTO", b"true", b"typ1")


class FontError(ValueError):
    """Raised when a font cannot be parsed safely."""


def _u16(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 2 > len(data):
        raise FontError("truncated font table")
    return struct.unpack_from(">H", data, offset)[0]


def _u32(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 4 > len(data):
        raise FontError("truncated font table")
    return struct.unpack_from(">I", data, offset)[0]


def _face_offset(data: bytes, face: int) -> int:
    if data[:4] == b"ttcf":
        if len(data) < 12:
            raise FontError("truncated TrueType Collection header")
        count = _u32(data, 8)
        if count == 0 or count > MAX_TABLE_COUNT:
            raise FontError("invalid TrueType Collection font count")
        if face < 0 or face >= count:
            raise FontError(f"face {face} is outside collection range 0..{count - 1}")
        offset = _u32(data, 12 + 4 * face)
        if offset >= len(data):
            raise FontError("font face offset is outside the file")
        return offset

    if data[:4] not in SFNT_TAGS:
        raise FontError("not a supported TrueType/OpenType file")
    if face != 0:
        raise FontError("face selection is only available for TrueType Collections")
    return 0


def _read_cmap(data: bytes, face: int = 0) -> bytes:
    base = _face_offset(data, face)
    num_tables = _u16(data, base + 4)
    if num_tables == 0 or num_tables > MAX_TABLE_COUNT:
        raise FontError("invalid table count")

    cmap_offset = None
    cmap_length = None
    for index in range(num_tables):
        record = base + 12 + index * 16
        if record + 16 > len(data):
            raise FontError("truncated table directory")
        tag = data[record:record + 4]
        if tag == b"cmap":
            cmap_offset = _u32(data, record + 8)
            cmap_length = _u32(data, record + 12)
            break
    if cmap_offset is None or cmap_length is None:
        raise FontError("font has no cmap table")
    if cmap_length == 0 or cmap_offset + cmap_length > len(data):
        raise FontError("cmap table is outside the file")
    return data[cmap_offset:cmap_offset + cmap_length]


def _parse_subtable(cmap: bytes, offset: int):
    if offset < 0 or offset + 4 > len(cmap):
        raise FontError("truncated cmap subtable")
    fmt = _u16(cmap, offset)
    length = _u16(cmap, offset + 2) if fmt in (0, 4, 6) else _u32(cmap, offset + 4)
    if length < 4 or offset + length > len(cmap):
        raise FontError("cmap subtable is outside the file")

    if fmt == 0:
        if length < 262:
            raise FontError("truncated cmap format 0")
        table = cmap[offset + 6:offset + 6 + 256]
        return lambda code: code < 256 and table[code] != 0

    if fmt == 6:
        if length < 10:
            raise FontError("truncated cmap format 6")
        first = _u16(cmap, offset + 6)
        count = _u16(cmap, offset + 8)
        if 10 + count * 2 > length:
            raise FontError("cmap format 6 glyph array is truncated")
        glyphs = struct.unpack_from(f">{count}H", cmap, offset + 10) if count else ()
        return lambda code: first <= code < first + count and glyphs[code - first] != 0

    if fmt == 4:
        if length < 16:
            raise FontError("truncated cmap format 4")
        seg_count = _u16(cmap, offset + 6) // 2
        if seg_count == 0 or seg_count > MAX_SEGMENTS:
            raise FontError("invalid cmap format 4 segment count")
        end_offset = offset + 14
        start_offset = end_offset + 2 * seg_count + 2
        delta_offset = start_offset + 2 * seg_count
        range_offset = delta_offset + 2 * seg_count
        if range_offset + 2 * seg_count > offset + length:
            raise FontError("cmap format 4 arrays are truncated")
        ends = struct.unpack_from(f">{seg_count}H", cmap, end_offset)
        starts = struct.unpack_from(f">{seg_count}H", cmap, start_offset)
        deltas = struct.unpack_from(f">{seg_count}h", cmap, delta_offset)
        ranges = struct.unpack_from(f">{seg_count}H", cmap, range_offset)

        def covers(code: int) -> bool:
            if code > 0xFFFF:
                return False
            for index in range(seg_count):
                start = starts[index]
                end = ends[index]
                if not (start <= code <= end):
                    continue
                range_position = range_offset + 2 * index
                range_value = ranges[index]
                if range_value == 0:
                    glyph = (code + deltas[index]) & 0xFFFF
                else:
                    glyph_position = range_position + range_value + 2 * (code - start)
                    if glyph_position + 2 > offset + length:
                        raise FontError("cmap format 4 glyph index is truncated")
                    glyph = _u16(cmap, glyph_position)
                    if glyph:
                        glyph = (glyph + deltas[index]) & 0xFFFF
                return glyph != 0
            return False

        return covers

    if fmt == 12:
        if length < 16:
            raise FontError("truncated cmap format 12")
        group_count = _u32(cmap, offset + 12)
        if group_count == 0 or group_count > MAX_GROUPS:
            raise FontError("invalid cmap format 12 group count")
        if 16 + group_count * 12 > length:
            raise FontError("cmap format 12 groups are truncated")
        groups = [
            struct.unpack_from(">III", cmap, offset + 16 + index * 12)
            for index in range(group_count)
        ]

        def covers(code: int) -> bool:
            for start, end, start_glyph in groups:
                if start <= code <= end:
                    return start_glyph + (code - start) != 0
            return False

        return covers

    raise FontError(f"unsupported cmap format {fmt}")


def _lookups(cmap: bytes):
    if len(cmap) < 4:
        raise FontError("truncated cmap header")
    count = _u16(cmap, 2)
    if count == 0 or count > MAX_CMAP_RECORDS:
        raise FontError("invalid cmap encoding record count")
    if 4 + count * 8 > len(cmap):
        raise FontError("truncated cmap encoding records")

    lookups = []
    seen_offsets = set()
    for index in range(count):
        record = 4 + index * 8
        platform = _u16(cmap, record)
        encoding = _u16(cmap, record + 2)
        if platform != 0 and not (platform == 3 and encoding in (1, 10)):
            continue
        offset = _u32(cmap, record + 4)
        if offset in seen_offsets:
            continue
        seen_offsets.add(offset)
        fmt = _u16(cmap, offset)
        if fmt in (0, 4, 6, 12):
            lookups.append(_parse_subtable(cmap, offset))
    if not lookups:
        raise FontError("font has no supported Unicode cmap subtable")
    return lookups


def _characters(text: str) -> list[str]:
    return sorted({char for char in text if not char.isspace()})


def inspect_fonts(font_paths, text: str, face: int = 0) -> dict:
    characters = _characters(text)
    if not characters:
        raise ValueError("text contains no non-whitespace characters")
    if len(text.encode("utf-8")) > MAX_TEXT_BYTES:
        raise ValueError("text is too large")

    covered = set()
    font_reports = []
    for raw_path in font_paths:
        path = Path(raw_path)
        try:
            size = path.stat().st_size
        except OSError as exc:
            raise FontError(f"{path}: {exc}") from exc
        if size == 0 or size > MAX_FONT_BYTES:
            raise FontError(f"{path}: empty or larger than {MAX_FONT_BYTES} bytes")
        try:
            data = path.read_bytes()
            lookups = _lookups(_read_cmap(data, face))
            missing = [
                char for char in characters
                if not any(lookup(ord(char)) for lookup in lookups)
            ]
        except FontError as exc:
            raise FontError(f"{path}: {exc}") from exc
        covered.update(set(characters) - set(missing))
        font_reports.append({
            "path": str(path),
            "face": face,
            "missing": missing,
            "covered": len(characters) - len(missing),
        })

    all_missing = sorted(set(characters) - covered)
    return {
        "ok": not all_missing,
        "characters": len(characters),
        "covered": len(covered),
        "missing": all_missing,
        "fonts": font_reports,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Check font cmap coverage for the non-whitespace characters in text."
    )
    parser.add_argument("fonts", nargs="+", help="TTF/OTF/TTC font paths")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text", help="text to check")
    source.add_argument("--text-file", help="UTF-8 file containing text to check")
    parser.add_argument("--face", type=int, default=0, help="face index for TTC fonts")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)

    try:
        if args.text_file:
            path = Path(args.text_file)
            if path.stat().st_size > MAX_TEXT_BYTES:
                raise ValueError("text file is too large")
            text = path.read_text(encoding="utf-8-sig")
        else:
            text = args.text
        report = inspect_fonts(args.fonts, text, face=args.face)
    except (OSError, UnicodeError, FontError, ValueError) as exc:
        print(f"font coverage check failed: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    elif report["ok"]:
        print(
            f"Coverage OK: {report['covered']}/{report['characters']} characters "
            f"across {len(report['fonts'])} font(s)."
        )
    else:
        print(
            f"Missing glyphs for {len(report['missing'])} character(s): "
            f"{json.dumps(report['missing'], ensure_ascii=False)}"
        )
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
