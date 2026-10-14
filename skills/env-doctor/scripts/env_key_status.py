#!/usr/bin/env python3
"""Read-only dotenv key-state reporter for env-doctor.

Reports, for every key it can name, only a state: present / empty / missing /
unknown. Values, comments and raw lines never appear in the output, not even
in gaps - which is the point: the calling agent gets key names and states
instead of reading an environment file itself, while the file the user
explicitly handed over is opened here (the program), not by the model.

Deliberate boundaries: stdlib only, offline, read-only, one file per --env and
an optional --example; no project script is imported or executed and no shell
is involved; report fields contain validated key names, states and static gap
reasons, not raw file values. Symlinks and Windows reparse points in the path
are conservatively refused, as are non-regular files, files above 1 MiB,
unsupported encodings and decoded NUL content. This is not an OS sandbox:
path checks and opening are not atomic against concurrent filesystem changes.

Parsing is deliberately small: standalone/unquoted comments, ``export``,
quoted and unquoted values, and case-preserving keys. Trailing text after a
quoted value (including a comment) is unsupported and produces a gap. Interpolation, line continuations, quoted
multi-line values and escape sequences are *not* evaluated; the affected keys
are reported as unknown with a gap, and parsing stops at the first gap so the
inner lines of an unsupported multi-line value can never be mistaken for keys.

Exit codes: 0 report produced; 1 refused or incomplete report; 2 invalid args.
"""

import argparse
import json
import os
import re
import stat
import sys

SCHEMA_VERSION = 1
MAX_FILE_BYTES = 1024 * 1024
KEY_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]*$")
ASSIGNMENT_PATTERN = re.compile(r"^(?:export\s+)?([A-Za-z0-9_.-]+)\s*=\s*(.*)$")
INTERPOLATION_PATTERN = re.compile(r"\$\{|\$[A-Za-z_]")
COMMENT_PATTERN = re.compile(r"\s#")
ESCAPE_PATTERN = re.compile(r"\\.")

DISCLAIMER = (
    "只报告文件中的键名与状态：不输出值、不解析插值、不连接进程环境，"
    "也不能证明运行时已注入这些变量。"
)
NOTES = (
    "结果只描述给定的导出/样例文件：不代表进程、CI 或 secret store 的实际注入情况，"
    "插值、续行与多行值不会被求值（相关键标 unknown 并列 gap）。",
)


class DotenvSyntaxError(Exception):
    def __init__(self, reason, line_no):
        super().__init__(reason)
        self.reason = reason
        self.line_no = line_no


def parse_dotenv(text):
    """Return (states, gaps, stopped).

    states maps each key, with its original case, to present/empty/unknown.
    A gap ends parsing: lines after it may be the inside of a multi-line
    value, so they must never be reported as keys.
    """
    states = {}
    gaps = []
    for line_no, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = ASSIGNMENT_PATTERN.match(line)
        if not match:
            reason = "invalid-key" if "=" in line else "line-without-assignment"
            gaps.append({"line": line_no, "reason": reason})
            return states, gaps, True
        key, rest = match.group(1), match.group(2).strip()
        if not KEY_PATTERN.match(key):
            gaps.append({"line": line_no, "reason": "invalid-key"})
            return states, gaps, True
        try:
            status, reason = _classify_value(rest, line_no)
        except DotenvSyntaxError as error:
            gaps.append({"line": error.line_no, "reason": error.reason})
            return states, gaps, True
        states[key] = status
        if reason is not None:
            gaps.append({"line": line_no, "reason": reason})
            return states, gaps, True
    return states, gaps, False


def _classify_value(rest, line_no):
    """Return (status, gap_reason). Raises DotenvSyntaxError for broken input."""
    if rest.startswith("'"):
        end = rest.find("'", 1)
        if end == -1:
            raise DotenvSyntaxError("unterminated-quote", line_no)
        return _closed_value(rest, end + 1)
    if rest.startswith('"'):
        end = _closing_quote(rest)
        if end == -1:
            if rest.endswith("\\"):
                return "unknown", "line-continuation"
            raise DotenvSyntaxError("unterminated-quote", line_no)
        body = rest[1:end]
        if rest[end + 1:].strip():
            return "unknown", "quoted-value-trailing-text"
        if ESCAPE_PATTERN.search(body):
            return "unknown", "escape-not-interpreted"
        if INTERPOLATION_PATTERN.search(body):
            return "unknown", "unsupported-interpolation"
        return ("present" if body else "empty"), None
    # Unquoted: a '#' after whitespace starts a comment.
    comment = COMMENT_PATTERN.search(rest)
    if comment is not None:
        rest = rest[:comment.start()]
    rest = rest.strip()
    if rest.endswith("\\"):
        return "unknown", "line-continuation"
    if INTERPOLATION_PATTERN.search(rest):
        return "unknown", "unsupported-interpolation"
    return ("present" if rest else "empty"), None


def _closed_value(rest, index):
    if rest[index:].strip():
        return "unknown", "quoted-value-trailing-text"
    body = rest[1:index - 1]
    if ESCAPE_PATTERN.search(body):
        return "unknown", "escape-not-interpreted"
    return ("present" if body else "empty"), None


def _closing_quote(rest):
    index = 1
    while index < len(rest):
        if rest[index] == "\\":
            index += 2
            continue
        if rest[index] == '"':
            return index
        index += 1
    return -1


