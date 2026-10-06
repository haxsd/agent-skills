"""使用真实临时目录和进程验证调度边界，不请求付费模型。"""
import importlib.util
import concurrent.futures
import os
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "delegate.py"
SPEC = importlib.util.spec_from_file_location("delegate", MODULE_PATH)
delegate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(delegate)


class DelegateTests(unittest.TestCase):
    """以下测试分别覆盖写入冲突、参数边界、完成状态和超时。"""

    def test_blocked_report_is_not_treated_as_completed(self):
        # CLI 可以正常退出但无法执行任务；不能仅依据退出码判成功。
        outcome = {"returncode": 0, "timed_out": False}
        self.assertEqual(delegate.classify_result(outcome, "TASK_STATUS: blocked\n工具被拒绝"), "blocked")
        self.assertEqual(delegate.classify_result(outcome, "普通回复"), "unverified")
        self.assertEqual(delegate.classify_result(outcome, "TASK_STATUS: completed\n完成"), "completed")
        self.assertEqual(delegate.classify_result({"returncode": 1, "timed_out": False},
                                                  "TASK_STATUS: completed\n完成"), "failed")

    def test_child_environment_drops_unrelated_credentials(self):
        # 未知密钥名称也不能泄漏，因此采用必要系统变量白名单。
        parent = {"PATH": "tools", "SystemRoot": "C:\\Windows", "GITHUB_TOKEN": "private",
                  "CUSTOM_PASSWORD": "private", "OPENAI_API_KEY": "private"}
        child = delegate.child_environment(parent, "deepseek-key", Path("runtime"))
        self.assertNotIn("GITHUB_TOKEN", child)
        self.assertNotIn("CUSTOM_PASSWORD", child)
        self.assertNotIn("OPENAI_API_KEY", child)
        self.assertEqual(child["DEEPSEEK_API_KEY"], "deepseek-key")
        self.assertEqual(child["PATH"], "tools")

    def test_nested_text_logs_are_redacted_without_rewriting_binary_files(self):
        # 对 runtime 下的文本日志递归处理，数据库不是文本，不能盲目重新编码。
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            nested = root / "runtime"
            nested.mkdir()
            (nested / "trace.log").write_text("echo dummy-secret", encoding="utf-8")
            (nested / "state.db").write_bytes(b"\xff\x00binary")
            delegate.clean_logs(root, "dummy-secret")
            self.assertNotIn("dummy-secret", (nested / "trace.log").read_text(encoding="utf-8"))
            self.assertEqual((nested / "state.db").read_bytes(), b"\xff\x00binary")

    def test_one_future_failure_is_reported_without_aborting_collection(self):
        # 模拟线程向调用方传播的实际异常，不把整批结果丢失。
        future = concurrent.futures.Future()
        future.set_exception(PermissionError("dummy-secret cannot write"))
        result = delegate.future_result(future, "one", "dummy-secret")
        self.assertEqual(result["status"], "failed")
        self.assertNotIn("dummy-secret", result["error"])

    @unittest.skipUnless(os.name == "nt", "taskkill 回退测试仅限 Windows")
    def test_timeout_still_kills_process_when_taskkill_is_unavailable(self):
        # 系统辅助命令不存在时也必须回退 kill，而不是留下运行中的任务。
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = os.environ["SystemRoot"]
            try:
                os.environ["SystemRoot"] = directory
                result = delegate.execute([sys.executable, "-c", "import time; time.sleep(30)"], "",
                                          os.environ.copy(), 0.2, root / "out", root / "err")
                self.assertTrue(result["timed_out"])
                self.assertIsNotNone(result["returncode"])
            finally:
                os.environ["SystemRoot"] = original

    def test_shared_read_only_workspace_is_allowed(self):
        # 两个只读子任务可以同时观察同一份源码。
        with tempfile.TemporaryDirectory() as directory:
            tasks = [{"id": name, "prompt": "分析", "workspace": directory}
                     for name in ("a", "b")]
            self.assertEqual(len(delegate.validate_manifest({"tasks": tasks})), 2)

    def test_overlapping_write_workspaces_are_rejected(self):
        # 父子目录也属于重叠范围，不能只比较字符串是否相等。
        with tempfile.TemporaryDirectory() as directory:
            child = Path(directory) / "nested"
            child.mkdir()
            tasks = [
                {"id": "a", "prompt": "修改", "workspace": directory,
                 "sandbox": "workspace-write"},
                {"id": "b", "prompt": "分析", "workspace": str(child)},
            ]
            with self.assertRaisesRegex(ValueError, "重叠"):
                delegate.validate_manifest({"tasks": tasks})

    def test_duplicate_ids_and_path_traversal_are_rejected(self):
        # ID 同时用于输出目录，路径穿越必须在启动前失败。
        with tempfile.TemporaryDirectory() as directory:
            for ids in (("same", "same"), ("../escape",)):
                tasks = [{"id": name, "prompt": "分析", "workspace": directory}
                         for name in ids]
                with self.assertRaises(ValueError):
                    delegate.validate_manifest({"tasks": tasks})

    def test_command_pins_deepseek_and_keeps_secrets_out_of_arguments(self):
        # Prompt 使用 stdin；密钥使用子进程环境；主代理配置不被修改。
        config = {"codex_executable": "codex.exe", "base_url": "https://api.deepseek.com"}
        task = {"workspace": ".", "sandbox": "read-only", "prompt": "a; $(danger)"}
        command = delegate.build_command(config, task, Path("result.md"))
        self.assertEqual(command[command.index("-m") + 1], "deepseek-flash")
        self.assertIn("--ignore-user-config", command)
        self.assertIn("read-only", command)
        self.assertEqual(command[-1], "-")
        self.assertNotIn(task["prompt"], command)
        self.assertFalse(any("Bearer " in item for item in command))

    def test_real_process_receives_unicode_stdin_and_reports_failure(self):
        # 使用实际 Python 进程，验证 UTF-8 输入、落盘和非零退出码。
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            command = [sys.executable, "-X", "utf8", "-c",
                       "import sys; print(sys.stdin.read()); sys.exit(7)"]
            result = delegate.execute(command, "中文任务", os.environ.copy(), 10,
                                      root / "out", root / "err")
            self.assertEqual(result["returncode"], 7)
            self.assertFalse(result["timed_out"])
            self.assertIn("中文任务", (root / "out").read_text(encoding="utf-8"))

    def test_timeout_terminates_process(self):
        # 一个持续睡眠的真实子进程不能使调度器永久阻塞。
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = delegate.execute(
                [sys.executable, "-c", "import time; time.sleep(30)"], "",
                os.environ.copy(), 0.2, root / "out", root / "err")
            self.assertTrue(result["timed_out"])
            self.assertIsNotNone(result["returncode"])

    @unittest.skipUnless(os.name == "nt", "DPAPI 仅用于 Windows")
    def test_dpapi_file_with_trailing_newline_can_be_decrypted(self):
        # PowerShell Set-Content 会追加换行；不能把换行交给十六进制解码器。
        with tempfile.TemporaryDirectory() as directory:
            original = delegate.KEY_FILE
            old_env = os.environ.pop("DEEPSEEK_API_KEY", None)
            try:
                delegate.KEY_FILE = Path(directory) / "key.dpapi"
                protected = delegate.protect_key("test-key-for-roundtrip")
                delegate.KEY_FILE.write_text(protected + "\n", encoding="ascii")
                self.assertEqual(delegate.load_key(), "test-key-for-roundtrip")
            finally:
                delegate.KEY_FILE = original
                if old_env is not None:
                    os.environ["DEEPSEEK_API_KEY"] = old_env


if __name__ == "__main__":
    unittest.main()
