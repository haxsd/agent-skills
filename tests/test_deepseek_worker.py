"""Offline behavior checks for the API assistant; no paid calls or real keys."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stderr, redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import http.client
import io
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "skills/deepseek-subagent-orchestration/scripts/deepseek_worker.py"
spec = importlib.util.spec_from_file_location("deepseek_worker", SOURCE)
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


class Handler(BaseHTTPRequestHandler):
    seen = []
    status = 200
    finish_reason = "stop"
    content = {"summary": "done", "evidence": ["sample.txt:2: beta"], "suggestions": [], "unknowns": []}
    model = "deepseek-flash"
    active = 0
    maximum_active = 0
    lock = threading.Lock()

    def log_message(self, *args):
        pass

    def do_POST(self):
        data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        with self.lock:
            type(self).seen.append((self.path, data, self.headers.get("Authorization")))
            type(self).active += 1
            type(self).maximum_active = max(self.maximum_active, self.active)
        time.sleep(0.03)
        self.send_response(self.status)
        self.end_headers()
        response = {"model": self.model, "choices": [{"finish_reason": self.finish_reason,
                    "message": {"content": json.dumps(self.content)}}],
                    "usage": {"prompt_tokens": 50, "completion_tokens": 10, "total_tokens": 60}}
        self.wfile.write(json.dumps(response).encode())
        with self.lock:
            type(self).active -= 1


class TestWorker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        Handler.seen = []
        Handler.status, Handler.finish_reason, Handler.model = 200, "stop", "deepseek-flash"
        Handler.content = {"summary": "done", "evidence": ["sample.txt:2: beta"], "suggestions": [], "unknowns": []}
        Handler.maximum_active = 0
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "sample.txt").write_text("alpha\nbeta\ngamma\n", encoding="utf-8")
        self.client = worker.Client(f"http://127.0.0.1:{self.server.server_port}", "test-credential", 2)
        self.doc = {"jobs": [{"id": "review", "task": "Find beta", "acceptance": "Cite its line",
                              "files": [{"path": "sample.txt", "start_line": 2, "end_line": 2}]}]}

    def tearDown(self):
        self.temp.cleanup()

    def prepared(self):
        return worker.prepare_jobs(self.doc, self.root, self.client.key)

    def test_real_http_contract_and_line_excerpt(self):
        self.doc["jobs"][0]["context"] = "Use ask-questions-if-underspecified only when needed."
        job = self.prepared()[0]
        self.assertIn("2: beta", job["prompt"])
        self.assertNotIn("alpha", job["prompt"])
        result = worker.run_job(self.client, job, 128)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["usage"]["total_tokens"], 60)
        endpoint, payload, auth = Handler.seen[0]
        self.assertEqual(endpoint, "/chat/completions")
        self.assertEqual(auth, "Bearer test-credential")
        self.assertEqual(payload["model"], "deepseek-flash")
        self.assertEqual(payload["thinking"], {"type": "disabled"})
        self.assertEqual(payload["max_tokens"], 128)
        self.assertNotIn("tools", payload)
        self.assertEqual((self.root / "sample.txt").read_text(), "alpha\nbeta\ngamma\n")

    def test_preflight_rejects_paths_secrets_ranges_and_duplicate_ids(self):
        cases = []
        base = self.doc["jobs"][0]
        cases.append({"jobs": [base, base]})
        cases.append({"jobs": [base | {"id": "summary"}]})
        cases.append({"jobs": [base | {"id": "CON"}]})
        cases.append({"jobs": [base | {"context": "test-credential"}]})
        cases.append({"jobs": [base | {"context": "sk-" + "x" * 32}]})
        cases.append({"jobs": [base | {"files": [{"path": "sample.txt", "start_line": 5}]}]})
        cases.append({"jobs": [base | {"files": [str(self.root / "sample.txt")]}]})
        outside = self.root.parent / (self.root.name + "-outside.txt")
        outside.write_text("outside")
        cases.append({"jobs": [base | {"files": ["../" + outside.name]}]})
        (self.root / ".env.local").write_text("harmless fixture")
        cases.append({"jobs": [base | {"files": [".env.local"]}]})
        try:
            for doc in cases:
                with self.subTest(doc=doc), self.assertRaises(worker.WorkerError):
                    worker.prepare_jobs(doc, self.root, self.client.key)
            with self.assertRaises(worker.WorkerError):
                worker.prepare_jobs(self.doc, self.root, self.client.key, max_input=10)
            with self.assertRaises(worker.WorkerError):
                worker.prepare_jobs(self.doc, self.root, self.client.key, max_batch=10)
            self.assertEqual(Handler.seen, [])
        finally:
            outside.unlink()

    def test_malformed_and_truncated_results_are_not_completed(self):
        Handler.finish_reason = "length"
        self.assertEqual(worker.run_job(self.client, self.prepared()[0], 128)["status"], "incomplete")
        Handler.finish_reason = "stop"
        Handler.content = {"summary": "not enough fields"}
        self.assertEqual(worker.run_job(self.client, self.prepared()[0], 128)["status"], "error")

    def test_http_failure_never_retries_or_exposes_body(self):
        Handler.status = 401
        Handler.content = {"summary": "test-credential"}
        result = worker.run_job(self.client, self.prepared()[0], 128)
        self.assertEqual(result["status"], "error")
        self.assertIn("HTTP 401", result["error"])
        self.assertNotIn("test-credential", json.dumps(result))
        self.assertEqual(len(Handler.seen), 1)
        with patch.object(self.client.opener, "open", side_effect=http.client.IncompleteRead(b"test-credential", 50)):
            interrupted = worker.run_job(self.client, self.prepared()[0], 128)
        self.assertEqual(interrupted["status"], "error")
        self.assertNotIn("test-credential", json.dumps(interrupted))

    def test_auth_failure_stops_jobs_that_have_not_started(self):
        Handler.status = 403
        prepared = [self.prepared()[0] | {"id": str(i)} for i in range(6)]
        results = worker.run_batch(self.client, prepared, 128, 2)
        self.assertEqual(len(Handler.seen), 2)
        self.assertEqual([r["status"] for r in results], ["error", "error", "skipped", "skipped", "skipped", "skipped"])

    def test_other_deepseek_models_are_rejected(self):
        Handler.model = "deepseek-v4-pro"
        self.assertEqual(worker.run_job(self.client, self.prepared()[0], 128)["status"], "error")

    def test_redirect_never_forwards_authorization(self):
        with self.assertRaises(worker.WorkerError):
            worker.NoRedirect().redirect_request(None, None, 302, "move", {}, "https://other.test")

    def test_concurrent_calls_and_usage_are_independent(self):
        job = self.prepared()[0]
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: worker.run_job(self.client, job, 128), range(2)))
        self.assertEqual(Handler.maximum_active, 2)
        self.assertTrue(all(r["status"] == "completed" for r in results))

    def test_config_rejects_plaintext_keys_and_substitution(self):
        config = self.root / "config.json"
        for content in ({"api_key": "anything"}, {"model": "another-model"},
                        {"base_url": "http://api.deepseek.com"},
                        {"base_url": "https://api.deepseek.com?key=oops"}):
            worker.write_json(config, content)
            with self.subTest(content=content), self.assertRaises(worker.WorkerError):
                worker.load_config(config)
        worker.write_json(config, {})
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-env-credential"}):
            base, key, source = worker.load_config(config)
        self.assertEqual((base, key, source), ("https://api.deepseek.com", "test-env-credential", "environment"))

    @unittest.skipUnless(os.name == "nt", "Windows DPAPI")
    def test_dpapi_round_trip_is_not_plaintext(self):
        original = b"non-secret-fixture"
        encrypted = worker.dpapi(original)
        self.assertNotIn(original, encrypted)
        self.assertEqual(worker.dpapi(encrypted, decrypt=True), original)

    def test_cli_batch_writes_handoffs_and_rejects_existing_output(self):
        jobs_file, config, output = self.root / "jobs.json", self.root / "config.json", self.root / "out"
        worker.write_json(jobs_file, self.doc)
        worker.write_json(config, {})
        args = ["--config", str(config), "run", "--jobs", str(jobs_file), "--root", str(self.root), "--out-dir", str(output)]
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-credential"}), \
                patch.object(worker, "Client", return_value=self.client), \
                redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(worker.main(args), 0)
            self.assertEqual(worker.main(args), 2)
        self.assertEqual(worker.read_json(output / "summary.json")["jobs"][0]["status"], "completed")
        self.assertTrue((output / "review.json").exists())
        self.assertEqual(len(Handler.seen), 1)


if __name__ == "__main__":
    unittest.main()
