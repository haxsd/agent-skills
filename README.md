# agent-skills

我们的 agent 技能收藏与维护仓库：**35 个启用技能 · 5 个归档技能 · 8 个用途分类**。技能目录保持稳定，分类、价值判断和升级建议通过索引查找。

[分类目录](docs/catalog.md) · [安装指南](docs/guides/installation.md) · [逐项审查](docs/reviews/skill-review.md) · [整改路线](docs/reviews/roadmap.md) · [全部文档](docs/README.md)

## 按用途查找

| 类别 | 代表技能 |
|---|---|
| 需求与规划 | requirement-understanding、brainstorming、writing-plans |
| 实现与代理编排 | executing-plans、parallel-agents、deepseek-subagent-orchestration、mcp-builder |
| 质量、调试与审查 | systematic-debugging、code review、webapp-testing、property-based-testing |
| Git 隔离与交付 | using-git-worktrees、finishing-a-development-branch |
| 品牌、设计与 UI | ui-ux-pro-max、brand、design-system、ui-styling、design、canvas-design |
| 知识图谱与安全研究 | graphify、reverse-skill |
| 技能维护与运行效率 | writing-skills、token-efficient-workflow、toolkit-map（外部） |
| 数据库与后端 | supabase-postgres-best-practices |

## 安装与使用

从仓库根目录运行，先查看演练结果：

```powershell
.\install.ps1 -DryRun
.\install.ps1 -Only deepseek-subagent-orchestration -Target codex -DryRun
```

安装通过 Windows junction 指向此仓库；完整安装、卸载和外部源配置见 [安装指南](docs/guides/installation.md)。[DeepSeek API 助手](skills/deepseek-subagent-orchestration/SKILL.md) 保留当前 GPT 主代理，默认把独立工作块交给自己的 `deepseek-flash` API；支持受限文件工具和命名检查，凭据单独配置。

## 仓库结构

```text
skills/        当前启用的技能，按名称保留稳定路径
archive/       历史技能、规则与草稿，默认不安装
shared/        共用资源
docs/          分类索引、指南、审查、验证和历史资料
scripts/       仓库检查与生成工具
tests/         离线回归测试
```

`catalog.json` 保存人工判断，`manifest.json` 管理安装目标，`external.json` 登记独立维护的技能。维护步骤和自动检查范围见 [维护指南](docs/guides/maintenance.md)。

每个 skill 的价值、依赖、重复与升级建议都在审查报告中；合并/归档建议尚未自动实施。[四项新增技能](docs/reviews/curation-2026-09-30.md) 带固定上游版本和许可证。历史内容的来源与许可边界见 [署名说明](ATTRIBUTION.md)。
