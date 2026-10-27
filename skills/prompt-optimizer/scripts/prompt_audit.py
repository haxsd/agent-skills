#!/usr/bin/env python3
"""Heuristic, offline checks for prompt packages and recorded prompt evals."""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

MAX_PROMPT_BYTES = 2_000_000
MAX_JSON_BYTES = 8_000_000
CASE_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FINGERPRINT_RE = re.compile(r"^[0-9a-f]{64}$")
CHECK_TYPES = {"contains", "not_contains", "regex", "json_schema", "manual"}
SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{15,}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)
PRIVATE_PATH_PATTERNS = (
    re.compile(r"\b[A-Za-z]:\\Users\\[^\\\s]+", re.IGNORECASE),
    re.compile(r"(?<!\w)/home/[^/\s]+"),
)
CONTRADICTIONS = (
    ("clarification", re.compile(r"\balways ask\b", re.I),
     re.compile(r"\b(?:never ask|do not ask)\b", re.I)),
    ("verbosity", re.compile(r"\b(?:be|keep it) (?:very )?concise\b", re.I),
     re.compile(r"\b(?:provide|give) (?:very |extremely )?detailed\b", re.I)),
    ("tool-use", re.compile(r"\balways use (?:a )?tools?\b", re.I),
     re.compile(r"\b(?:never use|do not use) (?:a )?tools?\b", re.I)),
)
CHAIN_OF_THOUGHT_RE = re.compile(
    r"\b(?:think step[- ]by[- ]step|chain[- ]of[- ]thought|"
    r"show (?:all )?(?:your )?(?:internal |hidden )?reasoning)\b",
    re.I,
)


class AuditError(ValueError):
    pass


def _read_text(path):
    try:
        if path.stat().st_size > MAX_PROMPT_BYTES:
            raise AuditError(f"{path}: prompt exceeds {MAX_PROMPT_BYTES} bytes")
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        raise AuditError(f"{path}: unreadable prompt: {exc}") from exc


def _load_json(path):
    try:
        if path.stat().st_size > MAX_JSON_BYTES:
            raise AuditError(f"{path}: JSON exceeds {MAX_JSON_BYTES} bytes")
        return json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=lambda value: (_ for _ in ()).throw(
                ValueError(f"non-RFC numeric constant: {value}")
            ),
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise AuditError(f"{path}: invalid JSON: {exc}") from exc


def _line_number(text, offset):
    return text.count("\n", 0, offset) + 1


def _without_code(text):
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    return re.sub(r"`[^`\n]*`", "", text)


def lint_text(text):
    findings = []

    def add(level, code, message, line=None):
        finding = {"level": level, "code": code, "message": message}
        if line is not None:
            finding["line"] = line
        findings.append(finding)

    if not text.strip():
        add("error", "empty-prompt", "Prompt is empty.")
        return findings

    if text.count("```") % 2:
        add("warning", "unbalanced-code-fence", "Fenced code blocks are not balanced.")

    for pattern in SECRET_PATTERNS:
        match = pattern.search(text)
        if match:
            add(
                "error",
                "secret-like-value",
                "Prompt contains a secret-like value; replace it with a placeholder. "
                "The matched value is intentionally not echoed.",
                _line_number(text, match.start()),
            )
            break

    for pattern in PRIVATE_PATH_PATTERNS:
        match = pattern.search(text)
        if match:
            add(
                "warning",
                "private-user-path",
                "Prompt contains an absolute user path; use a declared input variable.",
                _line_number(text, match.start()),
            )
            break

    control = re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\u202a-\u202e\u2066-\u2069]", text)
    if control:
        add(
            "error",
            "unsafe-control-character",
            "Prompt contains a control or bidirectional override character.",
            _line_number(text, control.start()),
        )

    for name, left, right in CONTRADICTIONS:
        if left.search(text) and right.search(text):
            add(
                "warning",
                "possible-contradiction",
                f"Prompt appears to contain conflicting {name} rules; verify precedence.",
            )

    reasoning = CHAIN_OF_THOUGHT_RE.search(text)
    if reasoning:
        add(
            "warning",
            "reasoning-request",
            "Ask for a concise evidence summary instead of hidden chain-of-thought.",
            _line_number(text, reasoning.start()),
        )

    prose = _without_code(text)
    double = set(re.findall(r"\{\{\s*([A-Za-z_][\w.-]*)\s*\}\}", prose))
    single = set(re.findall(r"(?<!\{)\{\s*([A-Za-z_][\w.-]*)\s*\}(?!\})", prose))
    mixed = sorted(double & single)
    if mixed:
        add(
            "warning",
            "mixed-placeholder-style",
            "The same placeholder uses both {{name}} and {name} forms: "
            + ", ".join(mixed[:5]),
        )
    if prose.count("{") != prose.count("}"):
        add("warning", "unbalanced-placeholder-braces", "Placeholder braces are unbalanced.")

    paragraphs = {}
    for paragraph in re.split(r"\n\s*\n", prose):
        normalized = re.sub(r"\s+", " ", paragraph).strip()
        if len(normalized) < 80:
            continue
        paragraphs.setdefault(normalized, 0)
        paragraphs[normalized] += 1
    if any(count > 1 for count in paragraphs.values()):
        add("warning", "duplicate-paragraph", "Prompt repeats a long paragraph verbatim.")

    if len(text) > 1500 and not re.search(r"(?m)^(?:#{1,6}\s|<[A-Za-z][\w-]*>)", text):
        add(
            "hint",
            "no-section-boundaries",
            "Long prompt has no headings or delimiters; check whether content types are mixed.",
        )

    return sorted(
        findings,
        key=lambda item: (
            {"error": 0, "warning": 1, "hint": 2}[item["level"]],
            item.get("line", 0),
            item["code"],
        ),
    )


