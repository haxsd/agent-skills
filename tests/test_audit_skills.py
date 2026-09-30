"""Observable repository checks, using temporary fixtures and stdlib only."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location(
    "audit_skills", Path(__file__).resolve().parents[1] / "scripts" / "audit_skills.py")
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class AuditTests(unittest.TestCase):
    def fixture(self, root):
        (root / "skills" / "example").mkdir(parents=True)
        (root / "archive" / "skills").mkdir(parents=True)
        text = "---\nname: example\ndescription: Use for fixture checks.\n---\n\nUnique evidence.\n"
        (root / "skills" / "example" / "SKILL.md").write_text(text, encoding="utf-8", newline="\n")
        (root / "manifest.json").write_text(json.dumps({"skills": [{
            "name": "example", "files": 1, "bytes": len(text.encode()),
            "description": "Use for fixture checks."}]}), encoding="utf-8")
        (root / "external.json").write_text("[]", encoding="utf-8")
        return {"baselineCommit": "fixture", "reviewedAt": "2026-09-30",
                "categories": [{"id": "testing", "title": "测试"}],
                "skills": [{"name": "example", "state": "active", "value": "high",
                            "readiness": "conditional", "action": "retain",
                            "category": "testing", "mergeWith": [],
                            "evidence": [{"file": "SKILL.md", "text": "Unique evidence."}]}]}

    def test_clean_inventory_has_no_errors_and_locates_evidence(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            result = audit.inspect(root, self.fixture(root))
            self.assertFalse(result["findings"])
            self.assertEqual(6, result["skills"][0]["evidence"][0]["line"])

    def test_new_unreviewed_skill_is_not_silently_omitted(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            catalog = self.fixture(root)
            (root / "skills" / "new-skill").mkdir()
            codes = {item["code"] for item in audit.inspect(root, catalog)["findings"]}
            self.assertIn("uncatalogued-skill", codes)
            self.assertIn("manifest-coverage", codes)

    def test_changed_source_invalidates_evidence(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            catalog = self.fixture(root)
            catalog["skills"][0]["evidence"][0]["text"] = "Removed instruction"
            result = audit.inspect(root, catalog)
            self.assertIn("stale-evidence", {item["code"] for item in result["findings"]})

    def test_generated_project_asset_is_hint_not_invalid_skill(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            catalog = self.fixture(root)
            path = root / "skills" / "example" / "SKILL.md"
            with path.open("a", encoding="utf-8") as handle:
                handle.write("Generate `assets/design-tokens.css` in the user's project.\n")
            findings = audit.inspect(root, catalog)["findings"]
            unresolved = [item for item in findings if item["code"] == "unresolved-path-in-entrypoint"]
            self.assertEqual("hint", unresolved[0]["level"])
            self.assertFalse(any(item["level"] == "error" for item in findings))

    def test_duplicate_detection_is_cross_skill_and_line_ending_independent(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            catalog = self.fixture(root)
            second = root / "archive" / "skills" / "second"
            second.mkdir()
            (second / "SKILL.md").write_text(
                "---\nname: second\ndescription: Other fixture.\n---\n", encoding="utf-8")
            catalog["skills"].append({**catalog["skills"][0], "name": "second",
                                      "state": "archived", "evidence": []})
            (root / "skills" / "example" / "reference.md").write_bytes(b"shared\r\ntext\r\n")
            (second / "reference.md").write_bytes(b"shared\ntext\n")
            groups = audit.inspect(root, catalog)["exactDuplicateTextGroupsLF"]
            self.assertEqual([["archive/skills/second/reference.md", "skills/example/reference.md"]], groups)


if __name__ == "__main__":
    unittest.main()
