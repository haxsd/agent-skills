"""启动真实 Codex/DeepSeek 子代理；仅用 Python 标准库，无额外安装依赖。

主代理负责准备任务清单、隔离工作区和验收；本脚本负责凭据、进程和日志。
不会修改主代理的 model/provider 配置，也不会调用内置 GPT spawn_agent。
"""
import argparse
import concurrent.futures
import ctypes
import getpass
import json
import os
import re
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

MODEL = "deepseek-flash"
MODEL_NAME = "DeepSeek-V4.1-Flash"
CONFIG = Path.home() / ".codex" / "deepseek-subagents.json"
KEY_FILE = Path.home() / ".codex" / "credentials" / "deepseek-subagents.key.dpapi"


def validate_manifest(manifest):
    """在启动任何进程前检查任务、目录、ID 和并行读写冲突。"""
    tasks = manifest.get("tasks")
    if not isinstance(tasks, list) or not 1 <= len(tasks) <= 24:
        raise ValueError("tasks 必须包含 1 至 24 个子任务")
    seen, checked = set(), []
    for source in tasks:
        task = dict(source)
        task_id = task.get("id", "")
        if not isinstance(task_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", task_id):
            raise ValueError("任务 ID 必须为安全的小写字母、数字、短横线或下划线")
        if task_id in seen:
            raise ValueError("任务 ID 不可重复")
        seen.add(task_id)
        if not isinstance(task.get("prompt"), str) or not task["prompt"].strip():
            raise ValueError("每个任务必须有非空 prompt")
        if not task.get("workspace"):
            raise ValueError("每个任务必须指定 workspace")
        workspace = Path(task["workspace"]).resolve(strict=True)
        if not workspace.is_dir():
            raise ValueError("workspace 必须是已经存在的目录")
        task["workspace"] = str(workspace)
        task.setdefault("sandbox", "read-only")
        if task["sandbox"] not in ("read-only", "workspace-write"):
            raise ValueError("只允许 read-only 或 workspace-write")
        timeout = task.get("timeout_sec", 600)
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 10 <= timeout <= 1800:
            raise ValueError("timeout_sec 必须介于 10 与 1800 秒")
        task["timeout_sec"] = timeout
        for previous in checked:
            other = Path(previous["workspace"])
            overlap = workspace.is_relative_to(other) or other.is_relative_to(workspace)
            if overlap and "workspace-write" in (task["sandbox"], previous["sandbox"]):
                raise ValueError("任务工作区重叠：写任务必须使用独立目录或独立 worktree")
        checked.append(task)
    return checked


def build_command(config, task, result_path):
    """使用参数列表而非 shell 字符串；prompt 和密钥均不进入命令行。"""
    overrides = {
        "approval_policy": "never",
        "model_provider": "deepseek-subagent",
        "model_providers.deepseek-subagent.name": "DeepSeek",
        "model_providers.deepseek-subagent.base_url": config.get("base_url", "https://api.deepseek.com"),
        "model_providers.deepseek-subagent.env_key": "DEEPSEEK_API_KEY",
        "model_providers.deepseek-subagent.wire_api": "responses",
        "model_providers.deepseek-subagent.request_max_retries": 2,
        "model_providers.deepseek-subagent.stream_max_retries": 1,
        "model_reasoning_effort": "high",
        # 模型调用需要密钥，但其执行的终端命令不需要；排除传递给终端工具。
        "shell_environment_policy.exclude": ["DEEPSEEK_API_KEY"],
        "shell_environment_policy.set.DEEPSEEK_SUBAGENT": "1",
        "features.multi_agent": False,
        "web_search": "disabled",
    }
    if os.name == "nt":
        # 独立 CODEX_HOME 不继承桌面配置，必须显式启用原生受限沙箱。
        overrides["windows.sandbox"] = "unelevated"
    command = [config["codex_executable"], "exec", "--ignore-user-config",
               "--skip-git-repo-check", "--ephemeral", "--json", "--color", "never",
               "-C", task["workspace"], "--sandbox", task.get("sandbox", "read-only")]
    for key, value in overrides.items():
        # JSON 的字符串/数组/布尔值语法也是这些 TOML 配置值的合法语法。
        command.extend(["-c", key + "=" + json.dumps(value, ensure_ascii=False)])
    command.extend(["-m", MODEL, "-o", str(result_path), "-"])
    return command


def execute(command, prompt, env, timeout, stdout_path, stderr_path):
    """日志直接写文件，避免管道填满；超时后结束整个工具进程树。"""
    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    with open(stdout_path, "wb") as output, open(stderr_path, "wb") as errors:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=output, stderr=errors,
                                   env=env, creationflags=creationflags,
                                   start_new_session=(os.name != "nt"))
        timed_out = False
        try:
            process.communicate(prompt.encode("utf-8"), timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            timed_out = True
            try:
                if os.name == "nt":
                    # 按持有的 PID 结束进程树；辅助命令异常时仍必须执行 kill 回退。
                    taskkill = Path(os.environ["SystemRoot"]) / "System32" / "taskkill.exe"
                    subprocess.run([str(taskkill), "/PID", str(process.pid), "/T", "/F"],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   creationflags=subprocess.CREATE_NO_WINDOW, timeout=15)
                else:
                    os.killpg(process.pid, signal.SIGKILL)
            except (OSError, subprocess.SubprocessError):
                pass
            finally:
                if process.poll() is None:
                    process.kill()
                # 二次等待也有上限，不能在超时清理阶段无限阻塞。
                process.communicate(timeout=10)
    return {"returncode": process.returncode, "timed_out": timed_out}


def dpapi(data, encrypt=False):
    """直接调用 Windows DPAPI；不依赖不同版本 PowerShell 的模块加载行为。"""
    if os.name != "nt":
        raise ValueError("DPAPI 需要 Windows；其他系统请使用环境变量")

    class Blob(ctypes.Structure):
        # DWORD 长度 + 指向字节的指针，与 Windows DATA_BLOB 的 ABI 一致。
        _fields_ = [("size", ctypes.c_ulong), ("data", ctypes.POINTER(ctypes.c_ubyte))]

    buffer = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    destination = Blob()
    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p
    function = crypt32.CryptProtectData if encrypt else crypt32.CryptUnprotectData
    function.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p,
                         ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(Blob)]
    function.restype = ctypes.c_int
    # UI_FORBIDDEN 防止无人值守时显示系统对话框；默认仅当前用户可解密。
    if not function(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(destination)):
        raise ValueError("Windows 凭据解密或保存失败，请在当前账户重新执行 set-key")
    try:
        return ctypes.string_at(destination.data, destination.size)
    finally:
        kernel32.LocalFree(destination.data)


