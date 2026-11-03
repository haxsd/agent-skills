#!/usr/bin/env python3
"""Summarize agent/LLM eval results, compare with a baseline, and calibrate judges.

Standard library only. Input is JSON Lines, one record per trial:
  {"case": "c1", "bucket": "tool-choice", "pass": true}
Optional fields: "trial" (int), "error" (str, marks an invalid run that is not scored).

  summary   eval_report.py summary results.jsonl
  compare   eval_report.py compare baseline.jsonl candidate.jsonl [--tolerance 0.05] [--fail-on-regression]
  judge     eval_report.py judge labels.jsonl   (records: {"human": true, "judge": false})
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

Z95 = 1.959963984540054


def load(path: str) -> list[dict]:
    rows = []
    with Path(path).open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{lineno}: invalid JSON: {exc}") from exc
            rows.append(row)
    return rows


def wilson(passed: int, total: int) -> tuple[float, float]:
    if total == 0:
        return (0.0, 0.0)
    p = passed / total
    denom = 1 + Z95**2 / total
    centre = p + Z95**2 / (2 * total)
    margin = Z95 * math.sqrt(p * (1 - p) / total + Z95**2 / (4 * total**2))
    return (max(0.0, (centre - margin) / denom), min(1.0, (centre + margin) / denom))


def aggregate(rows: list[dict]) -> dict:
    buckets: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    cases: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    invalid = 0
    for row in rows:
        if row.get("error"):
            invalid += 1
            continue
        if "pass" not in row or "case" not in row:
            raise SystemExit(f"record missing 'case' or 'pass': {row}")
        ok = 1 if row["pass"] else 0
        bucket = str(row.get("bucket", "all"))
        for key, table in ((bucket, buckets), ("__all__", buckets), (str(row["case"]), cases)):
            table[key][0] += ok
            table[key][1] += 1
    return {"buckets": dict(buckets), "cases": dict(cases), "invalid": invalid}


def bucket_lines(agg: dict) -> list[dict]:
    out = []
    for name, (passed, total) in sorted(agg["buckets"].items(), key=lambda kv: (kv[0] != "__all__", kv[0])):
        lo, hi = wilson(passed, total)
        out.append({"bucket": "ALL" if name == "__all__" else name, "passed": passed, "total": total,
                    "rate": passed / total if total else 0.0, "ci95": [round(lo, 3), round(hi, 3)]})
    return out


def cmd_summary(args) -> int:
    agg = aggregate(load(args.results))
    result = {"buckets": bucket_lines(agg), "invalid_runs": agg["invalid"]}
    emit(result, args.json)
    return 0


def cmd_compare(args) -> int:
    base, cand = aggregate(load(args.baseline)), aggregate(load(args.candidate))
    rows, regressed = [], False
    names = sorted(set(base["buckets"]) | set(cand["buckets"]), key=lambda n: (n != "__all__", n))
    for name in names:
        bp, bt = base["buckets"].get(name, [0, 0])
        cp, ct = cand["buckets"].get(name, [0, 0])
        brate = bp / bt if bt else None
        crate = cp / ct if ct else None
        lo, hi = wilson(cp, ct)
        status = "ok"
        if brate is None or crate is None:
            status = "missing"
        elif crate < brate - args.tolerance and hi < brate:
            status = "REGRESSION"
            regressed = True
        elif crate < brate - args.tolerance:
            status = "drop-not-significant"
        elif crate > brate + args.tolerance:
            status = "improved"
        rows.append({"bucket": "ALL" if name == "__all__" else name, "baseline": brate, "candidate": crate,
                     "candidate_ci95": [round(lo, 3), round(hi, 3)], "status": status})
    flips = []
    for case, (cp, ct) in sorted(cand["cases"].items()):
        bp, bt = base["cases"].get(case, [0, 0])
        if bt and ct and bp / bt >= 0.5 > cp / ct:
            flips.append(case)
    result = {"buckets": rows, "newly_failing_cases": flips,
              "invalid_runs": {"baseline": base["invalid"], "candidate": cand["invalid"]}}
    emit(result, args.json)
    return 1 if regressed and args.fail_on_regression else 0


def cmd_judge(args) -> int:
    tp = tn = fp = fn = 0
    for row in load(args.labels):
        human, judge = bool(row["human"]), bool(row["judge"])
        if human and judge:
            tp += 1
        elif human:
            fn += 1
        elif judge:
            fp += 1
        else:
            tn += 1
    pos, neg = tp + fn, tn + fp
    result = {"n": pos + neg, "positives": pos, "negatives": neg,
              "tpr": tp / pos if pos else None, "tnr": tn / neg if neg else None,
              "agreement": (tp + tn) / (pos + neg) if pos + neg else None}
    if pos < 20 or neg < 20:
        result["warning"] = "fewer than 20 human-labelled passes or fails; calibration is not reliable yet"
    emit(result, args.json)
    return 0


def emit(result: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    for key, value in result.items():
        if isinstance(value, list) and value and isinstance(value[0], dict):
            print(f"{key}:")
            for item in value:
                print("  " + "  ".join(f"{k}={_fmt(v)}" for k, v in item.items()))
        else:
            print(f"{key}: {_fmt(value)}")


def _fmt(value):
    return f"{value:.3f}" if isinstance(value, float) else value


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    sub = parser.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("summary")
    s.add_argument("results")
    s.set_defaults(func=cmd_summary)
    c = sub.add_parser("compare")
    c.add_argument("baseline")
    c.add_argument("candidate")
    c.add_argument("--tolerance", type=float, default=0.05)
    c.add_argument("--fail-on-regression", action="store_true")
    c.set_defaults(func=cmd_compare)
    j = sub.add_parser("judge")
    j.add_argument("labels")
    j.set_defaults(func=cmd_judge)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
