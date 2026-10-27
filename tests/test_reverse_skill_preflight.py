"""Offline tests for reverse-skill external package preflight."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "reverse-skill" / "scripts" / "preflight.py"
SPEC = importlib.util.spec_from_file_location("reverse_preflight", SCRIPT)
preflight = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preflight)


def make_pack(root, include_review=True):
    root.mkdir(parents=True, exist_ok=True)
    (root / "RULES_zh.md").write_text("rules\n", encoding="utf-8")
    (root / "skills" / "scripts").mkdir(parents=True, exist_ok=True)
    (root / "skills" / "MASTER-ROUTING.md").write_text(
        "routing\n", encoding="utf-8"
    )
    (root / "skills" / "scripts" / "master-route.ps1").write_text(
        "route\n", encoding="utf-8"
    )
    (root / "skills" / "scripts" / "case-init.ps1").write_text(
        "init\n", encoding="utf-8"
    )
    if include_review:
        review = root / "skills" / "case-review" / "scripts"
        review.mkdir(parents=True, exist_ok=True)
        (review / "review_case.py").write_text("review\n", encoding="utf-8")


class PreflightTests(unittest.TestCase):
    def test_complete_pack_passes(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "pack"
            make_pack(root)
            report = preflight.inspect_root(root)
            self.assertTrue(report["ok"])
            self.assertEqual(["RULES_zh.md"], report["ruleFiles"])
            self.assertEqual([], report["missingRequired"])

    def test_missing_review_script_is_reported(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "pack"
            make_pack(root, include_review=False)
            report = preflight.inspect_root(root)
            self.assertFalse(report["ok"])
            self.assertIn(
                "skills/case-review/scripts/review_case.py",
                report["missingRequired"],
            )

    def test_missing_root_is_reported(self):
        with tempfile.TemporaryDirectory() as raw:
            missing = Path(raw) / "absent"
            report = preflight.inspect_root(missing)
            self.assertFalse(report["ok"])
            self.assertIn("error", report)

    def test_cli_returns_machine_readable_success(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "pack"
            make_pack(root)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = preflight.main(["--root", str(root)])
            self.assertEqual(0, code)
            report = json.loads(output.getvalue())
            self.assertTrue(report["ok"])

    def test_cli_returns_nonzero_for_incomplete_pack(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "pack"
            make_pack(root, include_review=False)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = preflight.main(["--root", str(root)])
            self.assertEqual(2, code)
            report = json.loads(output.getvalue())
            self.assertFalse(report["ok"])


if __name__ == "__main__":
    unittest.main()