def protect_key(key):
    """UTF-16LE + 十六进制格式兼容 Windows ConvertFrom-SecureString 的 DPAPI 文件。"""
    return dpapi(key.encode("utf-16-le"), encrypt=True).hex()


def load_key():
    """环境变量优先；否则用当前 Windows 用户身份解密本机 DPAPI 文件。"""
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if key:
        return key
    if os.name != "nt" or not KEY_FILE.is_file():
        raise ValueError("缺少密钥：运行 set-key，或设置 DEEPSEEK_API_KEY")
    return dpapi(bytes.fromhex(KEY_FILE.read_text(encoding="ascii").strip())).decode("utf-16-le")


def load_config():
    """只读取本技能的非敏感配置；不会读取或更改主代理 config.toml。"""
    if not CONFIG.is_file():
        raise ValueError("缺少运行配置：先执行 configure --codex <codex.exe 的绝对路径>")
    config = json.loads(CONFIG.read_text(encoding="utf-8-sig"))
    if not Path(config["codex_executable"]).is_file():
        raise ValueError("Codex CLI 路径已失效；用 toolkit-map 查找后重新 configure")
    url = urllib.parse.urlsplit(config.get("base_url", "https://api.deepseek.com"))
    if url.scheme != "https" or not url.hostname or url.username or url.password or url.query or url.fragment:
        raise ValueError("base_url 必须是无嵌入凭据的 HTTPS 地址")
    return config


