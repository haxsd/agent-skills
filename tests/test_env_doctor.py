# SPDX-License-Identifier: MIT
"""CLI regression tests for skills/env-doctor/scripts/env_key_status.py.

Every test drives the tool as a real process and asserts its stdout JSON, its
exit code and the safety rules of the package: key names and states only, never
a value, never a raw line, never a file path, and never a silent read of a real
project .env.

Fixtures are written into temporary directories and use obvious fake canary
strings; nothing here reads or displays a real environment file.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL = REPO_ROOT / "skills" / "env-doctor" / "scripts" / "env_key_status.py"

CANARY_PASSWORD = "fixture-password-do-not-echo"
CANARY_TOKEN = "sk-env-doctor-canary-do-not-echo"
CANARY_LEAK = "sk-env-doctor-canary-leak-detector"

EXAMPLE_TEXT = "\n".join([
    "# 示例：只保留键名线索，不代表运行时必须齐全。",
    "DATABASE_URL=",
    "SESSION_SECRET=",
    "API_TOKEN=",
    "OPTIONAL_LABEL=",
    "LOG_LEVEL=info",
    "LEGACY_FLAG=",
    "",
])

ENV_TEXT = "\n".join([
    "export DATABASE_URL=postgresql://fixture-user:%s@localhost/example" % CANARY_PASSWORD,
    "SESSION_SECRET='%s'" % CANARY_TOKEN,
    "API_TOKEN=\"\"",
    "OPTIONAL_LABEL=",
    "LOG_LEVEL=info # 行尾注释",
    "",
])

PARTIAL_ENV_TEXT = "\n".join([
    "export SESSION_SECRET='%s'" % CANARY_TOKEN,
    "API_TOKEN=\"\"",
    "OPTIONAL_LABEL=",
    "LOG_LEVEL=info # 行尾注释",
    "",
])

CASE_ENV_TEXT = "\n".join([
    "port=3000",
    "PORT=8080",
    "",
])

GAP_ENV_TEXT = "\n".join([
    "LOG_ROOT=${HOME}/data",
    "SAFE_VALUE=ok",
    "",
])

CONTINUATION_ENV_TEXT = 'SESSION_SECRET="part-one\\\n'

UNTERMINATED_ENV_TEXT = "\n".join([
    "OPEN_QUOTED='first-part-with-no-closing-quote",
    "CANARY_SECRET_PART=%s" % CANARY_LEAK,
    "LATER_KEY=value",
    "",
])

TRAILING_TEXT_ENV = "OPEN_QUOTED='value' trailing text here\n"

ESCAPE_ENV_TEXT = "SESSION_SECRET=\"part\\npart\"\n"


def run_cli(*args):
    """Run the tool with the interpreter running this test suite."""
    completed = subprocess.run(
        [sys.executable, str(TOOL)] + [str(arg) for arg in args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=15,
    )
    return (
        completed.returncode,
        completed.stdout.decode("utf-8", errors="replace"),
        completed.stderr.decode("utf-8", errors="replace"),
    )


class EnvKeyStatusCliTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="env-doctor-tests-")
        self.base = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def fixture(self, name, content):
        path = self.base / name
        path.write_text(content, encoding="utf-8", newline="\n")
        return path

    def payload(self, out, err):
        self.assert_no_canary(out, err)
        try:
            return json.loads(out)
        except json.JSONDecodeError as error:
            self.fail("stdout is not JSON (%s); stderr=%r" % (error, err))

    def statuses(self, data):
        return {item["key"]: item["status"] for item in data["variables"]}

    def gap_reasons(self, data):
        return {gap["reason"] for gap in data["gaps"]}

    def assert_no_canary(self, out, err):
        for canary in (
            CANARY_PASSWORD,
            CANARY_TOKEN,
            CANARY_LEAK,
            "postgresql://",
            "fixture-user",
        ):
            self.assertNotIn(canary, out + err)
        normalized = (out + err).replace("\\\\", "\\").replace("\\", "/").casefold()
        self.assertNotIn(self.base.as_posix().casefold(), normalized)

    # ------------------------------------------------------- safety boundary

    def test_env_option_is_required(self):
        code, out, err = run_cli()

        self.assertEqual(2, code, "stdout=%r stderr=%r" % (out, err))
        self.assertIn("--env", err, "expected the argparse usage message")

    def test_symlink_to_dotenv_is_non_zero_and_leaks_nothing(self):
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks unavailable")
        target = self.fixture(".env", ENV_TEXT)
        link = self.base / "notes.txt"
        try:
            os.symlink(target, link)
        except (OSError, NotImplementedError):
            self.skipTest("cannot create symlink (privilege or filesystem)")

        code, out, err = run_cli("--env", link)

        self.assertNotEqual(0, code, "stdout=%r stderr=%r" % (out, err))
        self.assertEqual("symlink-path-refused", self.payload(out, err)["refusal"])
        self.assert_no_canary(out, err)

    # ------------------------------------------------------ key-state report

    def test_dotenv_and_example_compare_reports_keys_only(self):
        env_file = self.fixture(".env", ENV_TEXT)
        example = self.fixture(".env.example", EXAMPLE_TEXT)

        code, out, err = run_cli("--env", env_file, "--example", example)

        self.assertEqual(0, code, "stdout=%r stderr=%r" % (out, err))
        self.assertEqual("", err)
        data = self.payload(out, err)
        self.assertEqual(1, data["schemaVersion"])
        self.assertEqual("ok", data["status"])
        self.assertEqual("compare", data["mode"])
        self.assertEqual(
            {
                "DATABASE_URL": "present",
                "SESSION_SECRET": "present",
                "API_TOKEN": "empty",
                "OPTIONAL_LABEL": "empty",
                "LOG_LEVEL": "present",
                "LEGACY_FLAG": "missing",
            },
            self.statuses(data),
        )
        self.assertEqual([], data["gaps"])
        self.assert_no_canary(out, err)

    def test_example_declared_key_not_seen_in_env_is_missing_not_an_error(self):
        env_file = self.fixture(".env", PARTIAL_ENV_TEXT)
        example = self.fixture(".env.example", EXAMPLE_TEXT)

        code, out, err = run_cli("--env", env_file, "--example", example)

        self.assertEqual(0, code, "stdout=%r stderr=%r" % (out, err))
        data = self.payload(out, err)
        statuses = self.statuses(data)
        self.assertEqual("missing", statuses["DATABASE_URL"])
        self.assertEqual("present", statuses["SESSION_SECRET"])
        self.assertEqual("empty", statuses["API_TOKEN"])
        self.assertIsNone(data.get("refusal"))

    def test_key_case_is_preserved(self):
        env_file = self.fixture(".env", CASE_ENV_TEXT)

        code, out, err = run_cli("--env", env_file)

        self.assertEqual(0, code, "stdout=%r stderr=%r" % (out, err))
        data = self.payload(out, err)
        self.assertEqual(["PORT", "port"], sorted(item["key"] for item in data["variables"]))
        self.assertEqual({"PORT": "present", "port": "present"}, self.statuses(data))

    # --------------------------------------------- unsupported syntax honesty

    def test_unquoted_interpolation_is_gap_and_stops_later_lines(self):
        env_file = self.fixture(".env", GAP_ENV_TEXT)

        code, out, err = run_cli("--env", env_file)

        self.assertEqual(1, code, "stdout=%r stderr=%r" % (out, err))
        data = self.payload(out, err)
        self.assertEqual("incomplete", data["status"])
        self.assertIn("unsupported-interpolation", self.gap_reasons(data))
        self.assertEqual("unknown", self.statuses(data)["LOG_ROOT"])
        self.assertNotIn("SAFE_VALUE", self.statuses(data))

    def test_line_continuation_is_gap(self):
        env_file = self.fixture(".env", CONTINUATION_ENV_TEXT)

        code, out, err = run_cli("--env", env_file)

        self.assertEqual(1, code, "stdout=%r stderr=%r" % (out, err))
        data = self.payload(out, err)
        self.assertEqual("incomplete", data["status"])
        self.assertIn("line-continuation", self.gap_reasons(data))
        self.assertEqual("unknown", self.statuses(data)["SESSION_SECRET"])

    def test_inner_lines_of_unsupported_multiline_are_not_keys(self):
        env_file = self.fixture(".env", UNTERMINATED_ENV_TEXT)

        code, out, err = run_cli("--env", env_file)

        self.assertEqual(1, code, "stdout=%r stderr=%r" % (out, err))
        data = self.payload(out, err)
        self.assertIn("unterminated-quote", self.gap_reasons(data))
        listed = " ".join(item["key"] for item in data["variables"])
        self.assertNotIn("CANARY_SECRET_PART", listed)
        self.assertNotIn("LATER_KEY", listed)
        self.assert_no_canary(out, err)

    def test_gaps_in_one_file_make_unseen_example_keys_unknown(self):
        env_file = self.fixture(".env", GAP_ENV_TEXT)
        example = self.fixture(".env.example", EXAMPLE_TEXT)

        code, out, err = run_cli("--env", env_file, "--example", example)

        self.assertEqual(1, code, "stdout=%r stderr=%r" % (out, err))
        data = self.payload(out, err)
        statuses = self.statuses(data)
        self.assertEqual("unknown", statuses["DATABASE_URL"])

    def test_trailing_text_after_quoted_value_is_gap(self):
        env_file = self.fixture(".env", TRAILING_TEXT_ENV)

        code, out, err = run_cli("--env", env_file)

        self.assertEqual(1, code, "stdout=%r stderr=%r" % (out, err))
        data = self.payload(out, err)
        self.assertIn("quoted-value-trailing-text", self.gap_reasons(data))
        self.assertEqual("unknown", self.statuses(data)["OPEN_QUOTED"])

    def test_escape_sequences_are_not_treated_as_verified_values(self):
        env_file = self.fixture(".env", ESCAPE_ENV_TEXT)

        code, out, err = run_cli("--env", env_file)

        self.assertEqual(1, code, "stdout=%r stderr=%r" % (out, err))
        data = self.payload(out, err)
        self.assertIn("escape-not-interpreted", self.gap_reasons(data))
        self.assertEqual("unknown", self.statuses(data)["SESSION_SECRET"])

    def test_any_env_parse_gap_keeps_unseen_example_keys_unknown(self):
        env_file = self.fixture(".env", "OTHER=\"${UNRESOLVED}\"\n")
        example = self.fixture(".env.example", "DATABASE_URL=\n")
        code, out, err = run_cli("--env", env_file, "--example", example)
        data = self.payload(out, err)
        self.assertEqual(1, code)
        self.assertEqual("unknown", self.statuses(data)["DATABASE_URL"])

    def test_nul_content_is_refused_without_leaking_values(self):
        env_file = self.base / ".env"
        env_file.write_bytes(b"KEY=placeholder\x00" + CANARY_TOKEN.encode("ascii"))
        code, out, err = run_cli("--env", env_file)
        data = self.payload(out, err)
        self.assertEqual(1, code)
        self.assertEqual([], data["variables"])
        self.assertNotIn(CANARY_TOKEN, out + err)

    @unittest.skipUnless(os.name == "posix" and hasattr(os, "mkfifo"), "POSIX FIFO")
    def test_fifo_is_rejected_before_open(self):
        fifo = self.base / "input-fifo"
        os.mkfifo(fifo)
        code, out, err = run_cli("--env", fifo)
        self.assertEqual(1, code)
        self.assertEqual("file-not-regular", self.payload(out, err)["gaps"][0]["reason"])

    @unittest.skipUnless(os.name == "nt", "Windows junction parent")
    def test_junction_parent_is_refused(self):
        shell = os.environ.get("TEST_POWERSHELL")
        if not shell or not os.path.isabs(shell):
            self.skipTest("requires an explicitly selected PowerShell path")
        target = self.base / "junction-target"
        target.mkdir()
        (target / ".env").write_text(ENV_TEXT, encoding="utf-8")
        link = self.base / "junction-parent"
        quoted_link = str(link).replace("'", "''")
        quoted_target = str(target).replace("'", "''")
        command = (f"New-Item -ItemType Junction -Path '{quoted_link}' "
                   f"-Target '{quoted_target}' -ErrorAction Stop | Out-Null")
        created = subprocess.run([shell, "-NoProfile", "-NonInteractive", "-Command", command],
                                 capture_output=True, check=False, timeout=15)
        if created.returncode:
            self.skipTest("cannot create a junction")
        try:
            self.assertFalse(link.is_symlink())
            code, out, err = run_cli("--env", link / ".env")
            self.assertEqual(1, code)
            data = self.payload(out, err)
            self.assertEqual("symlink-path-refused", data["refusal"])
            self.assertNotIn(CANARY_TOKEN, out + err)
        finally:
            os.rmdir(link)

    def test_notes_stay_honest_about_what_the_files_cannot_show(self):
        env_file = self.fixture(".env", ENV_TEXT)
        example = self.fixture(".env.example", EXAMPLE_TEXT)

        code, out, err = run_cli("--env", env_file, "--example", example)

        self.assertEqual(0, code, "stdout=%r stderr=%r" % (out, err))
        data = self.payload(out, err)
        notes = " ".join(data["notes"])
        self.assertIn("进程", notes)
        self.assertIn("插值", notes)

    # ---------------------------------------------------- file-level refusals

    def test_oversize_file_is_refused_statically(self):
        filler = "x" * (1024 * 1024 + 1)
        env_file = self.fixture(".env", "BIG=%s\n" % filler)

        code, out, err = run_cli("--env", env_file)

        self.assertEqual(1, code, "stdout=%r stderr=%r" % (out, err))
        data = self.payload(out, err)
        self.assertEqual("incomplete", data["status"])
        self.assertIn("file-too-large", self.gap_reasons(data))

    def test_binary_file_is_refused_statically(self):
        path = self.base / ".env"
        path.write_bytes(b"\xff\xfe\x00BINARY\x00\xff")

        code, out, err = run_cli("--env", path)

        self.assertEqual(1, code, "stdout=%r stderr=%r" % (out, err))
        data = self.payload(out, err)
        self.assertIn("binary-encoding-unsupported", self.gap_reasons(data))
        self.assertNotIn("BINARY", out + err)

    def test_directory_path_is_refused_statically(self):
        code, out, err = run_cli("--env", self.base)

        self.assertEqual(1, code, "stdout=%r stderr=%r" % (out, err))
        data = self.payload(out, err)
        self.assertIn("file-not-regular", self.gap_reasons(data))


if __name__ == "__main__":
    unittest.main()
