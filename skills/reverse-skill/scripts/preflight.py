#!/usr/bin/env python3
"""Read-only preflight for an external reverse-skill package."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys


RULE_FILES = ("RULES_zh.md", "RULES.md")
REQUIRED_FILES = (
    "skills/MASTER-ROUTING.md",
    "skills/scripts/master-route.ps1",
    "skills/scripts/case-init.ps1",
    "skills/case-review/scripts/review_case.py",
)
OPTIONAL_FILES = (
    "skills/tool-index.md",
    "skills/scripts/refresh-tool-index.ps1",
    "skills/scripts/bootstrap-reverse.ps1",
    "skills/field-journal",
)


def readable_file(root, relative):
    path = root / relative
    return path.is_file() and os.access(path, os.R_OK)


def inspect_root(raw_root):
    root = Path(raw_root).expanduser().resolve()
    report = {
        "ok": False,
        "root": str(root),
        "ruleFiles": [],
        "missingRequired": [],
        "optional": {},
    }
    if not root.is_dir():
        report["error"] = "root directory does not exist"
        return report
    rules = [name for name in RULE_FILES if readable_file(root, name)]
    report["ruleFiles"] = rules
    if not rules:
        report["missingRequired"].append("RULES_zh.md or RULES.md")
    for relative in REQUIRED_FILES:
        if not readable_file(root, relative):
            report["missingRequired"].append(relative)
    for relative in OPTIONAL_FILES:
        report["optional"][relative] = (
            (root / relative).exists()
            if relative.endswith("field-journal")
            else readable_file(root, relative)
        )
    report["ok"] = not report["missingRequired"]
    return report


def candidate_roots(explicit=None):
    candidates = []
    sources = []
    if explicit:
        candidates.append(Path(explicit))
        sources.append("explicit")
    elif os.environ.get("REVERSE_SKILL_ROOT"):
        candidates.append(Path(os.environ["REVERSE_SKILL_ROOT"]))
        sources.append("REVERSE_SKILL_ROOT")
    candidates.append(Path.home() / "tools" / "reverse-skill")
    sources.append("default")
    unique = []
    seen = set()
    for source, candidate in zip(sources, candidates):
        resolved = candidate.expanduser().resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append((source, resolved))
    return unique


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Check an external reverse-skill package without modifying it."
    )
    parser.add_argument("--root", help="explicit external skill-pack root")
    args = parser.parse_args(argv)
    if args.root:
        report = inspect_root(args.root)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["ok"] else 2
    tested = []
    for source, root in candidate_roots():
        report = inspect_root(root)
        report["source"] = source
        tested.append(report)
        if report["ok"]:
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0
    print(
        json.dumps(
            {
                "ok": False,
                "error": "external reverse-skill package was not found or is incomplete",
                "tested": tested,
                "next": "Set REVERSE_SKILL_ROOT or pass --root with the installed package directory.",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
