---
name: reverse-skill
description: 逆向工程技能路由包入口。用于 APK/Android、文件分诊、JS 解混淆与参数链、ELF/PE/Mach-O 深度逆向（haxsd/reverse-skills v0.2+）。Use when reverse engineering APKs, triage-ing binaries, JS deobfuscation/signing chains, or native ELF/PE/Mach-O analysis; not for vague "security audit" alone.
---

# reverse-skill 技能路由包（入口）

## 这个 skill 是什么

它本身不含逆向算法，而是一个**路由器**：把「用户任务」映射到正确的逆向方法论子技能，检查本机是否具备相应工具，然后按可复现的流程执行，而不是让模型凭空猜命令。

本仓库内的这个 skill **只是路由入口**。真正的技能包体在独立仓 [haxsd/reverse-skills](https://github.com/haxsd/reverse-skills)（同 [toolkit-map](https://github.com/haxsd/toolkit-map) 外挂模式），必须通过下面的解析顺序定位，**不要**写死某台机器的绝对路径。

## 技能包本体与本仓分工

本仓**不**把技能包本体 vendor 进仓库（见 [ATTRIBUTION.md](../../ATTRIBUTION.md#reverse-skill)）。分工如下：

- **技能包本体**：[haxsd/reverse-skills](https://github.com/haxsd/reverse-skills)（MIT，v0.2.0 起含 JS/二进制）。安装见下。
- **改写参考**（**不是**安装目标）：[zhaoxuya520/reverse-skill](https://github.com/zhaoxuya520/reverse-skill)（MIT）及其他上游，详见独立仓 `ATTRIBUTION.md`。
- 已安装时可用 `VERSION` / `git rev-parse HEAD` 核对版本。

### 安装（推荐）

```bash
git clone https://github.com/haxsd/reverse-skills.git "$HOME/tools/reverse-skills"
export REVERSE_SKILL_ROOT="$HOME/tools/reverse-skills"
```

```powershell
git clone https://github.com/haxsd/reverse-skills.git "$env:USERPROFILE\tools\reverse-skills"
$env:REVERSE_SKILL_ROOT = "$env:USERPROFILE\tools\reverse-skills"
```

## `<SKILL_ROOT>` 解析顺序

按顺序检查，取**第一个存在且可读**的目录作为 `<SKILL_ROOT>`：

1. **环境变量 `REVERSE_SKILL_ROOT`**：若已设置且该目录存在，直接采用。
   - PowerShell：`$env:REVERSE_SKILL_ROOT`
   - Bash：`$REVERSE_SKILL_ROOT`
2. **常见本地候选**（逐个探测）：
   - `$HOME/tools/reverse-skills`（Linux / macOS，**推荐复数路径**）
   - `%USERPROFILE%\tools\reverse-skills`（Windows）
   - `$HOME/tools/reverse-skill` / `%USERPROFILE%\tools\reverse-skill`（兼容旧路径）
   - 其它用户明确告知的路径
3. **都没找到 → 立即 STOP（外部包工作流）**：
   - 说明尚未安装 / 未定位到 `haxsd/reverse-skills`。
   - 请用户按上文 clone，或设置 `REVERSE_SKILL_ROOT`；**不要** clone 第三方上游仓冒充本 skill 的包体。
   - **不要**猜测路径、**不要**凭空执行命令、**不要**编造技能模块或脚本名。
   - 若任务仍需推进，改走下方「未安装技能包时的最小流程」。

> 会话内已确定过 `<SKILL_ROOT>` 可沿用；一旦缺文件，回到本节重新确认。

## 预检（Preflight，任何外部包动作之前）

```powershell
python scripts/preflight.py
python scripts/preflight.py --root "<SKILL_ROOT>"
```

```bash
python scripts/preflight.py
python scripts/preflight.py --root "<SKILL_ROOT>"
```

脚本按 `REVERSE_SKILL_ROOT`、`--root`、默认 `~/tools/reverse-skills`（及兼容旧路径）解析，输出 JSON：`ok`、`root`、`missingRequired`、`optional`。

退出码非 0 时 **STOP**，把 `missingRequired` 原样列给用户。脚本只读，不安装、不修复、不执行技能包。

## 何时使用

用户任务明确涉及以下场景时启用；不要因笼统的「安全 / 审计 / 渗透」字样就触发：

- APK / Android 包逆向（指纹、反编译、API 面、调用链）
- 未知文件 / 二进制**分诊**（容器、架构、加壳线索）
- JS 解混淆、签名/加密参数链、webpack/bundle 分析
- 通用 ELF/PE/Mach-O 深度（表面→工具选择→反汇编/反编译）
- 协议/CTF/固件专项、渗透 payload、EDR 绕过——**包体不收**；勿假装有模块

## 工作流程（外部技能包）

1. **确定 `<SKILL_ROOT>`**；缺失则 STOP 或改走最小流程。
2. **预检**：`python scripts/preflight.py`。
3. **读全局规则**：`<SKILL_ROOT>/RULES_zh.md` 或 `RULES.md`。
4. **路由**：读 `<SKILL_ROOT>/skills/MASTER-ROUTING.md`，或运行：

   ```powershell
   pwsh -NoProfile -File "<SKILL_ROOT>\skills\scripts\master-route.ps1" -Hint "<任务描述>"
   ```

   ```bash
   bash "<SKILL_ROOT>/skills/scripts/master-route.sh" --hint "<任务描述>"
   # 若只有 pwsh：也可跑 master-route.ps1
   ```

5. **建案例**（动手前强制）：

   ```powershell
   pwsh -NoProfile -File "<SKILL_ROOT>\skills\scripts\case-init.ps1" -Hint "<任务>" -CaseName "my-case" -Preset offline-sample -Sample .\app.apk
   ```

   ```bash
   bash "<SKILL_ROOT>/skills/scripts/case-init.sh" --hint "<任务>" --case-name my-case --preset offline-sample --sample ./app.apk
   ```

   针对外部目标时必须 `auth.status=granted` 并给出有效网络配置；本地样本用 `offline-sample`。`-Force` 不能越过授权门禁。

6. **进子技能**：打开 PRIMARY 的 `SKILL.md`（`triage` / `android-apk` / `js-reverse` / `binary-reverse`）。
7. **交付前自检**：

   ```bash
   python "<SKILL_ROOT>/skills/case-review/scripts/review_case.py" work/<case> --strict
   ```

> 路径均相对 `<SKILL_ROOT>`。脚本缺失说明版本不符——停下报告，不要臆造。

## 未安装技能包时的最小流程

1. **授权与范围**：确认授权或合法 CTF/自测；未授权则拒绝，只做防御性理解。
2. **识别样本**：路径、类型、哈希（`file` / `Get-FileHash` / `sha256sum`）。
3. **静态初判**：只用已确认存在的工具（`strings`、`jadx` 等）；没有就如实说明。
4. **证据链**：保存哈希、命令与摘录；结论对应证据。
5. **不做**：不装未请求工具、不关杀软、不把最小流程伪装成完整路由结果。

## 工具检查

动态确认：`Get-Command` / `command -v`。不确定就说「未检测到」。独立仓 `registry.json` 声明了各模块前置工具。

## 安全与合规

- 使用前必须确认对目标有明确授权，或处于合法 CTF/教学/自测。未授权扫描、入侵、凭据窃取、持久化、破坏性操作一律拒绝。
- `haxsd/reverse-skills` **不包含** pentest payload 字典或 EDR 绕过模块。
- 遵守 `<SKILL_ROOT>/RULES_zh.md`（或 `RULES.md`）中的 scope 授权门禁与证据链要求。

## 更新

```bash
[ -d "<SKILL_ROOT>/.git" ] && git -C "<SKILL_ROOT>" pull
```

```powershell
if (Test-Path "<SKILL_ROOT>\.git") { git -C "<SKILL_ROOT>" pull }
```

记下实际 commit 或 `VERSION`。

<!-- provenance:start -->
> 创作归属：本仓原创。来源、署名与许可见 [来源说明](../../ATTRIBUTION.md#reverse-skill)。
<!-- provenance:end -->
