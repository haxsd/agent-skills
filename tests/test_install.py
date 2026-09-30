"""Windows junction regression in disposable profiles; never touches user installs."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "install.ps1"
SHELL = os.environ.get("TEST_POWERSHELL")


@unittest.skipUnless(os.name == "nt" and SHELL and Path(SHELL).is_file(), "Windows with explicit TEST_POWERSHELL required")
class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="codex-installer-test-")
        self.base = Path(self.temporary.name).resolve()
        self.repo, self.profile, self.external = self.base / "repo", self.base / "profile", self.base / "external"
        for path in (self.repo, self.profile, self.external):
            path.mkdir()
        shutil.copyfile(SOURCE, self.repo / "install.ps1")
        (self.repo / "shared").mkdir()
        (self.repo / "shared/rules.md").write_text("shared")
        names = ["example", "token-efficient-workflow"]
        for name in names:
            (self.repo / "skills" / name).mkdir(parents=True)
            (self.repo / "skills" / name / "SKILL.md").write_text("fixture")
        (self.external / "SKILL.md").write_text("external fixture")
        (self.repo / "manifest.json").write_text(json.dumps({"skills": [
            {"name": n, "defaultTargets": ["codex"]} for n in names]}))
        (self.repo / "external.json").write_text(json.dumps([
            {"name": "external-fixture", "path": "%INSTALL_TEST_EXTERNAL%", "targets": ["agents"]}]))
        self.environment = os.environ | {"USERPROFILE": str(self.profile), "INSTALL_TEST_EXTERNAL": str(self.external)}

    def tearDown(self):
        # Remove junctions themselves, never recursively traverse their sources.
        for current, dirs, _ in os.walk(self.base, topdown=True, followlinks=False):
            for name in list(dirs):
                path = Path(current) / name
                if path.is_junction():
                    self.assertTrue(path.is_relative_to(self.base))
                    os.rmdir(path)
                    dirs.remove(name)
        self.temporary.cleanup()

    def run_installer(self, *args, expected=0):
        result = subprocess.run([SHELL, "-NoProfile", "-File", str(self.repo / "install.ps1"), *args],
                                env=self.environment, text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result.stdout

    def test_only_filters_external_and_shared_and_is_idempotent(self):
        self.run_installer("-Only", "example", "-Target", "codex")
        target = self.profile / ".codex/skills/example"
        self.assertEqual(target.resolve(), (self.repo / "skills/example").resolve())
        self.assertFalse((self.profile / "tools/shared").exists())
        self.assertFalse((self.profile / ".codex/skills/external-fixture").exists())
        self.run_installer("-Only", "example", "-Target", "codex")
        self.assertEqual(list(self.profile.rglob("*.backup-*")), [])

    def test_external_only_and_explicit_target(self):
        self.run_installer("-Only", "external-fixture", "-Target", "codex")
        target = self.profile / ".codex/skills/external-fixture"
        self.assertEqual(target.resolve(), self.external)
        self.assertFalse((self.profile / ".codex/skills/example").exists())
        self.assertFalse((self.profile / ".agents/skills/external-fixture").exists())

    def test_unknown_name_and_dry_run_do_not_mutate(self):
        self.run_installer("-Only", "typo", expected=1)
        self.assertTrue(all(not (self.profile / p).exists() for p in (".codex", ".agents", "tools")))
        self.run_installer("-Only", "example", "-Target", "codex", "-DryRun")
        self.assertTrue(all(not (self.profile / p).exists() for p in (".codex", ".agents", "tools")))

    def test_real_directory_backup_and_uninstall_preserve_contents(self):
        target = self.profile / ".codex/skills/example"
        target.mkdir(parents=True)
        (target / "user.txt").write_text("user content")
        self.run_installer("-Only", "example", "-Target", "codex")
        backups = list((self.profile / ".codex").glob("skills.backup-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / "example/user.txt").read_text(), "user content")
        self.run_installer("-Only", "example", "-Target", "codex", "-Uninstall")
        self.assertFalse(target.exists())
        self.assertTrue((self.repo / "skills/example/SKILL.md").exists())
        self.assertTrue((backups[0] / "example/user.txt").exists())

    def test_shared_foreign_junction_replaced_without_deleting_source(self):
        shared = self.profile / "tools/shared"
        shared.parent.mkdir()
        command = f"New-Item -ItemType Junction -Path '{shared}' -Target '{self.external}' | Out-Null"
        subprocess.run([SHELL, "-NoProfile", "-Command", command], check=True, env=self.environment, capture_output=True)
        self.run_installer("-Only", "token-efficient-workflow", "-Target", "codex")
        self.assertEqual(shared.resolve(), (self.repo / "shared").resolve())
        self.assertTrue((self.external / "SKILL.md").exists())

    def test_external_source_equal_destination_is_preserved(self):
        target = self.profile / ".codex/skills/external-fixture"
        target.mkdir(parents=True)
        (target / "SKILL.md").write_text("original")
        self.environment["INSTALL_TEST_EXTERNAL"] = str(target)
        self.run_installer("-Only", "external-fixture", "-Target", "codex")
        self.assertFalse(target.is_junction())
        self.assertEqual((target / "SKILL.md").read_text(), "original")


if __name__ == "__main__":
    unittest.main()
