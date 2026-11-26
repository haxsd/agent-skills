#!/usr/bin/env python3
"""Check current repository documentation links and the counts stated in the entry docs."""
from collections import Counter
from pathlib import Path
import json
import re
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]

# 入口文档里手写的数量声明：README 不在 audit 的生成范围，改技能数后不会自己更新。
COUNT_CLAIMS = {
    "active": (r"(\d+)\s*个启用技能", r"(\d+)\s*active skills"),
    "archived": (r"(\d+)\s*个归档技能", r"(\d+)\s*archived skills"),
    "external": (r"(\d+)\s*个外部入口", r"(\d+)\s*external entries"),
    "categories": (r"(\d+)\s*个用途分类", r"(\d+)\s*categories"),
}


def declared_counts(root):
    catalog = json.loads((root / "catalog.json").read_text(encoding="utf-8-sig"))
    states = Counter(entry["state"] for entry in catalog["skills"])
    return {
        "active": states["active"],
        "archived": states["archived"],
        "external": states["external"],
        "categories": len(catalog["categories"]),
    }


def check_counts(root):
    expected = declared_counts(root)
    errors = []
    for name in ("README.md", "README-EN.md", "docs/README.md"):
        file = root / name
        if not file.is_file():
            continue
        for number, line in enumerate(file.read_text(encoding="utf-8-sig").splitlines(), 1):
            for key, patterns in COUNT_CLAIMS.items():
                for pattern in patterns:
                    for claimed in re.findall(pattern, line):
                        if int(claimed) != expected[key]:
                            errors.append(
                                f"{name}:{number}: 写着 {claimed} {key}，实际 {expected[key]}")
    return errors


def check(root):
    documents = [root / "README.md", root / "README-EN.md", root / "ATTRIBUTION.md", root / "archive/README.md"]
    documents += sorted(p for p in (root / "docs").rglob("*.md") if not {"history", "reviews", "validation"} & set(p.relative_to(root / "docs").parts))
    # 技能正文与归档技能的本地链接同样要查：技能被单独安装后，坏链接只在别人机器上爆发。
    documents += sorted((root / "skills").rglob("*.md"))
    documents += sorted((root / "archive" / "skills").rglob("*.md"))
    documents = [path for path in documents if path.is_file()]
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
    links, count = check(ROOT)
    stale = check_counts(ROOT)
    for error in links:
        print("BROKEN: " + error, file=sys.stderr)
    for error in stale:
        print("STALE: " + error, file=sys.stderr)
    print(f"Checked {count} current documents; {len(links)} broken local links, {len(stale)} stale counts")
    return bool(links or stale)


if __name__ == "__main__":
    raise SystemExit(main())
