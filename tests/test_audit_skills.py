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
    def test_xml_and_svg_metrics_ignore_checkout_line_endings(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            for suffix in (".xml", ".svg"):
                path = root / ("example" + suffix)
                expected = b"<root>\n  <item/>\n</root>\n"
                path.write_bytes(expected.replace(b"\n", b"\r\n"))
                self.assertEqual(audit.canonical_bytes(path), expected)

    def fixture(self, root):
        (root / "skills" / "example").mkdir(parents=True)
        (root / "archive" / "skills").mkdir(parents=True)
        text = "---\nname: example\ndescription: Use for fixture checks.\n---\n\nUnique evidence.\n"
        (root / "skills" / "example" / "SKILL.md").write_text(text, encoding="utf-8", newline="\n")
        (root / "manifest.json").write_text(json.dumps({"skills": [{
            "name": "example", "files": 1, "bytes": len(text.encode()),
            "description": "Use for fixture checks."}]}), encoding="utf-8")
        (root / "external.json").write_text("[]", encoding="utf-8")
        source_dir = root / "docs" / "sources"
        source_dir.mkdir(parents=True)
        (source_dir / "skill-provenance.json").write_text(json.dumps({
            "schemaVersion": 1, "skills": [{"name": "example", "kind": "original",
                                           "contributions": ["Fixture authored locally."]}]
        }), encoding="utf-8")
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

    def test_json_path_is_not_truncated_to_js(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            catalog = self.fixture(root)
            references = root / "skills/example/references"
            references.mkdir()
            (references / "schema.json").write_text("{}\n", encoding="utf-8")
            path = root / "skills/example/SKILL.md"
            with path.open("a", encoding="utf-8") as handle:
                handle.write("Validate `references/schema.json` before delivery.\n")
            findings = audit.inspect(root, catalog)["findings"]
            messages = [item["message"] for item in findings
                        if item["code"] == "unresolved-path-in-entrypoint"]
            self.assertNotIn("references/schema.js", messages)
            self.assertNotIn("references/schema.json", messages)

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

    def set_provenance(self, root, entries):
        (root / "docs" / "sources" / "skill-provenance.json").write_text(
            json.dumps({"schemaVersion": 1, "skills": entries}), encoding="utf-8")

    def test_unclassified_history_is_visible_not_assumed_original(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            catalog = self.fixture(root)
            self.set_provenance(root, [])
            result = audit.inspect(root, catalog)
            self.assertEqual("unverified", result["skills"][0]["authorship"])
            catalog["skills"][0]["priority"] = "P2"
            rendered = audit.render_catalog(catalog, result)
            self.assertIn("待核验", rendered)
            self.assertNotIn("| 本仓原创 |", rendered)

    def test_upstream_material_cannot_be_relabelled_as_original(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            catalog = self.fixture(root)
            self.set_provenance(root, [{"name": "example", "kind": "original",
                                       "upstreamFiles": ["skills/example/UPSTREAM.json"],
                                       "contributions": ["Translated and improved."]}])
            result = audit.inspect(root, catalog)
            self.assertIn("provenance-original-upstream", {f["code"] for f in result["findings"]})

    def test_derived_skill_requires_upstream_and_contribution(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            catalog = self.fixture(root)
            self.set_provenance(root, [{"name": "example", "kind": "derived"}])
            codes = {f["code"] for f in audit.inspect(root, catalog)["findings"]}
            self.assertIn("provenance-missing-upstream", codes)
            self.assertIn("provenance-missing-contributions", codes)

    def test_source_files_cannot_escape_repository(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            catalog = self.fixture(root)
            self.set_provenance(root, [{"name": "example", "kind": "upstream",
                                       "upstreamFiles": ["../outside.json"]}])
            codes = {f["code"] for f in audit.inspect(root, catalog)["findings"]}
            self.assertIn("provenance-source-path", codes)

    def test_dependency_does_not_turn_original_wrapper_into_derivative(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            catalog = self.fixture(root)
            source = "skills/example/UPSTREAM.json"
            (root / source).write_text(json.dumps({
                "repository": "https://github.com/example/tool", "commit": "a" * 40,
                "license": "MIT"}), encoding="utf-8")
            self.set_provenance(root, [{"name": "example", "kind": "original",
                                       "dependencyFiles": [source],
                                       "contributions": ["Original wrapper text; no tool code copied."]}])
            result = audit.inspect(root, catalog)
            self.assertFalse(any(f["level"] == "error" for f in result["findings"]))
            self.assertEqual("original", result["skills"][0]["authorship"])

    def test_duplicate_or_unknown_provenance_entry_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            catalog = self.fixture(root)
            entry = {"name": "example", "kind": "unverified"}
            self.set_provenance(root, [entry, entry, {"name": "typo", "kind": "upstream"}])
            codes = {f["code"] for f in audit.inspect(root, catalog)["findings"]}
            self.assertIn("provenance-duplicate", codes)
            self.assertIn("provenance-unknown-skill", codes)

    def test_original_cannot_hide_existing_upstream_metadata(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            catalog = self.fixture(root)
            (root / "skills/example/UPSTREAM.json").write_text("{}", encoding="utf-8")
            codes = {f["code"] for f in audit.inspect(root, catalog)["findings"]}
            self.assertIn("provenance-unclassified-upstream", codes)

    def test_sources_are_rendered_for_original_and_derived_skills(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            catalog = self.fixture(root)
            source = "skills/example/UPSTREAM.json"
            (root / source).write_text(json.dumps({
                "repository": "https://github.com/example/tool", "commit": "a" * 40,
                "license": "MIT", "author": "Upstream Author"}), encoding="utf-8")
            self.set_provenance(root, [{"name": "example", "kind": "derived",
                                       "upstreamFiles": [source], "contributions": ["Add local tests."]}])
            result = audit.inspect(root, catalog)
            rendered = audit.render_attribution(root, catalog, result)
            self.assertIn("Upstream Author", rendered)
            self.assertIn("https://github.com/example/tool", rendered)
            self.assertIn("Add local tests.", rendered)
            self.assertIn("MIT", rendered)
            self.assertIn("a" * 40, rendered)
            note = audit.render_source_note("example", "derived", "active")
            self.assertIn("../../ATTRIBUTION.md#example", note)
            archived = audit.render_source_note("example", "derived", "archived")
            self.assertIn("../../../ATTRIBUTION.md#example", archived)

    def test_source_note_update_preserves_skill_content_and_is_idempotent(self):
        text = "---\nname: example\ndescription: Fixture.\n---\n\n# Example\n\nKeep this instruction.\n"
        note = audit.render_source_note("example", "original", "active")
        updated = audit.with_source_note(text, note)
        self.assertIn("Keep this instruction.", updated)
        self.assertEqual(updated, audit.with_source_note(updated, note))
        changed = audit.with_source_note(updated, audit.render_source_note("example", "derived", "active"))
        self.assertEqual(1, changed.count("<!-- provenance:start -->"))
        self.assertNotIn("本仓原创", changed)

    def test_source_metadata_requires_pinned_version_and_license(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            catalog = self.fixture(root)
            source = "skills/example/UPSTREAM.json"
            (root / source).write_text('{"repository": "https://github.com/example/tool"}', encoding="utf-8")
            self.set_provenance(root, [{"name": "example", "kind": "upstream", "upstreamFiles": [source]}])
            codes = {f["code"] for f in audit.inspect(root, catalog)["findings"]}
            self.assertIn("provenance-source-metadata", codes)


if __name__ == "__main__":
    unittest.main()
