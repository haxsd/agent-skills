# SPDX-License-Identifier: Apache-2.0
"""Offline tests for skills/gh-fix-ci/scripts/inspect_ci_failures.py.

`gh` is never invoked: run_gh_command is replaced with canned responses, so the
tests cover run selection, job expansion and snippet windows without network.
"""

import importlib.util
import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL = REPO_ROOT / "skills" / "gh-fix-ci" / "scripts" / "inspect_ci_failures.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("inspect_ci_failures", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeGh:
    def __init__(self, module, responses):
        self.module = module
        self.responses = responses
        self.calls = []

    def __call__(self, args, cwd):
        self.calls.append(list(args))
        for prefix, payload in self.responses:
            if list(args[:len(prefix)]) == prefix:
                return self.module.GhResult(0, json.dumps(payload), "")
        return self.module.GhResult(1, "", "unexpected gh call: " + " ".join(args))


class InspectCiFailuresTest(unittest.TestCase):
    def setUp(self):
        self.tool = load_tool()
        self.original = self.tool.run_gh_command

    def tearDown(self):
        self.tool.run_gh_command = self.original

    def test_branch_mode_reports_only_latest_completed_run_per_workflow(self):
        runs = [
            {"databaseId": 3, "workflowName": "CI", "status": "completed",
             "conclusion": "success", "createdAt": "2026-11-02T10:00:00Z"},
            {"databaseId": 2, "workflowName": "CI", "status": "completed",
             "conclusion": "failure", "createdAt": "2026-11-02T09:00:00Z"},
            {"databaseId": 5, "workflowName": "Docs", "status": "in_progress",
             "conclusion": "", "createdAt": "2026-11-02T11:00:00Z"},
            {"databaseId": 4, "workflowName": "Docs", "status": "completed",
             "conclusion": "failure", "createdAt": "2026-11-02T08:00:00Z"},
        ]
        self.tool.run_gh_command = FakeGh(self.tool, [(["run", "list"], runs)])
        self.assertEqual(self.tool.latest_failed_runs("main", Path(".")), ["4"])

    def test_run_mode_expands_jobs_into_checks(self):
        payload = {"url": "https://github.com/o/r/actions/runs/9", "jobs": [
            {"name": "test (ubuntu)", "status": "completed", "conclusion": "failure",
             "url": "https://github.com/o/r/actions/runs/9/job/11"},
            {"name": "test (windows)", "status": "completed", "conclusion": "success",
             "url": "https://github.com/o/r/actions/runs/9/job/12"},
        ]}
        self.tool.run_gh_command = FakeGh(self.tool, [(["run", "view", "9"], payload)])
        checks = self.tool.run_checks(["9"], Path("."))
        failing = [c for c in checks if self.tool.is_failing(c)]
        self.assertEqual([c["name"] for c in failing], ["test (ubuntu)"])
        self.assertEqual(self.tool.extract_job_id(failing[0]["detailsUrl"]), "11")

    def test_runner_error_line_keeps_cause_and_drops_cleanup(self):
        log = "\n".join(["setup"] * 5 + ["Traceback (most recent call last):",
                                          "ValueError: boom", "FAILED (failures=1)",
                                          "##[error]Process completed with exit code 1.",
                                          "Post job cleanup.", "git config --unset-all extraheader"])
        snippet = self.tool.extract_failure_snippet(log, max_lines=50, context=3)
        self.assertIn("ValueError: boom", snippet)
        self.assertTrue(snippet.endswith("exit code 1."))
        self.assertNotIn("Post job cleanup", snippet)

    def test_display_target(self):
        self.assertEqual(self.tool.display_target("12"), "PR #12")
        self.assertEqual(self.tool.display_target("Branch main"), "Branch main")


if __name__ == "__main__":
    unittest.main()
