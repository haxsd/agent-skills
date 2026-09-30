#!/usr/bin/env python3
"""Rebuild the classified index and evidence review using Python stdlib only.

This is a repository consistency audit, not a YAML parser, runtime certification,
or automatic value scorer. Human judgments live in catalog.json. No skills are
installed, moved, merged, or executed by this script.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
VALUES = {"high": "高", "medium": "中", "low": "低"}
STATES = {"active": "启用", "archived": "归档", "external": "外部"}
READINESS = {
    "runnable": "局部实测可运行", "conditional": "条件可用",
    "conflicting": "规则需改造", "incomplete": "收录/引用不完整",
    "external": "依赖外部环境",
}
ACTIONS = {
    "retain": "保留", "upgrade": "升级", "merge": "合并候选",
    "archive-proposed": "建议归档", "archive-retain": "维持归档",
    "retain-external": "保持外部",
}
TEXT_SUFFIXES = {".md", ".py", ".cjs", ".js", ".csv", ".json", ".html", ".sh"}
NORMALIZED_SUFFIXES = TEXT_SUFFIXES | {".yaml", ".yml", ".txt", ".dot", ".ts"}


def canonical_bytes(path):
    raw = path.read_bytes()
    if path.suffix in NORMALIZED_SUFFIXES or not path.suffix:
        return raw.replace(b"\r\n", b"\n")
    return raw


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def skill_dir(root, entry):
    if entry["state"] == "active":
        return root / "skills" / entry["name"]
    if entry["state"] == "archived":
        return root / "archive" / "skills" / entry["name"]
    return None


def frontmatter_fields(text):
    """Read top-level scalar fields of these entrypoints, without executing YAML."""
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
    if not match:
        raise ValueError("missing frontmatter delimiters")
    fields = {}
    for line in match.group(1).splitlines():
        field = re.match(r"^([a-zA-Z][\w-]*):\s*(.*)$", line)
        if field:
            key, value = field.groups()
            if key in fields:
                raise ValueError(f"duplicate top-level field: {key}")
            fields[key] = value
    return fields


def scalar(value):
    if value.startswith('"') and value.endswith('"'):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    return value


def inventory(root):
    found = {}
    for state, base in (("active", root / "skills"),
                        ("archived", root / "archive" / "skills")):
        for folder in sorted(base.iterdir()):
            if folder.is_dir():
                key = (state, folder.name)
                found[key] = folder
    return found


def inspect(root, catalog):
    findings = []

    def add(level, code, path, message):
        findings.append({"level": level, "code": code,
                         "path": str(path), "message": message})

    categories = {entry["id"]: entry["title"] for entry in catalog["categories"]}
    entries = catalog["skills"]
    names = [entry["name"] for entry in entries]
    if len(names) != len(set(names)):
        add("error", "duplicate-catalog-name", "catalog.json", "Skill names must be unique")
    expected = {(entry["state"], entry["name"]) for entry in entries
                if entry["state"] != "external"}
    found = inventory(root)
    for key in sorted(set(found) - expected):
        add("error", "uncatalogued-skill", found[key].relative_to(root), "Missing human review")
    for key in sorted(expected - set(found)):
        add("error", "missing-skill", key[1], f"Missing {key[0]} folder")

    manifest = read_json(root / "manifest.json")
    manifest_names = [entry["name"] for entry in manifest["skills"]]
    active_names = {name for state, name in found if state == "active"}
    if len(manifest_names) != len(set(manifest_names)) or set(manifest_names) != active_names:
        add("error", "manifest-coverage", "manifest.json", "Manifest and active folders differ")
    externals = read_json(root / "external.json")
    if {entry["name"] for entry in externals} != {
            entry["name"] for entry in entries if entry["state"] == "external"}:
        add("error", "external-coverage", "external.json", "External registrations and catalog differ")
    manifest_map = {entry["name"]: entry for entry in manifest["skills"]}
    metrics = []
    duplicate_map = defaultdict(list)
    for entry in entries:
        name = entry["name"]
        path = skill_dir(root, entry)
        if entry["category"] not in categories:
            add("error", "unknown-category", name, entry["category"])
        for field, choices in (("value", VALUES), ("state", STATES),
                               ("readiness", READINESS), ("action", ACTIONS)):
            if entry[field] not in choices:
                add("error", "invalid-enum", name, f"{field}={entry[field]}")
        for target in entry["mergeWith"]:
            if target not in names:
                add("error", "unknown-merge-target", name, target)
        resolved_evidence = []
        for evidence in entry["evidence"]:
            source = root / evidence["repoFile"] if "repoFile" in evidence else path / evidence["file"]
            if not source.is_file():
                add("error", "missing-evidence-file", name, str(source))
                continue
            text = source.read_text(encoding="utf-8-sig")
            lines = [i for i, line in enumerate(text.splitlines(), 1) if evidence["text"] in line]
            if not lines:
                add("error", "stale-evidence", source.relative_to(root), evidence["text"])
            else:
                resolved_evidence.append({"path": source.relative_to(root).as_posix(),
                                          "line": lines[0], "text": evidence["text"]})
        if path is None:
            metrics.append({"name": name, "state": entry["state"],
                            "evidence": resolved_evidence})
            continue
        entrypoint = path / "SKILL.md"
        if not entrypoint.exists():
            add("error", "missing-entrypoint", path.relative_to(root), "Missing SKILL.md")
            continue
        text = entrypoint.read_text(encoding="utf-8-sig")
        try:
            fields = frontmatter_fields(text)
        except ValueError as exc:
            add("error", "frontmatter", entrypoint.relative_to(root), str(exc))
            fields = {}
        parsed_name = scalar(fields.get("name", ""))
        if (parsed_name != name or len(name) > 64 or
                not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name)):
            add("error", "skill-name", entrypoint.relative_to(root), "Invalid or mismatched name")
        description = scalar(fields.get("description", ""))
        if not description or len(description) > 1024 or description in {"|", ">"}:
            add("error", "description", entrypoint.relative_to(root), "Invalid scalar description")
        files = sorted(p for p in path.rglob("*") if p.is_file() and
                       "__pycache__" not in p.parts and p.suffix != ".pyc")
        total_bytes = sum(len(canonical_bytes(p)) for p in files)
        row = {"name": name, "state": entry["state"],
               "path": entrypoint.relative_to(root).as_posix(),
               "lines": len(text.splitlines()), "entryBytesLF": len(text.encode("utf-8")),
               "entrySha256LF": hashlib.sha256(text.encode("utf-8")).hexdigest(),
               "files": len(files), "bytes": total_bytes,
               "scriptFiles": sum("scripts" in p.relative_to(path).parts and
                                  "tests" not in p.relative_to(path).parts for p in files),
               "testFiles": sum(p.name.startswith("test_") and p.suffix == ".py" for p in files),
               "evidence": resolved_evidence}
        metrics.append(row)
        if row["lines"] > 500:
            add("warning", "large-entrypoint", row["path"],
                f"{row['lines']} lines; use progressive disclosure")
        if entry["state"] == "active" and name in manifest_map:
            cached = manifest_map[name]
            for field, actual in (("files", len(files)), ("bytes", total_bytes),
                                  ("description", description)):
                if cached.get(field) != actual:
                    add("warning", "manifest-cache-drift", "manifest.json", f"{name}: {field}")
        for file in files:
            relative = file.relative_to(root).as_posix()
            if file.suffix in TEXT_SUFFIXES and "tests" not in file.relative_to(path).parts:
                normalized = file.read_bytes().replace(b"\r\n", b"\n")
                if normalized:
                    duplicate_map[hashlib.sha256(normalized).hexdigest()].append((name, relative))
        # These are hints, not hard failures: some paths are generated project assets.
        candidates = set(re.findall(
            r"(?<![\w/])(?:references|scripts|templates|assets|data)/[\w./-]+\.(?:md|py|cjs|js|json|csv|css|html|sh)", text))
        for ref in sorted(candidates):
            if not (path / ref).is_file() and not (root / ref).is_file():
                add("hint", "unresolved-path-in-entrypoint", row["path"], ref)
    duplicates = [sorted(path for _, path in group)
                  for group in duplicate_map.values() if len({name for name, _ in group}) > 1]
    return {"baselineCommit": catalog["baselineCommit"], "reviewedAt": catalog["reviewedAt"],
            "counts": dict(Counter(entry["state"] for entry in entries)),
            "scope": "Static consistency; paths marked hint may be generated project assets. Not full YAML validation or behavioral certification.",
            "skills": metrics, "exactDuplicateTextGroupsLF": sorted(duplicates),
            "findings": sorted(findings, key=lambda item: (item["level"], item["path"], item["code"], item["message"]))}


def cell(text):
    return text.replace("|", "\\|").replace("\n", " ")


def table_link(entry, metric):
    if "path" in metric:
        return f"[{entry['name']}](../{metric['path']})"
    return f"{entry['name']}（外部）"


def render_catalog(catalog, audit):
    metrics = {row["name"]: row for row in audit["skills"]}
    out = ["# Skills 分类目录", "", "由 `catalog.json` 和 `scripts/audit_skills.py` 生成。", "",
           f"审查日期：{catalog['reviewedAt']}。27 个启用 + 5 个归档 + 1 个外部入口。", "",
           "分类是逻辑索引，保留平铺目录，兼容现有安装器。状态描述仓库当前布局，动作是审查建议，不会自动移动/卸载。",
           "价值高/中/低来自内容审查，不能解读为实测收益；条件可用也不代表所有流程通过了运行验证。", "",
           "安装目标仍只由 `manifest.json` / `external.json` 决定；不要从本目录生成第二套目标配置。", "",
           "详见 [逐项审查](skill-review.md)、[整改路线](review-roadmap.md)、[机器检查结果](audit-findings.json)。", ""]
    for category in catalog["categories"]:
        out.extend([f"## {category['title']}", "",
                    "| Skill | 当前状态 | 内容价值 | 当前就绪程度 | 建议 | 优先级 |",
                    "|---|---|---|---|---|---|"])
        for entry in catalog["skills"]:
            if entry["category"] == category["id"]:
                out.append("| " + " | ".join([
                    table_link(entry, metrics[entry["name"]]), STATES[entry["state"]],
                    VALUES[entry["value"]], READINESS[entry["readiness"]],
                    ACTIONS[entry["action"]], entry["priority"]]) + " |")
        out.append("")
    out.extend(["## 如何维护", "", "1. 新增/移走技能时更新 `catalog.json` 与安装 manifest。",
                "2. 每项补真实用途、问题、改进、可观察验收场景和可定位的来源证据。",
                "3. 运行 `python scripts/audit_skills.py --write` 更新派生文档，再运行 `--check` 校验一致性。",
                "4. 安装只用现有 `install.ps1`；本轮仅执行 DryRun，没有接管本机技能目录。", ""])
    return "\n".join(out)


def render_review(catalog, audit):
    metrics = {row["name"]: row for row in audit["skills"]}
    categories = {row["id"]: row["title"] for row in catalog["categories"]}
    out = ["# 逐项价值与升级审查", "", f"审查日期：{catalog['reviewedAt']}。基线提交：`{catalog['baselineCommit']}`。", "",
           "27 个启用和 5 个归档 SKILL.md 已逐一通读；关键脚本、参考和现有测试按风险抽查，未穷尽执行所有资源。",
           "toolkit-map 仅评估外部接入，未把独立仓库当成本仓库已审完的内容。合并判断基于职责、输入输出和实质内容，不以同名或文字相似率定论。", "",
           "**评分尺度**：高＝有非显然方法、可复用工具/数据或可验证操作约束；中＝有帮助但偏通用、依赖环境或流程偏重；低＝缺少独立产出、被现有入口覆盖或主要重复宿主规则。",
           "**证据边界**：静态问题可由链接定位；运行结论仅覆盖 [整改路线里的实测记录](review-roadmap.md)。没有做真实用户任务的全量 A/B，价值评级属于专业判断。", ""]
    for i, entry in enumerate(catalog["skills"], 1):
        metric = metrics[entry["name"]]
        out.extend([f"## {i:02d}. {entry['name']}", "",
                    f"{categories[entry['category']]} · {STATES[entry['state']]} · 价值：{VALUES[entry['value']]} · {READINESS[entry['readiness']]} · {entry['priority']} · {ACTIONS[entry['action']]}", "",
                    entry["summary"], "", f"**真正的增益**：{entry['uniqueValue']}", ""])
        if "lines" in metric:
            out.extend([f"**体量**：入口 {metric['lines']} 行 / {metric['entryBytesLF']:,} 字节（LF）；整个目录 {metric['files']} 个文件 / {metric['bytes']:,} 规范化字节；生产 scripts 文件 {metric['scriptFiles']}，Python 测试文件 {metric['testFiles']}。文本统一 LF，二进制原样计数，字节数不等于 token 数。", ""])
        out.extend(["**问题与限制**", "", *[f"- {problem}" for problem in entry["issues"]], "",
                    "**优化方案**", "", *[f"- {idea}" for idea in entry["improvements"]], ""])
        if entry["mergeWith"]:
            out.extend(["**关联/合并候选**：" + "、".join(f"`{name}`" for name in entry["mergeWith"]) + "。此字段也包含只迁出重叠模块的关系，不代表整个技能都要合并。", ""])
        out.extend(["**升级后的验收场景（尚未全量执行）**", "", *[f"- {case}" for case in entry["scenarios"]], "",
                    "**来源定位**", ""])
        for evidence in metric["evidence"]:
            out.append(f"- [{evidence['path']}:{evidence['line']}](../{evidence['path']}#L{evidence['line']})：`{evidence['text']}`")
        out.append("")
    out.extend(["## 完全重复的文本资源", "",
                "下表按 LF 规范化后 SHA-256 分组，只收录跨 skill 的相同文本，排除测试 fixtures。完全相同只证明这些资源可统一来源，不证明两个技能整体等价。", ""])
    if audit["exactDuplicateTextGroupsLF"]:
        for group in audit["exactDuplicateTextGroupsLF"]:
            out.append("- " + "；".join(f"[{path}](../{path})" for path in group))
    else:
        out.append("未发现符合该范围的完全重复资源；职责重叠仍见逐项审查。")
    out.append("")
    return "\n".join(out)


def outputs(catalog, audit):
    return {
        "docs/catalog.md": render_catalog(catalog, audit),
        "docs/skill-review.md": render_review(catalog, audit),
        "docs/audit-findings.json": json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="Rebuild derived documents")
    mode.add_argument("--check", action="store_true", help="Fail if derived documents are missing or stale")
    args = parser.parse_args()
    try:
        catalog = read_json(ROOT / "catalog.json")
        audit = inspect(ROOT, catalog)
    except (ValueError, KeyError, OSError, TypeError) as exc:
        print(f"Audit failed: {exc}", file=sys.stderr)
        return 1
    counts = Counter(item["level"] for item in audit["findings"])
    print(f"Skills: {audit['counts']}; errors={counts['error']}, warnings={counts['warning']}, hints={counts['hint']}")
    if counts["error"]:
        for item in audit["findings"]:
            if item["level"] == "error":
                print(f"ERROR [{item['code']}] {item['path']}: {item['message']}")
        return 1
    stale = []
    for relative, content in outputs(catalog, audit).items():
        path = ROOT / relative
        if args.write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
        elif args.check and (not path.exists() or path.read_text(encoding="utf-8") != content):
            stale.append(relative)
    if stale:
        print("Stale derived files: " + ", ".join(stale))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