def probe(config, key):
    """调用官方模型列表确认鉴权和版本；不在未确认时静默改用其他模型。"""
    request = urllib.request.Request(config["base_url"].rstrip("/") + "/models",
                                     headers={"Authorization": "Bearer " + key})
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        # 不输出供应商响应正文，以免代理服务回显凭据。
        raise ValueError(f"DeepSeek 鉴权/模型检查失败：HTTP {error.code}") from None
    except (urllib.error.URLError, TimeoutError):
        raise ValueError("DeepSeek 模型接口网络连接失败") from None
    model = next((item for item in payload.get("data", []) if item.get("id") == MODEL), None)
    if not model:
        raise ValueError("该接口未提供 deepseek-flash；请核对服务地址和模型权限")
    if model.get("name") and model["name"] != MODEL_NAME:
        raise ValueError("deepseek-flash 别名的版本已变化；需确认仍使用 V4.1 Flash 后更新技能")
    return {"ok": True, "model": MODEL, "name": model.get("name", MODEL_NAME)}


def classify_result(outcome, report):
    """进程正常退出还需子代理明确汇报结果；阻塞报告不是成功产物。"""
    if outcome["returncode"] != 0 or outcome["timed_out"]:
        return "failed"
    marker = re.match(r"\s*TASK_STATUS:\s*(completed|blocked|failed)\b", report)
    return marker.group(1) if marker else "unverified"


def child_environment(parent, key, child_home):
    """只继承运行 CLI 必需的系统变量，隔离其他供应商及未知名称的凭据。"""
    allowed = {"PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP",
               "USERPROFILE", "HOMEDRIVE", "HOMEPATH", "APPDATA", "LOCALAPPDATA",
               "PROGRAMDATA", "PROGRAMFILES", "PROGRAMFILES(X86)", "COMMONPROGRAMFILES",
               "PROCESSOR_ARCHITECTURE", "NUMBER_OF_PROCESSORS", "USERNAME", "USERDOMAIN",
               "LANG", "LC_ALL", "TERM"}
    env = {name: value for name, value in parent.items() if name.upper() in allowed}
    env.update({"DEEPSEEK_API_KEY": key, "DEEPSEEK_SUBAGENT": "1",
                "CODEX_HOME": str(child_home), "PYTHONUTF8": "1"})
    return env


def clean_logs(directory, key):
    """递归清理文本日志；跳过数据库和二进制，避免损坏 CLI 运行状态。"""
    text_suffixes = {".md", ".json", ".jsonl", ".log", ".txt", ".toml", ".rules"}
    for path in directory.rglob("*"):
        if path.is_file() and path.suffix.lower() in text_suffixes:
            content = path.read_text(encoding="utf-8", errors="replace")
            if key in content:
                path.write_text(content.replace(key, "[REDACTED]"), encoding="utf-8")


def future_result(future, task_id, key):
    """收集单个任务的异常为失败记录，避免破坏其他任务和整批汇总。"""
    try:
        return future.result()
    except Exception as error:
        return {"id": task_id, "status": "failed", "model": MODEL,
                "error": str(error).replace(key, "[REDACTED]")}


def run_task(config, task, run_dir, key):
    """每个任务具有独立配置目录和日志；子代理禁用递归分派。"""
    directory = run_dir / task["id"]
    directory.mkdir()
    child_home = directory / "runtime"
    child_home.mkdir()
    result_path = directory / "result.md"
    env = child_environment(os.environ, key, child_home)
    prompt = (
        "你是由 GPT 主代理派出的 DeepSeek V4.1 Flash 执行子代理。不要再启动子代理，"
        "不要调用 deepseek-subagents 调度器。遵守工作区 AGENTS.md 和下方主代理要求。"
        "默认中文，代码带详细注释。只完成分配的任务。"
        "不得提交/推送/发布/发送消息/修改主代理配置或访问凭据。"
        "只读任务可分析、设计、输出补丁和完整草稿；不可写项目文件。"
        "写任务只能在指定独立工作区修改文件。最终汇报完成内容、文件路径、"
        "实际验证命令及结果、未解决问题；不要把推测说成已验证。"
        "最终回复第一行严格写 TASK_STATUS: completed 或 TASK_STATUS: blocked 或 TASK_STATUS: failed。"
        "只有确实完成任务才用 completed；权限、依赖、网络阻碍用 blocked。"
        "一次工具调用被拒绝后不要连续换壳重试；明确报告阻塞。\n\n"
        + task["prompt"])
    started = time.monotonic()
    try:
        outcome = execute(build_command(config, task, result_path), prompt, env,
                          task["timeout_sec"], directory / "events.jsonl", directory / "stderr.log")
        report = result_path.read_text(encoding="utf-8") if result_path.is_file() else ""
        outcome["status"] = classify_result(outcome, report)
    except Exception as error:
        # 只记录经过密钥替换的错误文本，不记录完整进程环境。
        outcome = {"status": "failed", "error": str(error).replace(key, "[REDACTED]")}
    clean_logs(directory, key)
    outcome.update({"id": task["id"], "model": MODEL, "workspace": task["workspace"],
                    "result": str(result_path), "elapsed_sec": round(time.monotonic() - started, 2)})
    (directory / "status.json").write_text(json.dumps(outcome, ensure_ascii=False, indent=2), encoding="utf-8")
    return outcome


