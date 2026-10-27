# 安装与外部技能

从仓库根目录在 Windows PowerShell 中执行，先演练：

```powershell
.\install.ps1 -DryRun
.\install.ps1 -Only deepseek-subagent-orchestration -Target codex -DryRun
.\install.ps1 -Only deepseek-subagent-orchestration -Target codex
.\install.ps1 -Uninstall -DryRun
```

安装器使用目录联接，仓库保存内容，平台目录保存联接。现有真实目录会先备份；卸载只删除指向本仓库或已登记外部源的联接，保留真实内容。

`manifest.json` 是安装目标的权威来源。`agents` 通用组展开到 agents/cursor/devin/claude；Codex 专属项默认只到 codex。显式 `-Target` 覆盖默认目标。`-Only` 同时限制库内和外部技能；只在安装 token-efficient-workflow 或未指定 `-Only` 时处理它需要的 shared。未知名称在改动之前报错。

## 外部技能

toolkit-map 独立维护，仅在 `external.json` 登记，不把副本并入此仓库。默认路径是 `%USERPROFILE%\Projects\toolkit-map`，请按实际源目录配置；源不存在时会报告并跳过，不会自动下载。

`path` 支持绝对路径、仓库相对路径、`%ENV%` 环境变量。例如：

```json
{"name":"toolkit-map","path":"%TOOLKIT_MAP_ROOT%","targets":["agents","cursor","devin","claude"]}
```

先在当前 PowerShell 中设置该环境变量为已确认的源目录，再演练。源和目标相同会直接保留目录，避免把技能源搬进备份后建立坏联接。

## DeepSeek 凭据

安装 skill 后，按 [API 助手配置](../../skills/deepseek-subagent-orchestration/references/api-workers.md) 配置自己的凭据。常规有界委派优先使用 API 路线；`deepseek-subagents` 是需要 Codex CLI 进程和完整本机工具链时的显式高级路线。两条路线不要同时用于同一工作块。主对话 GPT 不切换；本机的全局规则和 DPAPI 密文不由这个仓库分发。其他机器需要自己的配置。
