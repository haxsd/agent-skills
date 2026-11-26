"""Entry-document count assertions, using temporary fixtures and stdlib only."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location(
    "check_docs", Path(__file__).resolve().parents[1] / "scripts" / "check_docs.py")
docs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(docs)


def fixture(root, readme, archived=0, external=0):
    """Write a catalog plus a README whose counts the caller controls."""
    skills = [{"name": f"a{index}", "state": "active"} for index in range(2)]
    skills += [{"name": f"z{index}", "state": "archived"} for index in range(archived)]
    skills += [{"name": f"e{index}", "state": "external"} for index in range(external)]
    (root / "catalog.json").write_text(json.dumps({
        "categories": [{"id": "one"}, {"id": "two"}, {"id": "three"}],
        "skills": skills,
    }), encoding="utf-8")
    (root / "README.md").write_text(readme, encoding="utf-8", newline="\n")
    (root / "README-EN.md").write_text("", encoding="utf-8", newline="\n")


class CheckDocsTests(unittest.TestCase):
    def test_matching_counts_pass(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            fixture(root, "> 2 个启用技能、0 个归档技能、3 个用途分类\n\n[指南](docs/guide.md)\n")
            (root / "docs").mkdir()
            (root / "docs" / "guide.md").write_text("# Guide\n", encoding="utf-8")
            self.assertEqual(docs.check_counts(root), [])
            errors, count = docs.check(root)
            self.assertEqual(errors, [])
            # README.md、README-EN.md、docs/guide.md；不存在的入口文档不计入。
            self.assertEqual(count, 3)

    def test_stale_count_is_reported_with_line_number(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            fixture(root, "# x\n\n> 5 个启用技能、0 个归档技能、3 个用途分类\n")
            errors = docs.check_counts(root)
            self.assertEqual(len(errors), 1)
            self.assertIn("README.md:3", errors[0])
            self.assertIn("实际 2", errors[0])

    def test_english_entry_is_checked_too(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            fixture(root, "# x\n")
            (root / "README-EN.md").write_text(
                "9 active skills, 0 archived skills and 3 categories\n", encoding="utf-8")
            errors = docs.check_counts(root)
            self.assertEqual(len(errors), 1)
            self.assertIn("README-EN.md:1", errors[0])

    def test_genuinely_broken_link_still_fails(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            fixture(root, "> 2 个启用技能、0 个归档技能、3 个用途分类\n\n[缺失](docs/none.md)\n")
            errors, _ = docs.check(root)
            self.assertEqual(errors, ["README.md: docs/none.md"])


if __name__ == "__main__":
    unittest.main()
