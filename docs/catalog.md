# Skills 分类目录

由 `catalog.json` 和 `scripts/audit_skills.py` 生成。

审查日期：2026-10-27。38 个启用 + 11 个归档 + 1 个外部入口。

分类是逻辑索引，保留平铺目录，兼容现有安装器。状态描述仓库当前布局，动作是审查建议，不会自动移动/卸载。
价值高/中/低来自内容审查，不能解读为实测收益；条件可用也不代表所有流程通过了运行验证。

安装目标仍只由 `manifest.json` / `external.json` 决定；不要从本目录生成第二套目标配置。

来源分为第三方引入、本仓原创、原创改进（基于上游）和待核验；原创改进保留上游署名与许可。每项完整来源见 [署名说明](../ATTRIBUTION.md) 和 [来源登记](sources/skill-provenance.json)。

逐项审查、整改路线与机器检查结果由维护者在内部保存。

## 需求与规划

| Skill | 当前状态 | 创作归属 | 内容价值 | 当前就绪程度 | 建议 | 优先级 |
|---|---|---|---|---|---|---|
| [requirement-understanding](../skills/requirement-understanding/SKILL.md) | 启用 | 原创改进（基于上游） | 中 | 条件可用 | 保留 | P1 |
| [brainstorming](../archive/skills/brainstorming/SKILL.md) | 归档 | 第三方引入 | 中 | 规则需改造 | 维持归档 | P1 |
| [writing-plans](../skills/writing-plans/SKILL.md) | 启用 | 原创改进（基于上游） | 中 | 条件可用 | 保留 | P1 |
| [ask-questions-if-underspecified](../archive/skills/ask-questions-if-underspecified/SKILL.md) | 归档 | 第三方引入 | 中 | 条件可用 | 维持归档 | P1 |

## 实现与代理编排

| Skill | 当前状态 | 创作归属 | 内容价值 | 当前就绪程度 | 建议 | 优先级 |
|---|---|---|---|---|---|---|
| [executing-plans](../archive/skills/executing-plans/SKILL.md) | 归档 | 第三方引入 | 中 | 规则需改造 | 维持归档 | P1 |
| [execute-plan](../skills/execute-plan/SKILL.md) | 启用 | 原创改进（基于上游） | 高 | 条件可用 | 保留 | P1 |
| [parallel-agents](../skills/parallel-agents/SKILL.md) | 启用 | 原创改进（基于上游） | 高 | 条件可用 | 保留 | P1 |
| [deepseek-subagent-orchestration](../skills/deepseek-subagent-orchestration/SKILL.md) | 启用 | 本仓原创 | 中 | 局部实测可运行 | 保留 | P2 |
| [best-of-n-solving](../archive/skills/best-of-n-solving/SKILL.md) | 归档 | 待核验 | 低 | 条件可用 | 维持归档 | P2 |
| [dispatching-parallel-agents](../archive/skills/dispatching-parallel-agents/SKILL.md) | 归档 | 第三方引入 | 低 | 条件可用 | 维持归档 | P2 |
| [mcp-builder](../skills/mcp-builder/SKILL.md) | 启用 | 第三方引入 | 高 | 条件可用 | 保留 | P2 |
| [development-workflow](../skills/development-workflow/SKILL.md) | 启用 | 本仓原创 | 中 | 条件可用 | 保留 | P1 |
| [deepseek-subagents](../skills/deepseek-subagents/SKILL.md) | 启用 | 本仓原创 | 高 | 条件可用 | 保留 | P1 |

## 质量、调试与审查

| Skill | 当前状态 | 创作归属 | 内容价值 | 当前就绪程度 | 建议 | 优先级 |
|---|---|---|---|---|---|---|
| [env-doctor](../skills/env-doctor/SKILL.md) | 启用 | 原创改进（基于上游） | 高 | 条件可用 | 保留 | P2 |
| [systematic-debugging](../skills/systematic-debugging/SKILL.md) | 启用 | 原创改进（基于上游） | 高 | 条件可用 | 保留 | P1 |
| [test-driven-development](../skills/test-driven-development/SKILL.md) | 启用 | 原创改进（基于上游） | 中 | 条件可用 | 保留 | P1 |
| [verification-before-completion](../archive/skills/verification-before-completion/SKILL.md) | 归档 | 第三方引入 | 中 | 规则需改造 | 维持归档 | P1 |
| [requesting-code-review](../archive/skills/requesting-code-review/SKILL.md) | 归档 | 第三方引入 | 中 | 条件可用 | 维持归档 | P1 |
| [receiving-code-review](../archive/skills/receiving-code-review/SKILL.md) | 归档 | 第三方引入 | 中 | 规则需改造 | 维持归档 | P1 |
| [webapp-testing](../skills/webapp-testing/SKILL.md) | 启用 | 原创改进（基于上游） | 高 | 条件可用 | 保留 | P2 |
| [property-based-testing](../skills/property-based-testing/SKILL.md) | 启用 | 第三方引入 | 高 | 条件可用 | 保留 | P2 |
| [code-review](../skills/code-review/SKILL.md) | 启用 | 原创改进（基于上游） | 中 | 条件可用 | 保留 | P1 |
| [windows-powershell-safe](../skills/windows-powershell-safe/SKILL.md) | 启用 | 原创改进（基于上游） | 高 | 条件可用 | 保留 | P2 |
| [variant-analysis](../skills/variant-analysis/SKILL.md) | 启用 | 原创改进（基于上游） | 高 | 条件可用 | 保留 | P1 |

## Git 隔离与交付

