---
name: skill-scanner
description: 安装或引入技能前对技能目录做静态风险扫描：提示词注入、凭据访问、全局 agent 配置写入、下载即执行、脚本可疑构造、package.json lifecycle 与 frontmatter hooks/动态命令。Use when 需要离线复核某个技能目录、审查第三方技能来源，或在安装前做一遍只读体检。
license: Apache-2.0; see LICENSE.txt
---

# skill-scanner

对**一个技能目录**做离线静态扫描，输出待人工复核的候选风险条目。只读：不运行、不 import、
不联网、不写文件；结果里只有规则标识、相对路径、行号、静态理由和上下文标签。

脚本 `scripts/scan_skill.py` 只定位需要复核的静态线索，**不判定恶意、也不认证安全**。
零发现只能说明本次范围内未命中这些规则，不能据此声称可以安全安装。

## 何时用

- 准备安装、拷贝或启用一个来源不明的技能，先扫一遍。
- 技能里有"自动执行/直接运行/写入全局配置"之类的描述，想把可疑点列出来。
- 批量复核 `skills/` 下的目录，需要机器可解析的结构化结果。

不用它来做这些：元数据/收录/provenance 一致性核对用 `scripts/audit_skills.py`；产品代码审查用
`code-review`；查本机工具绝对路径用 `toolkit-map`；逆向、抓包、漏洞利用类任务找 `reverse-skill`。

## 调用方式

先按 `toolkit-map` 的流程拿 Python 的绝对路径，再用绝对路径调用脚本，不要靠 PATH 猜：

```powershell
& '<map.ps1 的绝对路径>' find python -Project <当前工作区> -Json      # 取返回里的 path
& '<python 的绝对路径>' '<技能目录>\scripts\scan_skill.py' '<被扫描的技能目录>'
```

- 地图和现场都找不到 Python 时，如实报告缺失；不要为跑扫描器去装运行时。
- 可选参数（必须是正整数，否则 exit 2）：`--max-files`（默认 500，最多检查多少个文件）、
  `--max-file-bytes`（默认 1048576，单文件最多读多少字节）、`--max-entries`（默认 2000，最多枚举
  多少个目录条目）。`--help` 打印用法。
- 退出码：`0` 扫描完成（可能含待复核发现）；`1` 扫描不完整或被拒绝（看 `coverage.gaps` /
  `refusal`）；`2` 参数错误。发现本身不改变退出码——有发现也可能是 0。

## 输出契约

stdout 是一个 JSON 对象，必须整体解析；不写任何文件。

```json
{
  "schemaVersion": 1,
  "status": "ok 或 incomplete 或 refused",
  "refusal": null,
  "findings": [{"ruleId": "...", "category": "...", "file": "相对路径", "line": 12,
                "confidence": "high|medium|low", "context": null, "reason": "静态说明"}],
  "coverage": {"complete": true, "scannedFiles": 0, "examinedFiles": 0, "visitedEntries": 0,
               "gaps": [{"path": "相对路径", "reason": "..."}], "policySkips": [],
               "limits": {"maxFiles": 500, "maxFileBytes": 1048576, "maxEntries": 2000}},
  "assessment": "review-required 或 no-findings-detected",
  "disclaimer": "..."
}
```

- `assessment` 永远不会是 safe-to-install 这类结论；`disclaimer` 也明说零发现不是安全认证。
- 隐私口径：输出不含匹配到的原文行、URL 路径/查询串、环境变量值、秘密原文、绝对路径和异常细节。
  想了解某条发现，按 `file` + `line` 自己打开那一行看。
- `context` 为空表示没检测到"这是文档示例"的线索；`markdown-code-block`（fenced 代码块内）或
  `documentation-example`（上下行有"例如/示例/不要运行/example/fixture"等措辞）表示置信度已降一档，
  但**发现不会被丢掉**。

## 覆盖范围与覆盖缺口

