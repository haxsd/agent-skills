---
name: execute-plan
description: 执行书面实施计划：按依赖和工具能力选择顺序执行或委派子代理；含任务账本、逐任务审查与收尾交付。Use when you have a written implementation plan to execute.
---

# 执行实施计划（execute-plan）

两种模式，按依赖与宿主能力选择：

- **委派模式** — 任务基本独立、宿主具备子代理能力：每个任务派新的实现者子代理，任务后审查（规格符合性 + 代码质量），最后做整支审查。
- **顺序模式** — 任务紧耦合或没有子代理：在当前会话按计划逐项实现，用任务清单跟踪，逐项验证。

没有实施计划时，先走 requirement-understanding（需求与方案）与 writing-plans（写计划）。

**为什么委派**：每个任务用隔离上下文的新子代理，精确构造指令，不让它继承会话历史；主代理的上下文留给协调。

**核心原则**：每任务新子代理 + 任务审查 + 整体收尾审查 = 高质量、快迭代。工具调用之间最多一行短叙述——账本和工具结果就是记录。

**连续执行**：任务之间不停下来请示。只有四类事停下问：不可逆或破坏性操作；安全敏感动作；工作区之外的副作用（合并、推共享分支、发布）；计划坏到每一步都是猜。其余自己裁决并记账：`Ruling: <决定> — <理由> — <错了的代价>`。停在问题上等用户，代价是用户的一整天；错误裁决的代价用户看得见、可撤销。

## 流程总览

逐任务：派实现者 → 答复问题 → 实现/测试/提交 → 任务审查（规格 + 质量）→ 修复循环（最多 5 轮，范围化复审）→ 记入账本。全部完成后：整支最终审查 → 一次性修复派发 → 用 finishing-a-development-branch 收尾。

完整流程图：[references/process.md](references/process.md)。

## 准备

隔离工作区、账本检查、读计划、预检审查——未经明确同意不要直接在 main/master 上开工；已在隔离工作区时不重复创建。细节：[references/setup.md](references/setup.md)；模型选择：[references/model-selection.md](references/model-selection.md)。

## 逐任务循环

1. **派实现者** — 填 [implementer-prompt.md](implementer-prompt.md)；新子代理、隔离上下文。
2. **处理报告** — 答复阻塞问题；不要在主会话重做它的工作。
3. **审查任务** — 生成审查包；派 [task-reviewer-prompt.md](task-reviewer-prompt.md)。
4. **修复循环** — 最多 5 轮；R≤3 续用原实现者，R≥4 换新代理 + 更强模型；范围化复审用 [re-review-prompt.md](re-review-prompt.md)。R=5 裁决残留问题。
5. **完成任务** — 追加账本、勾掉任务、继续执行，不问"要继续吗"。

每步完整说明与脚本（`scripts/task-brief`、`scripts/review-package`、`scripts/sdd-workspace`）：[references/task-loop.md](references/task-loop.md)。

## 最终审查

整支审查同样给审查包：运行 `scripts/review-package PLAN_FILE MERGE_BASE HEAD`（MERGE_BASE = 分支起点，如 `git merge-base main HEAD`），把打印的路径放进最终审查派发。用可用模型中最强的（见模型选择），模板用 [code-review/references/code-reviewer.md](../code-review/references/code-reviewer.md)；把账本里 deferred-minor 与 parked 行指给它，由它裁决哪些必须在合并前修。

最终审查有发现时：派**一个**修复代理带完整发现清单（不是每条一个）。然后对修复波次只做一次范围化复审（`scripts/review-package PLAN_FILE FIX_BASE HEAD`）。残留发现按任务循环的裁决方式处理：park 并记录，或对承重的裁决并记账。没有第二轮修复波；承重的残留发现交给 finishing-a-development-branch 呈现给用户。

## 收尾

删除任何东西之前：收集账本里所有 `Ruling:` 行（预检裁决、park 的发现、裁决结论），按顺序放进最终消息的「我做过的裁决」，每条附上"错了的代价"——那是这些决定唯一到达用户的地方。删除工作区前，先把账本与关键报告落到 git 历史或文件里，别让证据随工作区一起消失。

整支审查干净且修复合入后，删除本计划的工作区；其他计划的目录不要动。用 [finishing-a-development-branch](../finishing-a-development-branch/SKILL.md) 收尾，验证契约见 [verification.md](../finishing-a-development-branch/references/verification.md)。

## 顺序模式检查清单

1. 读计划并批判性审查；有疑问先提出，不带着疑问开工
2. 确认隔离工作区（已有则复用）
3. 为计划任务建 todo，逐项：标记进行中 → 按计划步骤实现 → 运行指定验证 → 标记完成
4. 真实阻塞（缺依赖、指令不清、验证反复失败）停下说明；小问题自行修复并记账
5. 完成后同样走「最终审查」与「收尾」——顺序模式也要有验证证据和交付菜单

## 常见自我辩解

| 借口 | 实际 |
|------|------|
| "规格符合度差不多就行" | 审查发现规格缺口＝没完成。修复或到上限后裁决，只有这两种出口。 |
| "我自己修更快，派发是开销" | 主代理自己修会污染上下文且跳过审查。续用原实现者。 |
| "再来一轮就收敛了" | 过了上限不会收敛——失败是结构性的。裁决并重新路由。 |
| "审查者反正还会挑新问题" | 范围化复审只验证修复，不会乱跑。未触碰代码的新发现记账，不进循环。 |
| "这条发现明显是错的，直接丢" | 只能在上限时裁决，每次裁决都进账本。静默丢弃禁止。 |
| "修复很小，跳过复审" | 未复审的修复是回归的来源。每轮都以范围化复审结束。 |
| "账本记账是开销" | 账本是上下文压缩后唯一存活的东西。没有它的协调者会重做整个已完成序列。 |

## 示例

端到端流程演示：[references/example-walkthrough.md](references/example-walkthrough.md)。
