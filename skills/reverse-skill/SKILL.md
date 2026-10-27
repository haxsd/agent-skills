---
name: reverse-skill
description: 逆向工程 / 渗透测试 / 安全研究技能路由包（reverse-skill）入口。遇到 APK、二进制（exe/dll/so/elf）、前端 JS 加密与签名、抓包重放、协议逆向、CTF、固件、pwn/漏洞利用、补丁差分 N-day、恶意样本分析、EDR 绕过、代码审计、API/GraphQL 安全、供应链安全等任务时使用。Use when reverse engineering, penetration testing, binary analysis, APK analysis, JS deobfuscation, CTF, malware analysis, exploit development, or security research tasks are involved.
---

# reverse-skill 技能路由包（入口）

## 这个 skill 是什么

它本身不含逆向算法，而是一个**路由器**：把「用户任务」映射到正确的逆向方法论子技能，检查本机是否具备相应工具，然后按可复现的流程执行，而不是让模型凭空猜命令。

本仓库内的这个 skill **只是路由入口**。真正的技能包体（`skills/`、`RULES*.md`、各种脚本与参考文档）以**外部安装**的形式存在，路径因机器而异，必须通过下面的解析顺序定位，**不要**在任何文档或命令里写死某一台机器的绝对路径。

## `<SKILL_ROOT>` 解析顺序

按顺序检查，取**第一个存在且可读**的目录作为 `<SKILL_ROOT>`：

1. **环境变量 `REVERSE_SKILL_ROOT`**：若已设置且该目录存在，直接采用。
   - PowerShell：`$env:REVERSE_SKILL_ROOT`
   - Bash：`$REVERSE_SKILL_ROOT`
2. **常见本地候选**（逐个探测，存在于本机则采用）：
   - `$HOME/tools/reverse-skill`（Linux / macOS）
   - `%USERPROFILE%\tools\reverse-skill`（Windows）
   - 其它用户明确告知的路径
3. **都没找到 → 立即 STOP**：
   - 告诉用户：本 skill 只是一个路由器，外部 reverse-skill 技能包尚未安装 / 未定位到，因此无法路由、无法读取 `RULES`、无法运行 `case-init` 等脚本。
   - 请用户提供安装路径，或设置 `REVERSE_SKILL_ROOT`，或先安装技能包。
   - **不要**猜测路径、**不要**凭空执行命令、**不要**编造技能模块或脚本名。

> 如果你在一次会话里已经确定过 `<SKILL_ROOT>`，可以沿用；一旦发现有文件缺失，回到本节的解析顺序重新确认，而不是继续硬跑。

## 预检（Preflight，任何动作之前）

先运行本技能自带的只读预检脚本：

```powershell
python scripts/preflight.py
python scripts/preflight.py --root "<SKILL_ROOT>"
```

脚本按 `REVERSE_SKILL_ROOT`、用户明确给出的 `--root`、默认 `$HOME/tools/reverse-skill` 的顺序解析路径，并输出 JSON：

- `ok`: 必需文件是否齐全。
- `root`: 实际解析到的目录。
- `missingRequired`: 缺失的规则、路由、建案或复核文件。
- `optional`: 工具索引、bootstrap、field-journal 等按需资源的可用性。

退出码非 0 时 **STOP**，把 `missingRequired` 原样列给用户，不要继续执行外部脚本。脚本只读，不安装、不修复、不执行技能包。

人工参考的必需文件为：

- `<SKILL_ROOT>\RULES_zh.md` 或 `<SKILL_ROOT>\RULES.md`
- `<SKILL_ROOT>\skills\MASTER-ROUTING.md`
- `<SKILL_ROOT>\skills\scripts\master-route.ps1`
- `<SKILL_ROOT>\skills\scripts\case-init.ps1`
- `<SKILL_ROOT>\skills\case-review\scripts\review_case.py`

若其中任意一项缺失：

- **STOP**，把缺失的文件/脚本列给用户，说明当前技能包可能不完整或版本不符，并请用户确认安装或更新。
- **不要**用虚构的命令替代，也不要跳过这个检查继续走工作流。

`tool-index.md`、`case-review`、`field-journal` 等属于按需读取/执行，若对应文件缺失，在需要时向用户报告并跳过该步，而不是伪造结果。

## 何时使用

用户任务涉及以下任一场景时启用本 skill，然后按下面的顺序把工作交给技能包本体：

- 移动端：APK / Android、iOS
- 二进制：exe / dll / so / elf、.NET / C#、Go / Rust
- Web / JS：前端加密参数、签名算法、混淆还原、DSL 虚拟机、抓包与重放
- 竞赛与对抗：CTF、补丁差分与 N-day、pwn 与漏洞利用、EDR 绕过
- 安全评估：渗透测试、代码审计、API / GraphQL 安全、供应链、固件与 IoT、Wi-Fi 与无线电

## 工作流程

