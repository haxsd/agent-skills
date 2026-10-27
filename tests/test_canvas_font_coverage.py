import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/canvas-design/scripts/check_font_coverage.py"
FONT = ROOT / "skills/canvas-design/canvas-fonts/DMMono-Regular.ttf"

SPEC = importlib.util.spec_from_file_location("canvas_font_coverage", SCRIPT)
assert SPEC and SPEC.loader
coverage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(coverage)


class FontCoverageTests(unittest.TestCase):
    def test_latin_font_covers_latin_and_ignores_whitespace(self):
        report = coverage.inspect_fonts([FONT], "AbC 123\n")
        self.assertTrue(report["ok"])
        self.assertEqual([], report["missing"])
        self.assertEqual(6, report["characters"])

    def test_latin_font_reports_missing_cjk(self):
        report = coverage.inspect_fonts([FONT], "你好")
        self.assertFalse(report["ok"])
        self.assertEqual(["你", "好"], report["missing"])
        self.assertEqual(0, report["covered"])

    def test_multiple_fonts_are_treated_as_a_fallback_stack(self):
        report = coverage.inspect_fonts([FONT, FONT], "ABC")
        self.assertTrue(report["ok"])
        self.assertEqual(2, len(report["fonts"]))

    def test_invalid_font_fails_closed(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "broken.ttf"
            path.write_bytes(b"not a font")
            with self.assertRaises(coverage.FontError):
                coverage.inspect_fonts([path], "ABC")

    def test_cli_returns_one_and_json_for_missing_glyph(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(FONT), "--text", "你好", "--json"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(1, result.returncode, result.stderr)
        self.assertEqual(["你", "好"], json.loads(result.stdout)["missing"])

    def test_cli_rejects_an_invalid_font(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "broken.ttf"
            path.write_bytes(b"broken")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path), "--text", "ABC"],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(2, result.returncode)
            self.assertIn("font coverage check failed", result.stderr)


if __name__ == "__main__":
    unittest.main()
