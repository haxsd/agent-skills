"""Unit and optional integration tests for the original PDF toolkit."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "pdf-toolkit" / "scripts" / "pdf_tool.py"
SPEC = importlib.util.spec_from_file_location("pdf_tool", SCRIPT)
pdf_tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pdf_tool)


class PageSelectionTests(unittest.TestCase):
    def test_all_and_explicit_ranges(self):
        self.assertEqual([1, 2, 3, 4], pdf_tool.parse_pages("all", 4))
        self.assertEqual([1, 3, 4, 5, 8], pdf_tool.parse_pages("1,3-5,last", 8))

    def test_duplicates_are_removed(self):
        self.assertEqual([1, 2, 3], pdf_tool.parse_pages("1,1-2,2,3", 3))

    def test_invalid_ranges_stop(self):
        for value in ("0", "5", "3-2", "1-9", ",", "last-last"):
            with self.subTest(value=value):
                with self.assertRaises(pdf_tool.PdfToolError):
                    pdf_tool.parse_pages(value, 4)


class OutputSafetyTests(unittest.TestCase):
    def test_output_cannot_replace_an_input(self):
        with tempfile.TemporaryDirectory() as raw:
            source = Path(raw) / "source.pdf"
            source.write_bytes(b"%PDF-1.4\n")
            with self.assertRaises(pdf_tool.PdfToolError):
                pdf_tool.find_output(source, inputs=(source,), overwrite=True)

    def test_existing_output_requires_explicit_overwrite(self):
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw) / "out.pdf"
            output.write_bytes(b"existing")
            with self.assertRaises(pdf_tool.PdfToolError):
                pdf_tool.find_output(output)
            self.assertEqual(
                output,
                pdf_tool.find_output(output, overwrite=True),
            )


class JsonInputTests(unittest.TestCase):
    def test_form_values_must_be_an_object(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "values.json"
            path.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")
            with self.assertRaises(pdf_tool.PdfToolError):
                pdf_tool.read_json(path)

    def test_valid_form_values_load(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "values.json"
            path.write_text(
                json.dumps({"name": "Ada", "approved": True}), encoding="utf-8"
            )
            self.assertEqual(
                {"name": "Ada", "approved": True}, pdf_tool.read_json(path)
            )


class CliTests(unittest.TestCase):
    def test_help_lists_core_commands(self):
        output = pdf_tool.build_parser().format_help()
        for command in (
            "inspect",
            "extract-text",
            "extract-tables",
            "merge",
            "split",
            "form-fill",
            "create",
            "render",
        ):
            self.assertIn(command, output)


@unittest.skipUnless(
    all(
        importlib.util.find_spec(name)
        for name in ("pypdf", "pdfplumber", "reportlab")
    ),
    "optional PDF integration dependencies are not installed",
)
class OptionalIntegrationTests(unittest.TestCase):
    def test_create_merge_split_and_extract_roundtrip(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            first = root / "first.pdf"
            second = root / "second.pdf"
            merged = root / "merged.pdf"
            pages_dir = root / "pages"
            text_json = root / "text.json"
            for path, text in (
                (first, "First document"),
                (second, "Second document"),
            ):
                self.assertEqual(
                    0,
                    pdf_tool.main(
                        [
                            "create",
                            "--title",
                            text,
                            "--text",
                            text,
                            "--output",
                            str(path),
                        ]
                    ),
                )
            self.assertEqual(
                0,
                pdf_tool.main(
                    ["merge", str(first), str(second), "--output", str(merged)]
                ),
            )
            pypdf = importlib.import_module("pypdf")
            self.assertEqual(2, len(pypdf.PdfReader(str(merged)).pages))
            self.assertEqual(
                0,
                pdf_tool.main(
                    [
                        "split",
                        str(merged),
                        "--output-dir",
                        str(pages_dir),
                    ]
                ),
            )
            self.assertEqual(2, len(list(pages_dir.glob("*.pdf"))))
            self.assertEqual(
                0,
                pdf_tool.main(
                    [
                        "extract-text",
                        str(merged),
                        "--output",
                        str(text_json),
                        "--format",
                        "json",
                    ]
                ),
            )
            extracted = json.loads(text_json.read_text(encoding="utf-8"))
            self.assertEqual(2, len(extracted["pages"]))


if __name__ == "__main__":
    unittest.main()
