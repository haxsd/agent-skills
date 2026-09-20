---
name: reverse-skill
description: 逆向工程 / 渗透测试 / 安全研究技能路由包（reverse-skill）入口。遇到 APK、二进制（exe/dll/so/elf）、前端 JS 加密与签名、抓包重放、协议逆向、CTF、固件、pwn/漏洞利用、补丁差分 N-day、恶意样本分析、EDR 绕过、代码审计、API/GraphQL 安全、供应链安全等任务时使用。Use when reverse engineering, penetration testing, binary analysis, APK analysis, JS deobfuscation, CTF, malware analysis, exploit development, or security research tasks are involved.
---

# reverse-skill 技能路由包（入口）

## 这个 skill 是什么

它本身不含逆向算法，而是一个**路由器**：把「用户任务」映射到正确的逆向方法论子技能，检查本机工具是否具备，然后按可复现的流程执行，而不是让模型凭空猜命令。

完整的技能包已经安装在：

```
C:\Users\Administrator\tools\reverse-skill
```

下面用 `<SKILL_ROOT>` 代指该路径。技能包共 49 个技能模块、89 个 `SKILL.md`，覆盖 APK 逆向、IDA / radare2 / Ghidra / Binary Ninja、JS 逆向、协议逆向、恶意样本、渗透工具链、攻击链编排、固件、pwn、EDR 绕过、威胁情报等方向。

## 何时使用

用户任务涉及以下任一场景时启用本 skill，然后按下面的顺序把工作交给技能包本体：

- 移动端：APK / Android、iOS
- 二进制：exe / dll / so / elf、.NET / C#、Go / Rust
- Web / JS：前端加密参数、签名算法、混淆还原、DSL 虚拟机、抓包与重放
- 竞赛与对抗：CTF、补丁差分与 N-day、pwn 与漏洞利用、EDR 绕过
- 安全评估：渗透测试、代码审计、API / GraphQL 安全、供应链、固件与 IoT、Wi-Fi 与无线电

## 工作流程

1. **读全局规则**：`<SKILL_ROOT>\RULES_zh.md`（中文）或 `RULES.md`（权威英文原文）。其中定义了 scope 授权门禁、证据链、时间线等强制环节。
2. **路由**：读 `<SKILL_ROOT>\skills\MASTER-ROUTING.md`，或直接让脚本给出 PRIMARY 结论：

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_ROOT>\skills\scripts\master-route.ps1" -Hint "<任务描述>"
   ```

3. **建案例**（动手前的强制环节）：

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_ROOT>\skills\scripts\case-init.ps1" -Hint "<任务描述>"
   ```

   针对外部目标时必须先满足 `auth.status=granted` 并给出有效网络配置；只有显式提供的本地样本可走 `offline-sample` 预设。`-Force` 不能越过授权门禁。

4. **进子技能**：读路由结果对应的 `<SKILL_ROOT>\skills\<模块>\SKILL.md`，按其 `ACTION REQUIRED` 执行，并在案例目录下追加时间线与工作项。
5. **查工具**：需要确认本机是否有某工具时读 `<SKILL_ROOT>\skills\tool-index.md`。
6. **交付前自检**：报告交付前运行案例复核脚本，处理全部 error：

   ```powershell
   python "<SKILL_ROOT>\skills\case-review\scripts\review_case.py" work\<case> --verify-hashes --strict
   ```

7. **沉淀经验**：任务完成后按技能包约定把可复用的坑点与流程写回 `<SKILL_ROOT>\skills\field-journal\`。

## 本机工具链现状（2026-09-17 扫描）

| 状态 | 工具 |
|---|---|
| 已具备 | `java` 1.8、`python` 3.12、`node` 16 / `npx`、`git`、`docker` |
| 缺失 | `jadx`、`apktool`、`adb`、`apksigner`、`zipalign`、`frida`、`radare2` 全系、`IDA Pro`、`Binary Ninja`、`nmap`、`seclists`、`yara`、`pwntools` |

含义：路由、方法论、报告模板现在就能用；真正做 APK 或二进制分析前要先补工具。需要时按 `<SKILL_ROOT>\README_zh.md` 的依赖表安装，或调用技能包自带的 bootstrap：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_ROOT>\skills\scripts\bootstrap-reverse.ps1" -List
```

注意 `node` 为 16.x，而技能包要求 22.12+ 才能跑 JS 工具链与 MCP；`C:\Users\Administrator\tools\node22` 目录里似乎另有一套 Node，必要时改用它。另外本机 `java` 是 1.8，新版 jadx 需要 JDK 11+。

## 安全与合规

- 技能包内的 `skills/pentest-tools/src-hunter/references/` 有部分 payload 参考文档会被 Windows Defender 标记为 `SCRIPT0049 / SCRIPT0065 / SCRIPT0066`，读取时报「文件包含病毒」。它们是 Markdown 文档而非可执行文件；不要为绕过提示而关闭杀毒软件。
- 技能包内含绕过类与利用类模块。使用前必须确认对目标拥有明确授权，或处于合法 CTF、教学、自测环境。未授权扫描、入侵、凭据窃取、持久化、破坏性操作一律拒绝执行，只做代码理解、样本分析、漏洞修补与防御性验证。

## 更新

```powershell
git -C "<SKILL_ROOT>" pull
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_ROOT>\skills\scripts\refresh-tool-index.ps1"
```
