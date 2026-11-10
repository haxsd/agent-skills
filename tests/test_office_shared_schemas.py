"""Offline checks for the shared Office schema path and Python package."""

from __future__ import annotations

import hashlib
import importlib
import os
import subprocess
import sys
import tempfile
import types
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARED_OFFICE_PYTHON = ROOT / "shared" / "office" / "python"
SHARED_SCHEMAS = ROOT / "shared" / "office" / "schemas"
SHARED_SOFFICE = SHARED_OFFICE_PYTHON / "office" / "soffice.py"
SHIM_FILES = {
    "__init__.py",
    "_path.py",
    "validate.py",
    "soffice.py",
    "zipio.py",
    "README.md",
}
DOCX_PPTX_ONLY = {
    "helpers/pptx_chart.py",
    "helpers/pptx_slide.py",
    "helpers/pptx_theme.py",
    "validators/docx.py",
    "validators/pptx.py",
    "validators/redlining.py",
}


def _clear_office_modules() -> None:
    for key in list(sys.modules):
        if key == "office" or key.startswith("office.") or key in {
            "helpers", "validators", "schema_paths", "zipio", "_path",
        } or key.startswith("helpers.") or key.startswith("validators."):
            del sys.modules[key]


def _import_office_from_skill(name: str):
    scripts = ROOT / "skills" / name / "scripts"
    _clear_office_modules()
    sys.path.insert(0, str(scripts))
    try:
        importlib.import_module("office")
        return types.SimpleNamespace(
            soffice=importlib.import_module("office.soffice"),
            helpers=importlib.import_module("office.helpers"),
            schema_paths=importlib.import_module("office.schema_paths"),
            zipio=importlib.import_module("office.zipio"),
        )
    finally:
        if str(scripts) in sys.path:
            sys.path.remove(str(scripts))


class OfficeSharedSchemasTests(unittest.TestCase):
    def tearDown(self):
        _clear_office_modules()
        os.environ.pop("AGENT_SKILLS_OFFICE_SCHEMAS", None)
        os.environ.pop("AGENT_SKILLS_OFFICE_PYTHON", None)

    def test_resolve_schemas_dir_uses_repo_shared_copy(self):
        office = _import_office_from_skill("xlsx")
        resolved = office.schema_paths.resolve_schemas_dir()
        self.assertEqual(resolved, SHARED_SCHEMAS.resolve())
        self.assertTrue((resolved / "ISO-IEC29500-4_2016" / "sml.xsd").is_file())

    def test_each_office_skill_omits_copied_xsd_trees(self):
        for name in ("xlsx", "docx", "pptx"):
            leftover = list((ROOT / "skills" / name).rglob("*.xsd"))
            self.assertEqual(leftover, [], f"{name} still vendors XSD files")

    def test_env_override_rejects_missing_dir(self):
        office = _import_office_from_skill("xlsx")
        os.environ["AGENT_SKILLS_OFFICE_SCHEMAS"] = str(ROOT / "does-not-exist")
        with self.assertRaises(FileNotFoundError):
            office.schema_paths.resolve_schemas_dir()

    def test_implementation_is_single_shared_copy(self):
        for name in ("xlsx", "docx", "pptx"):
            office_dir = ROOT / "skills" / name / "scripts" / "office"
            leftover = [
                p for p in office_dir.rglob("*")
                if p.is_file()
                and p.suffix != ".pyc"
                and "__pycache__" not in p.parts
                and p.name not in SHIM_FILES
            ]
            self.assertEqual(leftover, [], f"{name} still vendors office implementation: {leftover}")
        xlsx_dir = ROOT / "skills" / "xlsx" / "scripts" / "office"
        for rel in DOCX_PPTX_ONLY:
            self.assertFalse((xlsx_dir / rel).exists(), f"xlsx still carries {rel}")
        for rel in DOCX_PPTX_ONLY:
            self.assertTrue(
                (SHARED_OFFICE_PYTHON / "office" / rel).is_file(),
                f"shared copy missing {rel}",
            )

    def test_skills_do_not_duplicate_implementation_bytes(self):
        """Implementation files must not appear as byte-identical copies under skills/."""
        hashes: dict[str, list[str]] = {}
        for name in ("xlsx", "docx", "pptx"):
            office_dir = ROOT / "skills" / name / "scripts" / "office"
            for path in office_dir.rglob("*"):
                if not path.is_file() or path.name in SHIM_FILES:
                    continue
                digest = hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
                hashes.setdefault(digest, []).append(path.relative_to(ROOT).as_posix())
        duplicated = {k: v for k, v in hashes.items() if len(v) > 1}
        self.assertEqual(duplicated, {}, f"byte-identical implementation remains: {duplicated}")

    def test_each_skill_imports_the_same_shared_code_and_schemas(self):
        soffice_files = []
        schemas = []
        helper_files = []
        for name in ("xlsx", "docx", "pptx"):
            office = _import_office_from_skill(name)
            self.assertTrue(hasattr(office.soffice, "run_soffice"))
            self.assertTrue(hasattr(office.helpers, "safe_extract"))
            self.assertTrue(hasattr(office.helpers, "rezip"))
            soffice_files.append(Path(office.soffice.__file__).resolve())
            helper_files.append(Path(office.helpers.__file__).resolve())
            schemas.append(office.schema_paths.resolve_schemas_dir())
        self.assertEqual(set(soffice_files), {SHARED_SOFFICE.resolve()})
        self.assertEqual(len(set(helper_files)), 1)
        self.assertEqual(set(schemas), {SHARED_SCHEMAS.resolve()})

    def test_zipio_roundtrip_and_symlink_rejection(self):
        office = _import_office_from_skill("docx")
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            src = base / "src"
            src.mkdir()
            (src / "[Content_Types].xml").write_text("<Types/>", encoding="utf-8")
            (src / "word").mkdir()
            (src / "word" / "document.xml").write_text("<w:document/>", encoding="utf-8")
            archive = base / "sample.docx"
            unpacked = base / "unpacked"
            packed = base / "out.docx"
            office.zipio.pack_office(src, archive)
            office.zipio.unpack_office(archive, unpacked)
            self.assertEqual(
                (unpacked / "word" / "document.xml").read_text(encoding="utf-8"),
                "<w:document/>",
            )
            office.zipio.pack_office(unpacked, packed)
            self.assertTrue(packed.is_file())

            bad = base / "bad.docx"
            with zipfile.ZipFile(bad, "w") as zf:
                info = zipfile.ZipInfo("link-to-elsewhere")
                info.create_system = 3
                info.external_attr = 0xA000 << 16  # symlink
                zf.writestr(info, b"/tmp/target")
            with self.assertRaises(ValueError):
                office.zipio.unpack_office(bad, base / "unsafe")

    def test_skill_launchers_run_shared_zipio_help(self):
        launcher = ROOT / "skills" / "xlsx" / "scripts" / "office" / "zipio.py"
        result = subprocess.run(
            [sys.executable, str(launcher), "--help"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("unpack", result.stdout)


class InstallerScriptContractTests(unittest.TestCase):
    def test_shared_link_condition_includes_office_skills(self):
        text = (ROOT / "install.ps1").read_text(encoding="utf-8")
        self.assertIn("$SharedConsumers = @('token-efficient-workflow', 'xlsx', 'docx', 'pptx')", text)
        self.assertIn("$linkShared", text)
        # The previous condition must not remain as the only gate.
        self.assertNotIn(
            "if ((Test-Path $SharedSrc) -and (-not $Only -or 'token-efficient-workflow' -in $Only))",
            text,
        )


if __name__ == "__main__":
    unittest.main()