def build_report(env_text, example_text):
    env_states, env_gaps, env_stopped = parse_dotenv(env_text)
    if example_text is not None:
        example_states, example_gaps, example_stopped = parse_dotenv(example_text)
    else:
        example_states, example_gaps, example_stopped = {}, [], False
    incomplete = bool(env_gaps or example_gaps)
    if example_text is None:
        variables = [
            {"key": key, "status": env_states[key], "seenIn": "env"}
            for key in sorted(env_states)
        ]
        mode = "single"
    else:
        mode = "compare"
        variables = []
        for key in sorted(set(example_states) | set(env_states)):
            if key in env_states and key not in example_states:
                status = env_states[key]
                seen = "env"
            elif key in example_states and key not in env_states:
                seen = "example-only"
                status = "unknown" if (env_stopped or example_stopped) else "missing"
            else:
                seen = "env+example"
                status = env_states[key]
            variables.append({"key": key, "status": status, "seenIn": seen})
    return {
        "schemaVersion": SCHEMA_VERSION,
        "status": "incomplete" if incomplete else "ok",
        "mode": mode,
        "variables": variables,
        "gaps": gaps_for_report(env_gaps, example_gaps),
        "notes": list(NOTES),
        "disclaimer": DISCLAIMER,
    }


def gaps_for_report(env_gaps, example_gaps):
    """Return the env and example gaps with static file tags, never content."""
    gaps = [{"file": "env", **gap} for gap in env_gaps]
    gaps.extend({"file": "example", **gap} for gap in example_gaps)
    return gaps


def _resolve_symlink(path):
    """Return True when the path or a parent directory is a symlink/reparse point."""
    current = os.path.abspath(path)
    while True:
        if os.path.islink(current):
            return True
        try:
            info = os.lstat(current)
        except OSError:
            info = None
        if info is not None and getattr(info, "st_file_attributes", 0) & getattr(
                stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
            return True
        parent = os.path.dirname(current)
        if parent == current:
            return False
        current = parent


def _read_regular(path):
    """Return (kind, text). kind is ok/too-large/not-regular/not-found/binary/unreadable."""
    try:
        info = os.stat(path)
    except OSError:
        return "not-found", None
    if not stat.S_ISREG(info.st_mode):
        return "not-regular", None
    if info.st_size > MAX_FILE_BYTES:
        return "too-large", None
    try:
        with open(path, "rb") as handle:
            raw = handle.read(MAX_FILE_BYTES + 1)
    except OSError:
        return "unreadable", None
    if len(raw) > MAX_FILE_BYTES:
        return "too-large", None
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        encodings = ("utf-16",)
    elif raw.startswith(b"\xef\xbb\xbf"):
        encodings = ("utf-8-sig",)
    else:
        encodings = ("utf-8",)
    for encoding in encodings:
        try:
            text = raw.decode(encoding)
            if "\x00" in text:
                return "binary", None
            return "ok", text
        except (UnicodeDecodeError, LookupError):
            pass
    return "binary", None


def envelope(mode=None, status="blocked", variables=(), gaps=(), refusal=None):
    return {
        "schemaVersion": SCHEMA_VERSION,
        "status": status,
        "refusal": refusal,
        "mode": mode,
        "variables": list(variables),
        "gaps": list(gaps),
        "notes": list(NOTES),
        "disclaimer": DISCLAIMER,
    }


def _file_gap(kind):
    reason = {
        "too-large": "file-too-large",
        "not-regular": "file-not-regular",
        "binary": "binary-encoding-unsupported",
    }.get(kind, kind)
    return [{"file": "env", "line": 0, "reason": reason}]


def _write_json(payload):
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    stream = sys.stdout
    reconfigure = getattr(stream, "reconfigure", None)
    if reconfigure is not None:
        try:
            reconfigure(encoding="utf-8", errors="backslashreplace")
        except (ValueError, OSError):
            pass
    stream.write(text)
    stream.flush()


def build_parser():
    parser = argparse.ArgumentParser(
        prog="env_key_status.py",
        description=(
            "Report dotenv key names and states. Values and raw lines are never "
            "printed; interpolation and multi-line values are reported as gaps."
        ),
        epilog=(
            "exit codes: 0 report produced; 1 refused or incomplete report; "
            "2 invalid arguments."
        ),
    )
    parser.add_argument("--env", required=True, metavar="PATH",
                        help="dotenv-style file explicitly authorized by the user")
    parser.add_argument("--example", metavar="PATH",
                        help="optional example file to compare keys against")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    for raw in (args.env, args.example):
        if raw is not None and _resolve_symlink(raw):
            _write_json(envelope(refusal="symlink-path-refused"))
            return 1
    env_kind, env_text = _read_regular(args.env)
    if env_kind != "ok":
        _write_json(envelope(status="incomplete", gaps=_file_gap(env_kind)))
        return 1
    example_text = None
    if args.example is not None:
        example_kind, example_text = _read_regular(args.example)
        if example_kind != "ok":
            reason = _file_gap(example_kind)[0]["reason"]
            _write_json(envelope(status="incomplete",
                                 gaps=[{"file": "example", "line": 0, "reason": reason}]))
            return 1
    payload = build_report(env_text, example_text)
    _write_json(payload)
    return 0 if payload["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
