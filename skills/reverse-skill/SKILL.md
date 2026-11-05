---
name: reverse-skill
description: 逆向工程技能路由包入口。用于 APK/二进制逆向、前端 JS 解混淆与签名还原、抓包重放、协议逆向、CTF、固件分析、pwn/漏洞利用、恶意样本分析、补丁差分 N-day。Use when reverse engineering APKs or binaries, JS deobfuscation/signing, packet capture/replay, protocol RE, CTF, firmware analysis, pwn/exploit work, malware analysis, or patch/N-day diff is involved.
---

# reverse-skill 技能路由包（入口）

## 这个 skill 是什么

它本身不含逆向算法，而是一个**路由器**：把「用户任务」映射到正确的逆向方法论子技能，检查本机是否具备相应工具，然后按可复现的流程执行，而不是让模型凭空猜命令。

本仓库内的这个 skill **只是路由入口**。真正的技能包体（`skills/`、`RULES*.md`、各种脚本与参考文档）以**外部安装**的形式存在，路径因机器而异，必须通过下面的解析顺序定位，**不要**在任何文档或命令里写死某一台机器的绝对路径。

## 技能包本体与本仓分工

本仓**不**把技能包本体 vendor 进仓库（见 [ATTRIBUTION.md](../../ATTRIBUTION.md#reverse-skill)）。分工如下：

- **技能包本体**将放在独立仓库 `haxsd/reverse-skills`（**筹备中**，同 [toolkit-map](https://github.com/haxsd/toolkit-map) 外挂模式）。该仓可用之前，请用本机已安装路径，或设置 `REVERSE_SKILL_ROOT`。
- **上游** [zhaoxuya520/reverse-skill](https://github.com/zhaoxuya520/reverse-skill)（MIT，v1.0.1）**仅作改写参考**，**不是**本收藏库的安装目标；不要 `git clone` 它来充当本 skill 的技能包。
- 已有本地安装时，可用 `VERSION` / `git describe` 核对版本；路径以解析顺序为准，不要写死某台机器的绝对路径。

## `<SKILL_ROOT>` 解析顺序

按顺序检查，取**第一个存在且可读**的目录作为 `<SKILL_ROOT>`：

1. **环境变量 `REVERSE_SKILL_ROOT`**：若已设置且该目录存在，直接采用。
   - PowerShell：`$env:REVERSE_SKILL_ROOT`
   - Bash：`$REVERSE_SKILL_ROOT`
2. **常见本地候选**（逐个探测，存在于本机则采用）：
   - `$HOME/tools/reverse-skill`（Linux / macOS）
   - `%USERPROFILE%\tools\reverse-skill`（Windows）
   - 其它用户明确告知的路径
3. **都没找到 → 立即 STOP（外部包工作流）**：
   - 告诉用户：本 skill 只是路由器，外部技能包尚未安装 / 未定位到，因此无法路由、无法读取 `RULES`、无法运行 `case-init` 等脚本。
   - 请用户提供已安装路径，或设置 `REVERSE_SKILL_ROOT`；在 `haxsd/reverse-skills` 可用前不要去 clone 上游第三方仓当安装目标。
   - **不要**猜测路径、**不要**凭空执行命令、**不要**编造技能模块或脚本名。
   - 若任务仍需推进，改走下方「未安装技能包时的最小流程」，**不要**假装已进入外部包工作流。

> 如果你在一次会话里已经确定过 `<SKILL_ROOT>`，可以沿用；一旦发现有文件缺失，回到本节的解析顺序重新确认，而不是继续硬跑。

## 预检（Preflight，任何外部包动作之前）

先运行本技能自带的只读预检脚本（以脚本 JSON 与退出码为准；脚本检查必需文件是否齐全，缺失则非零退出）：

```powershell
# PowerShell（在本 skill 目录下）
python scripts/preflight.py
python scripts/preflight.py --root "<SKILL_ROOT>"
```

```bash
# bash
python scripts/preflight.py
python scripts/preflight.py --root "<SKILL_ROOT>"
```

脚本按 `REVERSE_SKILL_ROOT`、用户明确给出的 `--root`、默认 `$HOME/tools/reverse-skill` 的顺序解析路径，并输出 JSON：`ok`、`root`、`missingRequired`、`optional`。

退出码非 0 时 **STOP**，把 `missingRequired` 原样列给用户，不要继续执行外部脚本。脚本只读，不安装、不修复、不执行技能包。可选资源（如 `tool-index.md`、`field-journal`）缺失时，在需要该步再报告并跳过，不要伪造结果。

## 何时使用

用户任务明确涉及以下场景时启用；不要因笼统的「安全 / 审计 / 渗透」字样就触发：

- APK / 二进制（exe、dll、so、elf 等）逆向
- 前端 JS 解混淆、加密参数与签名还原
- 抓包与重放、协议逆向
- CTF、固件分析、pwn / 漏洞利用
- 恶意样本分析、补丁差分与 N-day

## 工作流程（外部技能包）

1. **确定 `<SKILL_ROOT>`**：按上文解析顺序定位；缺失则 STOP 外部包工作流（可改走最小流程）。
2. **预检**：运行 `python scripts/preflight.py`，以其 JSON 与退出码为准。
3. **读全局规则**：`<SKILL_ROOT>/RULES_zh.md`（中文）或 `RULES.md`。其中定义 scope 授权门禁、证据链、时间线等强制环节。
4. **路由**：读 `<SKILL_ROOT>/skills/MASTER-ROUTING.md`，或运行：

   ```powershell
   # PowerShell
   pwsh -NoProfile -ExecutionPolicy Bypass -File "<SKILL_ROOT>\skills\scripts\master-route.ps1" -Hint "<任务描述>"
   ```

   ```bash
   # bash（需要已安装 pwsh）
   pwsh -NoProfile -ExecutionPolicy Bypass -File "<SKILL_ROOT>/skills/scripts/master-route.ps1" -Hint "<任务描述>"
   ```

5. **建案例**（动手前强制）：

   ```powershell
   pwsh -NoProfile -ExecutionPolicy Bypass -File "<SKILL_ROOT>\skills\scripts\case-init.ps1" -Hint "<任务描述>"
   ```

   ```bash
   pwsh -NoProfile -ExecutionPolicy Bypass -File "<SKILL_ROOT>/skills/scripts/case-init.ps1" -Hint "<任务描述>"
   ```

   针对外部目标时必须先满足 `auth.status=granted` 并给出有效网络配置；只有显式提供的本地样本可走 `offline-sample` 预设。`-Force` 不能越过授权门禁。

6. **进子技能**：读路由结果对应的 `<SKILL_ROOT>/skills/<模块>/SKILL.md`，按其 `ACTION REQUIRED` 执行，并在案例目录下追加时间线与工作项。
7. **查工具**：需要时读 `<SKILL_ROOT>/skills/tool-index.md`（若存在）；否则用下方动态检查。
8. **交付前自检**：

   ```powershell
   python "<SKILL_ROOT>\skills\case-review\scripts\review_case.py" work\<case> --verify-hashes --strict
   ```

   ```bash
   python "<SKILL_ROOT>/skills/case-review/scripts/review_case.py" work/<case> --verify-hashes --strict
   ```

9. **沉淀经验**：按技能包约定写回 `<SKILL_ROOT>/skills/field-journal/`。

> ⚠️ 所有路径相对 `<SKILL_ROOT>`。若引用脚本在解析出的技能包里不存在，说明版本不符——停下来向用户报告，不要绕开或臆造。`.ps1` 在 bash 下需通过 `pwsh` 运行。

## 未安装技能包时的最小流程

外部包找不到、预检失败、或用户只要快速静态初判时，**不要编造外部模块名或命令**。在确认授权与范围后，用本机已验证存在的工具做最小静态梳理，并留下证据链：

1. **授权与范围**：确认对样本/目标有明确授权，或处于合法 CTF、教学、自测环境；未授权则拒绝，只做防御性理解。
2. **识别样本**：记录路径、类型与哈希。

   ```powershell
   Get-Item .\sample.bin | Format-List FullName, Length, LastWriteTime
   Get-FileHash .\sample.bin -Algorithm SHA256
   ```

   ```bash
   file ./sample.bin
   sha256sum ./sample.bin   # macOS 可用 shasum -a 256
   ```

3. **静态初判**（仅使用 `Get-Command` / `command -v` 已确认存在的工具；未检测到就如实说明，不要假设或编造调用方式）：
   - 通用：`strings`、`binwalk`；ELF/PE 可用 `readelf` / `objdump` / `dumpbin`
   - APK：`jadx`、`apktool`（若存在）
   - 混淆 JS：本地已有的美化/解混淆工具（若存在）
4. **证据链**：在案例目录保存哈希、实际执行的命令、关键输出摘录与时间；交付时结论必须对应证据。
5. **不做**：不安装未请求的工具、不关闭杀软、不把最小流程伪装成外部包完整路由结果。

## 工具检查：动态扫描优先

**不要**依赖文档里的固定工具清单。按以下优先级动态确认：

1. 若有 `<SKILL_ROOT>/skills/tool-index.md` 或刷新脚本：

   ```powershell
   pwsh -NoProfile -ExecutionPolicy Bypass -File "<SKILL_ROOT>\skills\scripts\refresh-tool-index.ps1"
   ```

   ```bash
   pwsh -NoProfile -ExecutionPolicy Bypass -File "<SKILL_ROOT>/skills/scripts/refresh-tool-index.ps1"
   ```

2. 否则在当前机器检查：`Get-Command <tool>`（PowerShell）或 `command -v <tool>`（bash），必要时再跑 `<tool> --version`。
3. 不确定时如实说明「未检测到」，不要假设存在，也不要编造调用方式。

需要安装缺失工具时，查阅技能包安装说明（如 `<SKILL_ROOT>/README_zh.md`），或在预检确认脚本存在后运行：

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File "<SKILL_ROOT>\skills\scripts\bootstrap-reverse.ps1" -List
```

```bash
pwsh -NoProfile -ExecutionPolicy Bypass -File "<SKILL_ROOT>/skills/scripts/bootstrap-reverse.ps1" -List
```

## 安全与合规

- 技能包内含绕过类与利用类模块。使用前必须确认对目标拥有明确授权，或处于合法 CTF、教学、自测环境。未授权扫描、入侵、凭据窃取、持久化、破坏性操作一律拒绝执行，只做代码理解、样本分析、漏洞修补与防御性验证。
- 技能包内的 `skills/pentest-tools/src-hunter/references/` 有部分 payload 参考文档会被 Windows Defender 标记为 `SCRIPT0049 / SCRIPT0065 / SCRIPT0066`，读取时报「文件包含病毒」。它们是 Markdown 文档而非可执行文件；不要为绕过提示而关闭杀毒软件。
- 遵守 `<SKILL_ROOT>/RULES_zh.md`（或 `RULES.md`）中的 scope 授权门禁与证据链要求。

## 更新

技能包本体位于 `<SKILL_ROOT>`（本机路径或未来的 `haxsd/reverse-skills` 安装目录）。若该目录是 git 仓库，可按需更新后刷新工具索引；没有 git 就跳过 pull：

```powershell
if (Test-Path "<SKILL_ROOT>\.git") { git -C "<SKILL_ROOT>" pull }
pwsh -NoProfile -ExecutionPolicy Bypass -File "<SKILL_ROOT>\skills\scripts\refresh-tool-index.ps1"
```

```bash
[ -d "<SKILL_ROOT>/.git" ] && git -C "<SKILL_ROOT>" pull
pwsh -NoProfile -ExecutionPolicy Bypass -File "<SKILL_ROOT>/skills/scripts/refresh-tool-index.ps1"
```

更新后记下实际 commit/tag 或 `VERSION`；不要把第三方上游仓当作本收藏库的默认安装源。

<!-- provenance:start -->
> 创作归属：本仓原创。来源、署名与许可见 [来源说明](../../ATTRIBUTION.md#reverse-skill)。
<!-- provenance:end -->
