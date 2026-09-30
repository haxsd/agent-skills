"""Scoped-execution invariants, with fake API turns and real local checks."""
from contextlib import redirect_stdout, redirect_stderr
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/deepseek-subagent-orchestration/scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


w, runtime = load("deepseek_worker"), load("agent_runtime")
HANDOFF = {"summary": "done", "evidence": [], "suggestions": [], "unknowns": []}


def turn(name, arguments, *, reason="tool_calls", model="deepseek-flash"):
    message = {"content": None, "tool_calls": [{"id": "call1", "type": "function",
               "function": {"name": name, "arguments": json.dumps(arguments)}}], "reasoning_content": "internal thought"}
    return {"model": model, "choices": [{"message": message, "finish_reason": reason}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}}


class FakeClient:
    key = "fixture-credential"

    def __init__(self, turns):
        self.turns, self.requests = list(turns), []

    def tools_chat(self, messages, tools, max_tokens, thinking):
        self.requests.append(json.loads(json.dumps(messages)))
        return self.turns.pop(0)


class TestRuntime(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "source"
        self.root.mkdir()
        (self.root / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
        self.output = Path(self.temp.name) / "out"
        self.doc = {"jobs": [{"id": "implement", "task": "Set VALUE to 2", "acceptance": "VALUE=2",
                             "files": ["module.py"], "writable": ["module.py"], "checks": []}]}
        self.options = SimpleNamespace(max_rounds=6, max_total_tokens=48000, max_input_chars=96000, thinking="disabled")

    def tearDown(self):
        self.temp.cleanup()

    def prepare(self):
        jobs = runtime.prepare_jobs(self.doc, self.root, FakeClient.key, w)
        runtime.create_workspaces(jobs, self.output, FakeClient.key, w)
        return jobs[0]

    def run_job(self, turns, job=None):
        self.client = FakeClient(turns)
        return runtime.run_job(self.client, job or self.prepare(), 4096, self.options, w)

    def test_multiturn_write_handoff_isolated_and_usage(self):
        record = self.run_job([turn("write_file", {"path": "module.py", "content": "VALUE = 2\n"}), turn("finish", HANDOFF)])
        self.assertEqual(record["status"], "completed")
        self.assertEqual(record["modified_files"], ["module.py"])
        self.assertEqual(record["usage"]["total_tokens"], 300)
        self.assertEqual((self.root / "module.py").read_text(), "VALUE = 1\n")
        self.assertEqual((Path(record["workspace"]) / "module.py").read_text(), "VALUE = 2\n")
        self.assertEqual(self.client.requests[1][-1]["role"], "tool")

    def test_real_named_check_gets_no_credentials(self):
        code = "import os; assert 'DEEPSEEK_API_KEY' not in os.environ; assert 'OTHER_TOKEN' not in os.environ; from module import VALUE; assert VALUE == 2; print('verified')"
        self.doc["jobs"][0]["checks"] = [{"name": "verify", "argv": [sys.executable, "-c", code]}]
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "do-not-inherit", "OTHER_TOKEN": "also-private"}):
            record = self.run_job([turn("write_file", {"path": "module.py", "content": "VALUE = 2\n"}),
                                   turn("run_check", {"name": "verify"}), turn("finish", HANDOFF)])
        self.assertEqual(record["status"], "completed")
        self.assertEqual(record["checks"][0]["exit_code"], 0)
        self.assertIn("verified", record["checks"][0]["output"])

    def test_unknown_check_and_outside_writes_have_no_effect(self):
        record = self.run_job([turn("write_file", {"path": "../escape.txt", "content": "bad"}),
                               turn("write_file", {"path": "other.py", "content": "bad"}),
                               turn("run_check", {"name": "unauthorized"}), turn("finish", HANDOFF)])
        self.assertEqual(record["modified_files"], [])
        self.assertEqual(len([x for x in record["tools"] if "error" in x]), 3)
        self.assertFalse((Path(self.temp.name) / "escape.txt").exists())

    def test_secret_source_preflight_before_api(self):
        (self.root / "module.py").write_text("credential=" + FakeClient.key)
        with self.assertRaises(w.WorkerError):
            self.prepare()

    def test_credential_paths_and_portable_traversal_rejected(self):
        for path in (".env", ".codex/auth.json", "../module.py", "C:/file", "a\\b", "con.txt", "dir//file", "file."):
            with self.subTest(path=path), self.assertRaises(w.WorkerError):
                runtime.relative_path(path, w)

    def test_file_directory_collisions_and_case_alias_rejected(self):
        for writes in (["MODULE.py"], ["module.py/child"]):
            self.doc["jobs"][0]["writable"] = writes
            with self.assertRaises(w.WorkerError):
                runtime.prepare_jobs(self.doc, self.root, FakeClient.key, w)

    def test_symlink_source_escape_rejected(self):
        outside = Path(self.temp.name) / "outside.txt"
        outside.write_text("not context")
        try:
            (self.root / "link.txt").symlink_to(outside)
        except OSError:
            self.skipTest("Symlink creation unavailable")
        self.doc["jobs"][0]["files"] = ["link.txt"]
        with self.assertRaises(w.WorkerError):
            self.prepare()

    def test_toolargument_types_do_not_mutate_files(self):
        record = self.run_job([turn("write_file", {"path": "module.py", "content": 2}), turn("finish", HANDOFF)])
        self.assertEqual(record["modified_files"], [])
        self.assertIn("error", record["tools"][0])

    def test_truncation_never_executes_partial_tools(self):
        record = self.run_job([turn("write_file", {"path": "module.py", "content": "bad"}, reason="length")])
        self.assertEqual(record["status"], "error")
        self.assertEqual(record["modified_files"], [])
        self.assertEqual(record["rounds"], 1)

    def test_wrong_model_never_executes_tools(self):
        record = self.run_job([turn("write_file", {"path": "module.py", "content": "bad"}, model="other")])
        self.assertEqual(record["status"], "error")
        self.assertEqual(record["modified_files"], [])

    def test_limits_terminate_without_retry(self):
        self.options.max_rounds = 1
        record = self.run_job([turn("list_files", {})])
        self.assertEqual(record["status"], "incomplete")
        self.assertEqual(record["rounds"], 1)

    def test_budget_preflight_makes_no_call(self):
        self.options.max_total_tokens = 256
        record = self.run_job([])
        self.assertEqual(record["status"], "error")
        self.assertEqual(self.client.requests, [])

    def test_thinking_history_preserved_but_not_in_result(self):
        self.options.thinking = "enabled"
        record = self.run_job([turn("list_files", {}), turn("finish", HANDOFF)])
        self.assertEqual(self.client.requests[1][-2]["reasoning_content"], "internal thought")
        self.assertNotIn("internal thought", json.dumps(record))

    def test_check_modifying_unowned_path_blocks_integration(self):
        self.doc["jobs"][0]["checks"] = [{"name": "bad-check", "argv": [sys.executable, "-c", "from pathlib import Path; Path('unowned.txt').write_text('unexpected')"]}]
        record = self.run_job([turn("run_check", {"name": "bad-check"}), turn("finish", HANDOFF)])
        self.assertEqual(record["status"], "error")
        self.assertIn("unowned.txt", record["modified_files"])

    def test_timeout_records_real_failed_check(self):
        self.doc["jobs"][0]["checks"] = [{"name": "slow", "argv": [sys.executable, "-c", "import time; time.sleep(5)"], "timeout": 1}]
        record = self.run_job([turn("run_check", {"name": "slow"}), turn("finish", HANDOFF)])
        self.assertTrue(record["checks"][0]["timed_out"])
        self.assertNotEqual(record["checks"][0]["exit_code"], 0)

    def test_search_and_numbered_reads(self):
        record = self.run_job([turn("search", {"text": "value"}), turn("read_file", {"path": "module.py"}), turn("finish", HANDOFF)])
        self.assertEqual(record["tools"][0]["result"]["matches"][0]["line"], 1)
        self.assertEqual(record["tools"][1]["result"]["lines"], ["1: VALUE = 1"])

    def test_long_reads_paginate_without_aborting_job(self):
        (self.root / "module.py").write_text(("# " + "longline" * 12 + "\n") * 400)
        record = self.run_job([turn("read_file", {"path": "module.py"}), turn("finish", HANDOFF)])
        self.assertEqual(record["status"], "completed")
        result = record["tools"][0]["result"]
        self.assertLess(result["next_line"], 300)
        self.assertLess(len(json.dumps(result)), 16000)

    def test_secret_in_path_never_enters_manifest(self):
        self.doc["jobs"][0]["writable"] = [FakeClient.key + ".txt"]
        with self.assertRaises(w.WorkerError):
            self.prepare()

    def test_parallel_jobs_cannot_own_the_same_integration_path(self):
        self.doc["jobs"].append(dict(self.doc["jobs"][0], id="second"))
        with self.assertRaises(w.WorkerError):
            self.prepare()

    def test_cli_execute_creates_artifacts_and_refuses_overwrite(self):
        jobs, config = Path(self.temp.name) / "jobs.json", Path(self.temp.name) / "config.json"
        w.write_json(jobs, self.doc)
        w.write_json(config, {})
        client = FakeClient([turn("finish", HANDOFF)])
        args = ["--config", str(config), "execute", "--jobs", str(jobs), "--root", str(self.root), "--out-dir", str(self.output)]
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": client.key}), patch.object(w, "Client", return_value=client), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(w.main(args), 0)
            self.assertEqual(w.main(args), 2)
        self.assertEqual(w.read_json(self.output / "implement.json")["mode"], "execute")


if __name__ == "__main__":
    unittest.main()
