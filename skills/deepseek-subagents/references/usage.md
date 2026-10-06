# 运行说明

脚本仅依赖 Python 标准库及 Codex CLI；当前安装已保存本机 CLI 路径和 Windows DPAPI 凭据。主代理 `config.toml` 不会改动。迁移电脑时重新配置 CLI 和密钥，不复制当前账户的 DPAPI 文件。

## 检查连接

```powershell
# 使用本机已验证的 Python，不依赖可能指向商店占位程序的 PATH。
$deepseekPython = '%USERPROFILE%\AppData\Local\Programs\Python\Python312\python.exe'
# 调度器位于当前用户技能目录。迁移时更新两处路径。
$deepseekRunner = '%USERPROFILE%\.codex\skills\deepseek-subagents\scripts\delegate.py'
# 检查 CLI、API 鉴权和模型标识；不会生成内容或改主代理配置。
& $deepseekPython -X utf8 $deepseekRunner doctor
```

## 任务清单

以下代码的注释说明字段；写出的文件为标准 JSON。

```python
import json
from pathlib import Path

# 两个只读任务可以并行分析同一份源码；实际委派时补充具体文件和验收条件。
workspace = Path.cwd().resolve()
tasks = {
    "tasks": [
        {
            "id": "inspect",
            "workspace": str(workspace),
            "sandbox": "read-only",
            "timeout_sec": 600,
            "prompt": "分析指定模块的错误原因，列出证据、文件行号和最小修复建议。",
        },
        {
            "id": "test-design",
            "workspace": str(workspace),
            "sandbox": "read-only",
            "timeout_sec": 600,
            "prompt": "针对提供的缺陷设计复现测试，输出带注释的完整测试代码。",
        },
    ]
}
# 中间文件不包含凭据；每次启动使用新的运行输出目录。
manifest = workspace / "work" / "deepseek" / "tasks.json"
manifest.parent.mkdir(parents=True, exist_ok=True)
manifest.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
```

```powershell
# 路径替换为当前项目实际路径；运行日志保存在新的目录中。
& $deepseekPython -X utf8 $deepseekRunner run `
  --manifest 'C:\项目\work\deepseek\tasks.json' `
  --out 'C:\项目\work\deepseek\run-001' `
  --max-workers 3
```

`workspace-write` 任务必须使用各自独立工作区；只有一个写任务时也优先隔离目录，便于 GPT 核对后整合。

## 输出和故障

- 每个任务目录：`result.md` 最终报告；`events.jsonl` 工具/状态事件；`stderr.log` CLI 诊断；`status.json` 退出码、耗时和状态。
- 整批目录：`summary.json` 汇总全部任务。每完成一个任务即输出一行 JSON 状态，主代理可提前查看结果。
- 任务状态：`completed` 已汇报完成；`blocked` 阻塞；`failed` 执行失败；`unverified` 报告未明确状态。GPT 仍须独立核验产物。
- 退出码 `0`：全部子代理明确汇报完成；`1`：至少一个失败、阻塞或未核验；`2`：配置、凭据或清单错误。完成状态不表示任务成果已验收。
- 默认单任务上限 600 秒，可在 10—1800 秒内调整；默认并发 3，可在 1—6 内调整。超时结束子代理及工具进程树。
- 失败后读诊断再修正，重跑用新目录；不要无界重试或重复执行已完成任务。

## 迁移或更新

```powershell
# 应用升级使 CLI 路径失效时，重新发现实际 codex.exe 后保存路径。
& $deepseekPython -X utf8 $deepseekRunner configure --codex 'C:\实际路径\codex.exe'
# 交互隐藏输入密钥，保存为 Windows DPAPI 密文，密钥不进入命令参数。
& $deepseekPython -X utf8 $deepseekRunner set-key
# 确认连接及指定模型。
& $deepseekPython -X utf8 $deepseekRunner doctor
```

`DEEPSEEK_API_KEY` 环境变量可覆盖本机凭据，适合 CI/非 Windows 系统。子代理通过独立 `CODEX_HOME` 隔离主代理认证、模型和 MCP 配置；密钥从终端工具环境中排除，日志亦替换可能回显的密钥。

## 核验依据

2026-10-06（中国时区）已核对以下官方接口/文档。

- [DeepSeek 模型接口](https://api-docs.deepseek.com/api/list-models/)：`deepseek-flash` 对应 `DeepSeek-V4.1-Flash`。
- [DeepSeek Responses API](https://api-docs.deepseek.com/guides/responses_api/)：Codex 的 Responses 兼容接口。
- [Codex 非交互执行](https://learn.chatgpt.com/docs/non-interactive-mode)：`exec`、JSONL、最终报告和 sandbox。
- [Codex provider 配置](https://learn.chatgpt.com/docs/config-file/config-reference)：`base_url`、`env_key`、`wire_api`。