1. **确定 `<SKILL_ROOT>`**：按上文解析顺序定位，缺失则 STOP（见「`<SKILL_ROOT>` 解析顺序」）。
2. **预检**：运行 `python scripts/preflight.py`，以其 JSON 与退出码为准。
3. **读全局规则**：`<SKILL_ROOT>\RULES_zh.md`（中文）或 `RULES.md`（权威英文原文）。其中定义了 scope 授权门禁、证据链、时间线等强制环节。
4. **路由**：读 `<SKILL_ROOT>\skills\MASTER-ROUTING.md`，或直接让脚本给出 PRIMARY 结论：

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_ROOT>\skills\scripts\master-route.ps1" -Hint "<任务描述>"
   ```

5. **建案例**（动手前的强制环节）：

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_ROOT>\skills\scripts\case-init.ps1" -Hint "<任务描述>"
   ```

   针对外部目标时必须先满足 `auth.status=granted` 并给出有效网络配置；只有显式提供的本地样本可走 `offline-sample` 预设。`-Force` 不能越过授权门禁。

6. **进子技能**：读路由结果对应的 `<SKILL_ROOT>\skills\<模块>\SKILL.md`，按其 `ACTION REQUIRED` 执行，并在案例目录下追加时间线与工作项。
7. **查工具**：需要确认本机是否有某工具时读 `<SKILL_ROOT>\skills\tool-index.md`（若存在；不存在则用下面的动态检查方式）。
8. **交付前自检**：报告交付前运行案例复核脚本，处理全部 error：

   ```powershell
   python "<SKILL_ROOT>\skills\case-review\scripts\review_case.py" work\<case> --verify-hashes --strict
   ```

9. **沉淀经验**：任务完成后按技能包约定把可复用的坑点与流程写回 `<SKILL_ROOT>\skills\field-journal\`。

> ⚠️ 所有路径都是相对于 `<SKILL_ROOT>` 的。若上文中引用的某个脚本在解析出的技能包里不存在，说明版本不符——停下来向用户报告，不要绕开或臆造。

## 工具检查：动态扫描优先

**不要**依赖本文档里的任何工具清单来做判断，那些内容会过时，且只反映**某一台机器**在**某一时刻**的状态。请按以下优先级动态确认：

1. 若有 `<SKILL_ROOT>\skills\tool-index.md` 或技能包提供的 toolkit-map / 刷新脚本：

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_ROOT>\skills\scripts\refresh-tool-index.ps1"
   ```

   以其输出为准。
2. 否则直接在**当前**机器上检查，例如 `Get-Command <tool>` / `where <tool>` / `<tool> --version`（Windows），或 `command -v <tool>` / `<tool> --version`（Linux/macOS）。
3. 不确定是否有对应工具时，如实说明「未检测到」，不要假设它存在，也不要编造调用方式。

### 历史快照（仅作示例，非权威、已过时）

下面这张表是**某台机器在 2026-09-17 扫描**得到的结果，仅用于说明「已具备/缺失」这种记录长什么样。**它不是当前真相，也不是本 skill 的要求**，请按上面的动态扫描方式核实。

| 状态（历史） | 工具（历史） |
|---|---|
| 已具备 | `java` 1.8、`python` 3.12、`node` 16 / `npx`、`git`、`docker` |
| 缺失 | `jadx`、`apktool`、`adb`、`apksigner`、`zipalign`、`frida`、`radare2` 全系、`IDA Pro`、`Binary Ninja`、`nmap`、`seclists`、`yara`、`pwntools` |

补充说明（同样仅反映该历史快照时的环境，会过时）：该机器上 Node 版本、JDK 版本、PATH 上的旧 Node 安装等细节都随时间变化；需要确定版本时一律用当前机器的实际命令核实，不要照抄旧记录，也不要去找文档里提到的某个特定目录（例如某份独立 Node 安装可能早已被清理）。

需要安装缺失工具时，查阅技能包安装说明（如 `<SKILL_ROOT>\README_zh.md` 的依赖表），或使用技能包自带的 bootstrap（若存在）：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_ROOT>\skills\scripts\bootstrap-reverse.ps1" -List
```

运行前同样要先通过预检，确认脚本确实存在。

## 安全与合规

- 技能包内含绕过类与利用类模块。使用前必须确认对目标拥有明确授权，或处于合法 CTF、教学、自测环境。未授权扫描、入侵、凭据窃取、持久化、破坏性操作一律拒绝执行，只做代码理解、样本分析、漏洞修补与防御性验证。
- 技能包内的 `skills/pentest-tools/src-hunter/references/` 有部分 payload 参考文档会被 Windows Defender 标记为 `SCRIPT0049 / SCRIPT0065 / SCRIPT0066`，读取时报「文件包含病毒」。它们是 Markdown 文档而非可执行文件；不要为绕过提示而关闭杀毒软件。
- 遵守 `<SKILL_ROOT>\RULES_zh.md`（或 `RULES.md`）中的 scope 授权门禁与证据链要求。

## 更新

技能包本体位于 `<SKILL_ROOT>`，更新时针对该目录操作（先把 `<SKILL_ROOT>` 解析出来再执行）：

```powershell
git -C "<SKILL_ROOT>" pull
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_ROOT>\skills\scripts\refresh-tool-index.ps1"
```

<!-- provenance:start -->
> 创作归属：本仓原创。来源、署名与许可见 [来源说明](../../ATTRIBUTION.md#reverse-skill)。
<!-- provenance:end -->
