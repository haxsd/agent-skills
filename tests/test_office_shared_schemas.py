"""Offline checks for the shared Office schema path."""

from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OFFICE = ROOT / "skills" / "xlsx" / "scripts" / "office"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class OfficeSharedSchemasTests(unittest.TestCase):
    def test_resolve_schemas_dir_uses_repo_shared_copy(self):
        schema_paths = load("office_schema_paths", OFFICE / "schema_paths.py")
        resolved = schema_paths.resolve_schemas_dir(OFFICE / "schema_paths.py")
        expected = (ROOT / "shared" / "office" / "schemas").resolve()
        self.assertEqual(resolved, expected)
        self.assertTrue((resolved / "ISO-IEC29500-4_2016" / "sml.xsd").is_file())

    def test_each_office_skill_omits_copied_xsd_trees(self):
        for name in ("xlsx", "docx", "pptx"):
            leftover = list((ROOT / "skills" / name).rglob("*.xsd"))
            self.assertEqual(leftover, [], f"{name} still vendors XSD files")

    def test_env_override_rejects_missing_dir(self):
        schema_paths = load("office_schema_paths_env", OFFICE / "schema_paths.py")
        os.environ["AGENT_SKILLS_OFFICE_SCHEMAS"] = str(ROOT / "does-not-exist")
        try:
            with self.assertRaises(FileNotFoundError):
                schema_paths.resolve_schemas_dir(OFFICE / "schema_paths.py")
        finally:
            os.environ.pop("AGENT_SKILLS_OFFICE_SCHEMAS", None)


if __name__ == "__main__":
    unittest.main()
