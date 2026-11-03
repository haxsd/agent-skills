"""Offline tests for skills/agent-evals/scripts/eval_report.py."""

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL = REPO_ROOT / "skills" / "agent-evals" / "scripts" / "eval_report.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("eval_report", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_jsonl(directory, name, rows):
    path = Path(directory) / name
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return str(path)


def trials(bucket, case_prefix, passed, total):
    return [{"case": f"{case_prefix}{i % 5}", "bucket": bucket, "pass": i < passed} for i in range(total)]


class EvalReportTests(unittest.TestCase):
    def setUp(self):
        self.tool = load_tool()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def run_tool(self, argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = self.tool.main(["--json", *argv])
        return code, json.loads(out.getvalue())

    def test_wilson_bounds(self):
        lo, hi = self.tool.wilson(8, 10)
        self.assertAlmostEqual(lo, 0.490, places=2)
        self.assertAlmostEqual(hi, 0.943, places=2)
        self.assertEqual(self.tool.wilson(0, 0), (0.0, 0.0))

    def test_summary_skips_invalid_runs(self):
        rows = trials("tools", "t", 3, 4) + [{"case": "t9", "bucket": "tools", "error": "timeout"}]
        code, result = self.run_tool(["summary", write_jsonl(self.tmp.name, "r.jsonl", rows)])
        self.assertEqual(code, 0)
        self.assertEqual(result["invalid_runs"], 1)
        tools = next(b for b in result["buckets"] if b["bucket"] == "tools")
        self.assertEqual((tools["passed"], tools["total"]), (3, 4))

    def test_significant_drop_is_regression_and_fails(self):
        base = write_jsonl(self.tmp.name, "b.jsonl", trials("tools", "t", 38, 40))
        cand = write_jsonl(self.tmp.name, "c.jsonl", trials("tools", "t", 10, 40))
        code, result = self.run_tool(["compare", base, cand, "--fail-on-regression"])
        self.assertEqual(code, 1)
        tools = next(b for b in result["buckets"] if b["bucket"] == "tools")
        self.assertEqual(tools["status"], "REGRESSION")
        self.assertTrue(result["newly_failing_cases"])

    def test_small_noisy_drop_is_not_regression(self):
        base = write_jsonl(self.tmp.name, "b.jsonl", trials("fmt", "f", 4, 5))
        cand = write_jsonl(self.tmp.name, "c.jsonl", trials("fmt", "f", 3, 5))
        code, result = self.run_tool(["compare", base, cand, "--fail-on-regression"])
        self.assertEqual(code, 0)
        fmt = next(b for b in result["buckets"] if b["bucket"] == "fmt")
        self.assertEqual(fmt["status"], "drop-not-significant")

    def test_judge_calibration_rates_and_warning(self):
        rows = [{"human": True, "judge": True}] * 9 + [{"human": True, "judge": False}] \
            + [{"human": False, "judge": False}] * 8 + [{"human": False, "judge": True}] * 2
        code, result = self.run_tool(["judge", write_jsonl(self.tmp.name, "j.jsonl", rows)])
        self.assertEqual(code, 0)
        self.assertAlmostEqual(result["tpr"], 0.9)
        self.assertAlmostEqual(result["tnr"], 0.8)
        self.assertIn("warning", result)


if __name__ == "__main__":
    unittest.main()
