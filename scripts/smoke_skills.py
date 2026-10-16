#!/usr/bin/env python3
"""Offline smoke checks for shipped data and tools, with isolated outputs.

Pass an absolute Node executable. No package installation, API calls, skill
installation, or modification to existing user projects occurs here.
"""

import argparse
import ast
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--node", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.node.is_absolute() or not args.node.is_file():
        parser.error("--node must be an existing absolute executable path")
    env = dict(os.environ, PYTHONUTF8="1")
    results = []

    def record(name, action):
        try:
            evidence = action()
            results.append({"name": name, "status": "pass", "evidence": evidence})
        except (AssertionError, OSError, ValueError, subprocess.SubprocessError) as exc:
            results.append({"name": name, "status": "fail", "evidence": str(exc)[:2000]})

    def run(command, cwd=ROOT, expected=0):
        result = subprocess.run(list(map(str, command)), cwd=cwd, env=env,
                                text=True, encoding="utf-8", capture_output=True, timeout=30)
        if result.returncode != expected:
            raise AssertionError(f"exit={result.returncode}, expected={expected}: " +
                                 (result.stdout + result.stderr)[-1500:])
        return result.stdout

    def syntax():
        # 归档技能的脚本同样要能解析：归档不安装，但会被人翻出来复制使用。
        paths = sorted((ROOT / "skills").rglob("*.py")) + sorted((ROOT / "archive").rglob("*.py"))
        for path in paths:
            ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path.relative_to(ROOT)))
        return {"pythonFilesParsed": len(paths), "scope": "syntax only; imports and external APIs not exercised"}

    record("Python syntax", syntax)

    def data_validation():
        output = run([sys.executable, ROOT / "skills/ui-ux-pro-max/scripts/validate_data.py"])
        if "OK: validated" not in output:
            raise AssertionError("validator did not confirm dataset validation")
        return output.strip()

    record("UI/UX data contracts", data_validation)

    def ux_query():
        output = run([sys.executable, ROOT / "skills/ui-ux-pro-max/scripts/search.py",
                      "keyboard focus modal", "--domain", "ux", "--json"])
        result = json.loads(output)
        if result.get("domain") != "ux" or not result.get("results"):
            raise AssertionError("wrong domain or empty search")
        return {"domain": result["domain"], "resultCount": len(result["results"]),
                "scope": "non-empty focused query; not an independent relevance benchmark"}

    record("UI/UX focused search", ux_query)

    def local_query(relative, query, domain):
        output = run([sys.executable, ROOT / relative, query, "--domain", domain, "--json"])
        result = json.loads(output)
        if not result.get("results"):
            raise AssertionError("empty local search")
        return {"domain": result.get("domain"), "resultCount": len(result["results"])}

    record("Logo offline search", lambda: local_query(
        "skills/design/scripts/logo/search.py", "minimalist tech", "style"))
    record("CIP offline search", lambda: local_query(
        "skills/design/scripts/cip/search.py", "business card", "deliverable"))
    record("Slides offline search", lambda: local_query(
        "skills/design-system/scripts/search-slides.py", "investor pitch", "strategy"))

    with tempfile.TemporaryDirectory(prefix="agent-skills-smoke-") as raw:
        project = Path(raw)
        (project / "docs").mkdir()
        (project / "assets").mkdir()

        def brand_sync():
            shutil.copyfile(ROOT / "skills/brand/templates/brand-guidelines-starter.md",
                            project / "docs/brand-guidelines.md")
            shutil.copyfile(ROOT / "skills/design-system/templates/design-tokens-starter.json",
                            project / "assets/design-tokens.json")
            run([args.node, ROOT / "skills/brand/scripts/sync-brand-to-tokens.cjs"], cwd=project)
            tokens = json.loads((project / "assets/design-tokens.json").read_text(encoding="utf-8"))
            for key, expected in (("primary", "#2563EB"), ("secondary", "#8B5CF6"), ("accent", "#10B981")):
                actual = tokens["primitive"]["color"][key]["500"]["$value"]
                if actual != expected:
                    raise AssertionError(f"{key}: {actual} != {expected}")
            return "Starter template synced with expected primary/secondary/accent colors"

        record("Brand template sync", brand_sync)

        def tokens_generation():
            target = project / "assets/generated-tokens.css"
            run([args.node, ROOT / "skills/design-system/scripts/generate-tokens.cjs",
                 "--config", ROOT / "skills/design-system/templates/design-tokens-starter.json",
                 "--output", target], cwd=project)
            css = target.read_text(encoding="utf-8")
            if "--" not in css or "{primitive." in css:
                raise AssertionError("missing CSS variables or unresolved primitive aliases")
            return {"cssBytes": target.stat().st_size, "scope": "bundled starter; not cycles/missing aliases"}

        record("Token CSS generation", tokens_generation)

        def tokens_validation():
            source = project / "src"
            source.mkdir()
            css = source / "sample.css"
            css.write_text(".btn { background: #FF6B6B; color: var(--color-primary); }\n", encoding="utf-8")
            output = run([args.node, ROOT / "skills/design-system/scripts/validate-tokens.cjs",
                          "--dir", source], expected=1)
            if "#FF6B6B" not in output:
                raise AssertionError("missed a hardcoded value sharing a line with a token")
            css.write_text(".btn { background: var(--color-bg); color: var(--color-primary); }\n", encoding="utf-8")
            output = run([args.node, ROOT / "skills/design-system/scripts/validate-tokens.cjs", "--dir", source])
            if "No token violations" not in output:
                raise AssertionError("token-only CSS was not accepted")
            return "Mixed hardcoded/token line rejected; token-only line accepted"

        record("Token validator regression", tokens_validation)

        def tailwind_generation():
            target = project / "tailwind.config.js"
            run([sys.executable, ROOT / "skills/ui-styling/scripts/tailwind_config_gen.py",
                 "--js", "--colors", "brand:#3b82f6", "--output", target], cwd=project)
            run([args.node, "--check", target], cwd=project)
            text = target.read_text(encoding="utf-8")
            if "#3b82f6" not in text:
                raise AssertionError("requested brand color missing")
            return "JS config generated with requested brand color and passes Node syntax check; no Tailwind build performed"

        record("Tailwind config generation", tailwind_generation)

    report = {"reviewedAt": "2026-09-30", "pythonVersion": sys.version.split()[0],
              "nodeVersion": run([args.node, "--version"]).strip(),
              "scope": "Offline smoke checks only; all generated project files are temporary. No external API or agent behavioral benchmark.",
              "results": results}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                               encoding="utf-8", newline="\n")
    for row in results:
        print(f"{row['status'].upper()}: {row['name']}")
        if row["status"] != "pass":
            print(row["evidence"])
    return int(any(row["status"] != "pass" for row in results))


if __name__ == "__main__":
    sys.exit(main())