- 扫描对象：技能目录下的文本文件；按扩展名或 shebang 选择语言规则（Python/JS/PowerShell/Shell/
  Markdown 等），入口 `SKILL.md` 优先扫描。`package.json` 用标准库 `json` 解析后定位
  `scripts` 下的生命周期键（minified 单行文件同样能定位），同名键不在 `scripts` 下不算；脚本原文
  不会出现在输出里。语法合法但 `scripts` 不是对象时，没有可识别的生命周期键；本脚本不验证 npm
  包结构是否合法，也不据此声称它能安装。
- 策略跳过：`.git`、`__pycache__`、`node_modules`、虚拟环境与各种缓存目录，记在 `policySkips`，
  不算缺口。
- 覆盖缺口 `gaps`：二进制（含 NUL 的伪文本）、超过字节上限、不可读、非 UTF-8 的未知格式、内部
  symlink/junction、特殊文件、无法解析的 `package.json`（`invalid-json`），以及文件数/枚举条目数
  超过 `--max-files`（`file-limit`）或 `--max-entries`（`entry-limit`）。
- **有缺口就是 `complete: false`、exit 1**：不许把这种结果当"扫过了"。要么抬高上限重跑，要么人工
  确认那些文件里没有会执行的东西。
- 枚举有界：目录按需读取迭代器，最多保留 `--max-entries` 个条目（`visitedEntries` 为保留条目计数），
  可以额外查看一个条目以判断是否截断，不会先把整个目录读进内存；子目录超限时整目录不读并记 `entry-limit`。
  根目录超限时直接拒绝（`refusal: root-entry-limit`），仍记录已枚举预算，不会假装已扫描文件。
- 链接不跟随：根路径由调用者显式传入时，按其解析到的目标作为授权根；根必须是含**普通**
  `SKILL.md` 的目录（符号链接/目录/ junction 一律拒绝），目录内部出现的链接只进 `gaps`，不读取。

## 复核流程

1. 先读 `status`、`coverage.complete`、`gaps`：有缺口先补覆盖，再看发现。
2. 逐条按 `file` + `line` 打开原文件人工判断：这行是文档示例，还是真的会被执行？
3. 重点确认"会不会自己动起来"的线索：frontmatter 的 hooks/钩子事件字段（含顶层 `PreToolUse`、
   `PostToolUse`）、正文里的 `!`command`` 动态命令、`package.json` 的 lifecycle 脚本、下载后交给
   解释器执行的写法。
4. 结论按"待复核 / 已确认 / 误报"写，不写"安全"或"恶意"；不要拿脚本输出当审计结论。
5. 需要人判断的关键点：脚本要什么权限、往哪写（尤其全局 agent 配置）、请求发往哪里、有没有
   "不要告诉用户"这类隐瞒迹象。

## 已知边界（务必连同结果一起转述）

- 纯文本模式匹配，不做语义或执行分析；换写法、编码、拆行拼装都能绕过。
- 文档示例只会降置信度不会删除，所以攻击者可以用"示例/example"话术降低某条的置信度——必须看行。
- 本技能自身的文档会引用模式关键词，自扫时出现少量对应条目属预期。
- 扫描是某一时刻的快照：目标在扫描期间被并发改动（stat 与读取之间、枚举与打开之间）不受保护，
  也没有文件锁；`package.json` 的行号由文本搜索定位，同名字符串可能让行号偏移。严格审计应在
  隔离环境里人工复核，不要只依赖本脚本。
- 二进制内容只看作覆盖缺口，不解析；不做依赖审计、不做漏洞扫描、不做免杀分析。
- 纯标准库、离线、跨 Windows/Linux；Windows 下文件名大小写不敏感、伪装后缀按内容判定。

规则清单（每条检测什么、为什么只算待复核、常见误报）见 [references/rules.md](references/rules.md)。

<!-- provenance:start -->
> 创作归属：原创改进（基于上游）。来源、署名与许可见 [来源说明](../../ATTRIBUTION.md#skill-scanner)。
<!-- provenance:end -->
