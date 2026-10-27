---
name: token-efficient-workflow
description: Token 效率工作流（Codex 侧入口）。适用于搜索、读取、编辑、调试、总结、运行命令、检查仓库、处理日志、使用项目参考、更新文件、生成最终回复等任务，避免不必要的上下文、大文件读取、超大终端输出、全仓扫描、冗长计划和过度解释。
targets: [codex-skills]
---

# Token 效率工作流（Codex 侧）

通用准则以 `token-efficiency-rules.md` 为唯一权威来源（核心规则、任务分级、噪声路径、日志处理、最小 diff、输出格式、排查顺序）。按以下顺序找第一个存在且可读的路径，只找一次，不做全盘扫描：

1. 安装布局（Windows）：`%USERPROFILE%\tools\shared\token-efficiency-rules.md`
2. 安装布局（POSIX/手工）：`~/tools/shared/token-efficiency-rules.md`
3. 源码仓库：`<repo>/shared/token-efficiency-rules.md`

找到后读一次并按它执行。都找不到时，使用下面的「最小自包含规则」并说明共享权威文件不可用；不要自行创建替代文件。

## 0. 最小自包含规则（共享文件缺失时）

这不是第二份权威规则，只是离线回退：

- 先分级：`simple` 直接做；`standard` 读最少相关文件；`deep` 先短计划，涉及凭据、生产数据、破坏性操作或多工具协作时先确认。
- 先精确搜索，再打开文件；不默认递归列目录、整份读日志或加载生成物/依赖目录。
- 大输出先摘要；日志只保留相关错误和 20–40 行关键上下文，再给下一步验证。
- 只改必要范围；不做无关重排，不覆盖用户已有改动。
- 最终答复保持简短，但必须包含实际结果、验证证据和未知/风险；不能用“简短”跳过验证。
- 没观察到 token、耗时或运行状态就写未知，不估算成事实。

## 1. 项目内上下文顺序

以下文件若存在才读取，缺哪个就跳过哪个，不要为缺失的文件停下来或自行创建：

1. `AGENTS.md`
2. `context/CURRENT_STATE.md`，任务依赖当前状态时
3. `context/KNOWN_ISSUES.md`，任务涉及风险、错误、自动化、客户、健康、广告、数据时
4. 项目 `references/` 下的索引（如果存在，且确需项目参考时）
5. 通过搜索命中的、或用户指定的具体文件

不要默认打开整个 `references/`、`agents/`、`context/`、`skills/`。存在 `PROJECT_EXCLUSIONS.md` 时，先遵守它再搜索或打开文件。若项目结构不同或上述目录不存在，就以实际存在的入口文档为准，不要假设固定布局。

## 2. 项目辅助脚本（可选）

以下脚本属于项目本地辅助工具，不随本仓库发布：

```powershell
..\tools\codex-helpers\search_symbol.ps1 "term"
..\tools\codex-helpers\find_usages.ps1 "term"
..\tools\codex-helpers\list_changed_files.ps1
..\tools\codex-helpers\summarize_file.ps1 ".\path\file.md"
```

存在时优先使用它们；若路径不存在或项目未提供这些脚本，直接改用原生搜索、读取、编辑工具，不要编造脚本或路径，也不要为了找它们做全仓扫描。

## 3. 自动化与大任务保护

把 WordPress、MCP、广告、Gmail、Telegram、Netlify、GitHub、数据导出、凭据、发布类任务一律视为 `deep`：

- 查询或写入前先核对账号/项目身份，避免拿一个客户的数据当另一个客户的来源
- 发送通知前先验证输出
- 健康检查先看总量与概览，出现告警再取明细
- 报表优先用本地缓存 JSON 做历史对比，只对新数据调用 API，绝不编造缺失指标

## 4. context 更新规则

仅在出现持续性项目变化时更新 `/context`：战略决策、结构性变更、新增已知问题、新增下一步动作、重要里程碑完成。

以下情况不更新：单篇文案、小改动、头脑风暴、一次性回复、例行自动化运行。

<!-- provenance:start -->
> 创作归属：本仓原创。来源、署名与许可见 [来源说明](../../ATTRIBUTION.md#token-efficient-workflow)。
<!-- provenance:end -->
