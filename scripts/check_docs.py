#!/usr/bin/env python3
"""Check current repository documentation links; historical snapshots are excluded."""
from pathlib import Path
import re
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]


def check(root):
    documents = [root / "README.md", root / "ATTRIBUTION.md", root / "archive/README.md"]
    documents += sorted(p for p in (root / "docs").rglob("*.md") if not {"history", "reviews", "validation"} & set(p.relative_to(root / "docs").parts))
    # 技能正文与归档技能的本地链接同样要查：技能被单独安装后，坏链接只在别人机器上爆发。
    documents += sorted((root / "skills").rglob("*.md"))
    documents += sorted((root / "archive" / "skills").rglob("*.md"))
    errors = []
    for file in documents:
        text = file.read_text(encoding="utf-8-sig")
        text = re.sub(r"```.*?```", "", text, flags=re.S)
        text = re.sub(r"`[^`]*`", "", text)
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if re.match(r"[\w+.-]+:|#", target):
                continue
            target = unquote(target.partition("#")[0].strip("<>"))
            if not target:
                continue
            resolved = (file.parent / target).resolve()
            if not resolved.is_relative_to(root.resolve()) or not resolved.exists():
                errors.append(f"{file.relative_to(root)}: {target}")
    return errors, len(documents)


def main():
    errors, count = check(ROOT)
    for error in errors:
        print("BROKEN: " + error, file=sys.stderr)
    print(f"Checked {count} current documents; {len(errors)} broken local links")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
