# 安装与外部技能

仓库是收藏集，不要求全部安装。推荐两种用法配合：

- **常驻核心集**：安装 `manifest.json` 里的 `presets.core`，覆盖日常编码流程。
- **按需使用**：其余技能留在仓库，由 `skill-discovery` 检索后直接读取 `SKILL.md`，或临时 `-Only` 安装。

安装器使用目录联接：仓库保存内容，平台目录保存联接。现有真实目录会先备份；卸载只删除指向本仓库或已登记外部源的联接，保留真实内容。

## 推荐：核心集

从仓库根目录在 Windows PowerShell 中执行，先演练：

```powershell
.\install.ps1 -Preset core -DryRun
.\install.ps1 -Preset core
```

`core` 当前包含 14 项：`requirement-understanding`、`systematic-debugging`、`test-driven-development`、`writing-plans`、`execute-plan`、`code-review`、`finishing-a-development-branch`、`windows-powershell-safe`、`env-doctor`、`toolkit-map`、`reverse-skill`、`reverse-skills`、`skill-scanner`、`skill-discovery`。

`-Preset` 与 `-Only` 互斥；`presets` 只是推荐组合，实际落到哪些平台仍由各技能的 `defaultTargets` 决定。核心集适合作为新机器的默认安装，不再全量挂载几十个领域技能。

## 按需安装与检索

任务需要核心集之外的能力时，先让 `skill-discovery` 检索：

1. 读 `docs/catalog.md` 的分类表，或搜 `catalog.json` 的 `name`、`summary`、`uniqueValue`、`scenarios`。
2. 只读命中的 `skills/<name>/SKILL.md`，不读整个仓库。

确认会反复使用后，再单独安装：

```powershell
.\install.ps1 -Only pdf-toolkit -DryRun
.\install.ps1 -Only pdf-toolkit
.\install.ps1 -Only docx,xlsx,pptx
```

`skill-discovery` 定位仓库的顺序是：环境变量 `AGENTSKILLS_ROOT` → `%USERPROFILE%\Desktop\agentskills` → `%USERPROFILE%\Projects\agentskills` → `~/agentskills`。换机器时如果都不匹配，设置环境变量，或直接告诉 agent 实际路径。

## 安装器行为

`manifest.json` 是安装目标的权威来源。`agents` 通用组展开到 agents/cursor/devin/claude；Codex 专属项默认只到 codex。显式 `-Target` 覆盖默认目标。`-Only` 同时限制库内和外部技能；全量安装、`-Preset core`，或 `-Only` 包含 `xlsx`、`docx`、`pptx`、`token-efficient-workflow` 任一，时才会联接 `shared/`；只安装其他技能时不联接。未知名称在改动之前报错。

卸载只删除本仓库建立的联接：

```powershell
.\install.ps1 -Uninstall -DryRun
.\install.ps1 -Only pdf-toolkit -Uninstall
```

## 外部技能

toolkit-map 独立维护，仅在 `external.json` 登记，不把副本并入此仓库。默认路径是 `%USERPROFILE%\Projects\toolkit-map`，请按实际源目录配置；源不存在时会报告并跳过，不会自动下载。reverse-skills 同理，默认 `%USERPROFILE%\tools\reverse-skills`。

`path` 支持绝对路径、仓库相对路径、`%ENV%` 环境变量。例如：

```json
{"name":"toolkit-map","path":"%TOOLKIT_MAP_ROOT%","targets":["agents","cursor","devin","claude"]}
```

先在当前 PowerShell 中设置该环境变量为已确认的源目录，再演练。源和目标相同会直接保留目录，避免把技能源搬进备份后建立坏联接。

## DeepSeek 凭据

安装 skill 后，按 [API 助手配置](../../skills/deepseek-subagent-orchestration/references/api-workers.md) 配置自己的凭据。常规有界委派优先使用 API 路线；`deepseek-subagents` 是需要 Codex CLI 进程和完整本机工具链时的显式高级路线。两条路线不要同时用于同一工作块。主对话 GPT 不切换；本机的全局规则和 DPAPI 密文不由这个仓库分发。其他机器需要自己的配置。