| Skill | 当前状态 | 创作归属 | 内容价值 | 当前就绪程度 | 建议 | 优先级 |
|---|---|---|---|---|---|---|
| [using-git-worktrees](../skills/using-git-worktrees/SKILL.md) | 启用 | 原创改进（基于上游） | 高 | 条件可用 | 保留 | P1 |
| [finishing-a-development-branch](../skills/finishing-a-development-branch/SKILL.md) | 启用 | 原创改进（基于上游） | 高 | 条件可用 | 保留 | P1 |

## 品牌、设计与 UI

| Skill | 当前状态 | 创作归属 | 内容价值 | 当前就绪程度 | 建议 | 优先级 |
|---|---|---|---|---|---|---|
| [ui-ux-pro-max](../skills/ui-ux-pro-max/SKILL.md) | 启用 | 原创改进（基于上游） | 高 | 条件可用 | 保留 | P1 |
| [brand](../skills/brand/SKILL.md) | 启用 | 原创改进（基于上游） | 高 | 条件可用 | 保留 | P2 |
| [design-system](../skills/design-system/SKILL.md) | 启用 | 原创改进（基于上游） | 高 | 条件可用 | 保留 | P1 |
| [ui-styling](../skills/ui-styling/SKILL.md) | 启用 | 原创改进（基于上游） | 中 | 条件可用 | 保留 | P1 |
| [design](../skills/design/SKILL.md) | 启用 | 原创改进（基于上游） | 高 | 条件可用 | 保留 | P1 |
| [canvas-design](../skills/canvas-design/SKILL.md) | 启用 | 原创改进（基于上游） | 中 | 条件可用 | 保留 | P2 |
| [slides](../archive/skills/slides/SKILL.md) | 归档 | 第三方引入 | 中 | 条件可用 | 维持归档 | P1 |
| [banner-design](../archive/skills/banner-design/SKILL.md) | 归档 | 第三方引入 | 中 | 依赖外部环境 | 维持归档 | P1 |
| [web-design-guidelines](../skills/web-design-guidelines/SKILL.md) | 启用 | 原创改进（基于上游） | 中 | 条件可用 | 保留 | P1 |
| [excalidraw-diagrams](../skills/excalidraw-diagrams/SKILL.md) | 启用 | 本仓原创 | 高 | 条件可用 | 保留 | P2 |

## 写作与内容

| Skill | 当前状态 | 创作归属 | 内容价值 | 当前就绪程度 | 建议 | 优先级 |
|---|---|---|---|---|---|---|
| [podcast-to-article](../skills/podcast-to-article/SKILL.md) | 启用 | 原创改进（基于上游） | 高 | 条件可用 | 保留 | P2 |
| [work-humanizer](../skills/work-humanizer/SKILL.md) | 启用 | 第三方引入 | 高 | 条件可用 | 保留 | P2 |

## 文档与办公

| Skill | 当前状态 | 创作归属 | 内容价值 | 当前就绪程度 | 建议 | 优先级 |
|---|---|---|---|---|---|---|
| [pdf-toolkit](../skills/pdf-toolkit/SKILL.md) | 启用 | 本仓原创 | 高 | 条件可用 | 保留 | P1 |

## 知识图谱与安全研究

| Skill | 当前状态 | 创作归属 | 内容价值 | 当前就绪程度 | 建议 | 优先级 |
|---|---|---|---|---|---|---|
| [graphify](../skills/graphify/SKILL.md) | 启用 | 原创改进（基于上游） | 高 | 依赖外部环境 | 保留 | P1 |
| [reverse-skill](../skills/reverse-skill/SKILL.md) | 启用 | 本仓原创 | 中 | 依赖外部环境 | 保留 | P1 |

## 技能维护与运行效率

| Skill | 当前状态 | 创作归属 | 内容价值 | 当前就绪程度 | 建议 | 优先级 |
|---|---|---|---|---|---|---|
| [writing-skills](../skills/writing-skills/SKILL.md) | 启用 | 原创改进（基于上游） | 中 | 条件可用 | 保留 | P2 |
| [using-superpowers](../archive/skills/using-superpowers/SKILL.md) | 归档 | 第三方引入 | 低 | 规则需改造 | 维持归档 | P1 |
| [token-efficient-workflow](../skills/token-efficient-workflow/SKILL.md) | 启用 | 本仓原创 | 中 | 条件可用 | 保留 | P1 |
| [suggesting-rules](../skills/suggesting-rules/SKILL.md) | 启用 | 本仓原创 | 低 | 条件可用 | 保留 | P2 |
| toolkit-map（外部） | 外部 | 本仓原创 | 高 | 依赖外部环境 | 保持外部 | P0 |
| [skill-scanner](../skills/skill-scanner/SKILL.md) | 启用 | 原创改进（基于上游） | 高 | 条件可用 | 保留 | P1 |
| [waiting-and-async](../skills/waiting-and-async/SKILL.md) | 启用 | 本仓原创 | 高 | 条件可用 | 保留 | P2 |
| [prompt-optimizer](../skills/prompt-optimizer/SKILL.md) | 启用 | 原创改进（基于上游） | 高 | 条件可用 | 保留 | P1 |

## 数据库与后端

| Skill | 当前状态 | 创作归属 | 内容价值 | 当前就绪程度 | 建议 | 优先级 |
|---|---|---|---|---|---|---|
| [supabase-postgres-best-practices](../skills/supabase-postgres-best-practices/SKILL.md) | 启用 | 第三方引入 | 高 | 条件可用 | 保留 | P2 |

## 如何维护

1. 新增/移走技能时更新 `catalog.json` 与安装 manifest。
2. 每项补真实用途、问题、改进、可观察验收场景和可定位的来源证据。
3. 运行 `python scripts/audit_skills.py --write` 更新派生文档，再运行 `--check` 校验一致性。
4. 安装参考 [安装指南](guides/installation.md)；验证范围见 [检查指南](guides/maintenance.md)。