def lint_prompt(path):
    text = _read_text(path)
    findings = lint_text(text)
    counts = {
        level: sum(item["level"] == level for item in findings)
        for level in ("error", "warning", "hint")
    }
    return {
        "schemaVersion": 1,
        "tool": "prompt_audit.lint.v1",
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "findings": findings,
        "counts": counts,
        "scope": "Heuristic static checks only; no model behavior or secret-exhaustiveness claim.",
    }


def _secret_in_value(value):
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return any(pattern.search(serialized) for pattern in SECRET_PATTERNS)


def validate_eval_fixture(payload, prompt_text=None):
    errors, warnings = [], []
    if not isinstance(payload, dict):
        return {"errors": ["Fixture must be a JSON object."], "warnings": [], "summary": {}}
    if payload.get("schemaVersion") != 1:
        errors.append("schemaVersion must be 1.")
    target = payload.get("target")
    if not isinstance(target, dict) or not isinstance(target.get("surface"), str) or not target["surface"].strip():
        errors.append("target.surface must describe the prompt surface under test.")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not 5 <= len(cases) <= 50:
        errors.append("cases must contain 5-50 items.")
        cases = cases if isinstance(cases, list) else []
    prompt_hash = payload.get("promptSha256")
    if prompt_hash is not None and (
        not isinstance(prompt_hash, str) or not FINGERPRINT_RE.fullmatch(prompt_hash)
    ):
        errors.append("promptSha256 must be a lowercase SHA-256 digest.")
    if prompt_text is not None:
        actual = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()
        if prompt_hash is None:
            errors.append("promptSha256 is required when --prompt is supplied.")
        elif prompt_hash != actual:
            errors.append("promptSha256 does not match the supplied prompt.")
    seen_ids, seen_inputs = set(), set()
    splits = {"dev": 0, "held_out": 0}
    for index, case in enumerate(cases):
        label = f"cases[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{label} must be an object.")
            continue
        case_id = case.get("id")
        if not isinstance(case_id, str) or not CASE_ID_RE.fullmatch(case_id):
            errors.append(f"{label}.id must be a lowercase slug.")
        elif case_id in seen_ids:
            errors.append(f"duplicate case id: {case_id}")
        else:
            seen_ids.add(case_id)
        split = case.get("split")
        if split not in splits:
            errors.append(f"{label}.split must be dev or held_out.")
        else:
            splits[split] += 1
        input_text = case.get("input")
        if not isinstance(input_text, str) or not input_text.strip() or len(input_text) > 20_000:
            errors.append(f"{label}.input must be a non-empty string up to 20000 characters.")
        else:
            normalized = re.sub(r"\s+", " ", input_text).strip()
            if normalized in seen_inputs:
                warnings.append(f"{label}: duplicate input adds little coverage.")
            seen_inputs.add(normalized)
        checks = case.get("checks")
        if not isinstance(checks, list) or not 1 <= len(checks) <= 12:
            errors.append(f"{label}.checks must contain 1-12 checks.")
            checks = []
        for check_index, check in enumerate(checks):
            check_label = f"{label}.checks[{check_index}]"
            if not isinstance(check, dict):
                errors.append(f"{check_label} must be an object.")
                continue
            kind = check.get("type")
            if kind not in CHECK_TYPES:
                errors.append(f"{check_label}.type is unsupported.")
                continue
            if kind in {"contains", "not_contains"}:
                value = check.get("value")
                if not isinstance(value, str) or not value.strip() or len(value) > 2000:
                    errors.append(f"{check_label}.value must be a non-empty string.")
            elif kind == "regex":
                pattern = check.get("value")
                if not isinstance(pattern, str) or len(pattern) > 500:
                    errors.append(f"{check_label}.value must be a regex string up to 500 characters.")
                else:
                    try:
                        re.compile(pattern)
                    except re.error as exc:
                        errors.append(f"{check_label}.value is not a valid regex: {exc}")
            elif kind == "json_schema":
                if not isinstance(check.get("value"), dict):
                    errors.append(f"{check_label}.value must be a JSON schema object.")
            elif kind == "manual":
                rubric = check.get("rubric")
                if not isinstance(rubric, str) or not rubric.strip():
                    errors.append(f"{check_label}.rubric is required for manual checks.")
        weight = case.get("weight", 1)
        if isinstance(weight, bool) or not isinstance(weight, int) or not 1 <= weight <= 10:
            errors.append(f"{label}.weight must be an integer from 1 to 10.")
        if "blocking" in case and not isinstance(case["blocking"], bool):
            errors.append(f"{label}.blocking must be boolean.")
        maximum = case.get("max_output_chars")
        if maximum is not None and (
            isinstance(maximum, bool) or not isinstance(maximum, int) or not 1 <= maximum <= 100_000
        ):
            errors.append(f"{label}.max_output_chars must be an integer from 1 to 100000.")
        if _secret_in_value(case):
            errors.append(f"{label}: secret-like value detected; use synthetic placeholders.")
    if splits["dev"] == 0:
        errors.append("At least one dev case is required.")
    if splits["held_out"] == 0:
        errors.append("At least one frozen held_out case is required.")
    return {
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "cases": len(cases),
            "dev": splits["dev"],
            "heldOut": splits["held_out"],
        },
    }