def main():
    """提供配置、凭据、诊断和批量调度四个命令。"""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    configure = commands.add_parser("configure", help="保存本技能配置，不改变 GPT 主代理")
    configure.add_argument("--codex", required=True)
    configure.add_argument("--base-url", default="https://api.deepseek.com")
    commands.add_parser("set-key", help="交互输入新密钥并保存为 Windows DPAPI 密文")
    commands.add_parser("doctor", help="检查本机 CLI、鉴权和模型版本")
    run = commands.add_parser("run", help="并行执行任务清单")
    run.add_argument("--manifest", required=True)
    run.add_argument("--out", required=True)
    run.add_argument("--max-workers", type=int, default=3)
    args = parser.parse_args()
    try:
        if args.command == "configure":
            executable = Path(args.codex).resolve(strict=True)
            if not executable.is_file():
                raise ValueError("--codex 必须指向可执行文件")
            CONFIG.parent.mkdir(parents=True, exist_ok=True)
            CONFIG.write_text(json.dumps({"codex_executable": str(executable),
                                          "base_url": args.base_url.rstrip("/")},
                                         ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps({"ok": True, "config": str(CONFIG)}))
            return 0
        if args.command == "set-key":
            if os.name != "nt":
                raise ValueError("非 Windows 系统请使用 DEEPSEEK_API_KEY 环境变量")
            key = getpass.getpass("DeepSeek API key: ").strip()
            if not key:
                raise ValueError("密钥不能为空")
            protected = protect_key(key)
            KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
            KEY_FILE.write_text(protected, encoding="ascii")
            print(json.dumps({"ok": True, "credential": "Windows DPAPI"}))
            return 0
        if args.command == "run" and os.environ.get("DEEPSEEK_SUBAGENT") == "1":
            raise ValueError("执行子代理禁止递归派生；请交回 GPT 主代理")
        config, key = load_config(), load_key()
        if args.command == "doctor":
            version = subprocess.run([config["codex_executable"], "--version"],
                                     capture_output=True, text=True, timeout=10)
            if version.returncode:
                raise ValueError("Codex CLI 无法启动")
            print(json.dumps({**probe(config, key), "cli": version.stdout.strip()}, ensure_ascii=False))
            return 0
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8-sig"))
        tasks = validate_manifest(manifest)
        if not 1 <= args.max_workers <= 6:
            raise ValueError("--max-workers 必须介于 1 与 6")
        run_dir = Path(args.out).resolve()
        if run_dir.exists():
            raise ValueError("--out 必须是新目录，避免覆盖此前任务日志")
        probe(config, key)
        run_dir.mkdir(parents=True)
        outcomes = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as pool:
            futures = {pool.submit(run_task, config, task, run_dir, key): task["id"] for task in tasks}
            for future in concurrent.futures.as_completed(futures):
                result = future_result(future, futures[future], key)
                outcomes.append(result)
                # 每完成一个任务即打印状态，主代理可以在其他任务运行时读取结果。
                print(json.dumps(result, ensure_ascii=False), flush=True)
        summary = {"model": MODEL, "tasks": outcomes,
                   "ok": all(task["status"] == "completed" for task in outcomes)}
        (run_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if summary["ok"] else 1
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