def _validate_run(payload, label):
    errors = []
    if not isinstance(payload, dict) or payload.get("schemaVersion") != 1:
        return None, [f"{label}: schemaVersion 1 object is required."]
    cases = payload.get("cases")
    if not isinstance(cases, list) or not 1 <= len(cases) <= 500:
        return None, [f"{label}.cases must contain 1-500 results."]
    for field in ("promptSha256", "evalSha256"):
        value = payload.get(field)
        if value is not None and (
            not isinstance(value, str) or not FINGERPRINT_RE.fullmatch(value)
        ):
            errors.append(f"{label}.{field} must be a lowercase SHA-256 digest.")
    normalized = []
    seen = set()
    for index, case in enumerate(cases):
        item_label = f"{label}.cases[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{item_label} must be an object.")
            continue
        case_id = case.get("id")
        if not isinstance(case_id, str) or not CASE_ID_RE.fullmatch(case_id):
            errors.append(f"{item_label}.id must be a lowercase slug.")
            continue
        if case_id in seen:
            errors.append(f"{label}: duplicate result id {case_id}.")
        seen.add(case_id)
        if not isinstance(case.get("passed"), bool):
            errors.append(f"{item_label}.passed must be boolean.")
        weight = case.get("weight", 1)
        if isinstance(weight, bool) or not isinstance(weight, int) or not 1 <= weight <= 10:
            errors.append(f"{item_label}.weight must be an integer from 1 to 10.")
        if "blocking" in case and not isinstance(case["blocking"], bool):
            errors.append(f"{item_label}.blocking must be boolean.")
        score = case.get("score")
        if score is not None and (
            isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 1
        ):
            errors.append(f"{item_label}.score must be a number from 0 to 1.")
        normalized.append(case)
    return normalized, errors


def compare_runs(baseline, candidate):
    baseline_cases, baseline_errors = _validate_run(baseline, "baseline")
    candidate_cases, candidate_errors = _validate_run(candidate, "candidate")
    errors = baseline_errors + candidate_errors
    if errors or baseline_cases is None or candidate_cases is None:
        return {
            "errors": errors or ["Run data is incomplete."],
            "verdict": "invalid",
            "note": "Fix run records before comparing outcomes.",
        }
    base = {case["id"]: case for case in baseline_cases}
    cand = {case["id"]: case for case in candidate_cases}
    if set(base) != set(cand):
        missing = sorted(set(base) - set(cand))
        extra = sorted(set(cand) - set(base))
        errors.append(f"Result ids differ; missing={missing[:5]} extra={extra[:5]}.")
    if baseline.get("evalSha256") and candidate.get("evalSha256") and (
        baseline["evalSha256"] != candidate["evalSha256"]
    ):
        errors.append("Runs use different eval fixtures (evalSha256 mismatch).")
    if baseline.get("model") and candidate.get("model") and baseline["model"] != candidate["model"]:
        errors.append("Runs use different model metadata; comparison is not controlled.")
    regressions, improvements = [], []
    for case_id in sorted(set(base) & set(cand)):
        before, after = base[case_id], cand[case_id]
        record = {
            "id": case_id,
            "weight": after.get("weight", before.get("weight", 1)),
            "blocking": bool(after.get("blocking", before.get("blocking", False))),
        }
        if before["passed"] and not after["passed"]:
            regressions.append(record)
        elif not before["passed"] and after["passed"]:
            improvements.append(record)

    def pass_rate(cases):
        total = sum(case.get("weight", 1) for case in cases)
        passed = sum(case.get("weight", 1) for case in cases if case["passed"])
        return passed / total if total else 0.0

    def mean_score(cases):
        scores = [case["score"] for case in cases if case.get("score") is not None]
        return sum(scores) / len(scores) if scores else None

    blocking_regressions = [item for item in regressions if item["blocking"]]
    if blocking_regressions:
        verdict = "blocked"
    elif regressions:
        verdict = "regressed"
    elif improvements:
        verdict = "improved"
    else:
        verdict = "unchanged"
    if errors:
        verdict = "invalid"
    return {
        "baseline": {
            "weightedPassRate": pass_rate(baseline_cases),
            "meanScore": mean_score(baseline_cases),
        },
        "candidate": {
            "weightedPassRate": pass_rate(candidate_cases),
            "meanScore": mean_score(candidate_cases),
        },
        "regressions": regressions,
        "improvements": improvements,
        "blockingRegressions": blocking_regressions,
        "errors": errors,
        "verdict": verdict,
        "note": "Recorded outcomes are evidence, not proof of general model behavior.",
    }


def _write(payload):
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    lint = commands.add_parser("lint", help="Run static prompt heuristics.")
    lint.add_argument("prompt", type=Path)
    lint.add_argument(
        "--fail-on", choices=("error", "warning", "none"), default="error"
    )
    validate = commands.add_parser("validate-evals", help="Validate an eval fixture.")
    validate.add_argument("fixture", type=Path)
    validate.add_argument("--prompt", type=Path)
    compare = commands.add_parser("compare", help="Compare two recorded runs.")
    compare.add_argument("baseline", type=Path)
    compare.add_argument("candidate", type=Path)
    compare.add_argument("--fail-on-regression", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "lint":
            text = _read_text(args.prompt)
            result = lint_prompt(args.prompt)
            result["prompt"] = str(args.prompt)
            _write(result)
            levels = {"error": {"error"}, "warning": {"error", "warning"}, "none": set()}[args.fail_on]
            return int(any(item["level"] in levels for item in result["findings"]))
        if args.command == "validate-evals":
            prompt_text = _read_text(args.prompt) if args.prompt else None
            result = validate_eval_fixture(_load_json(args.fixture), prompt_text)
            _write(result)
            return int(bool(result["errors"]))
        result = compare_runs(_load_json(args.baseline), _load_json(args.candidate))
        _write(result)
        if result["verdict"] == "invalid":
            return 2
        if args.fail_on_regression and result["verdict"] in {"blocked", "regressed"}:
            return 1
        return 0
    except AuditError as exc:
        _write({"schemaVersion": 1, "error": str(exc)})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
