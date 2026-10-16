# agent-skills

我们的 agent 技能收藏与维护仓库：**36 个启用技能 · 11 个归档技能 · 9 个用途分类**。技能目录保持稳定，分类、价值判断和升级建议通过索引查找。

[分类目录](docs/catalog.md) · [安装指南](docs/guides/installation.md) · [全部文档](docs/README.md)

## 按用途查找

| 类别 | 代表技能 |
|---|---|
| 需求与规划 | requirement-understanding、writing-plans |
| 实现与代理编排 | execute-plan、parallel-agents、deepseek-subagent-orchestration、mcp-builder |
| 质量、调试与审查 | env-doctor、systematic-debugging、variant-analysis、code-review、webapp-testing、property-based-testing、windows-powershell-safe |
| Git 隔离与交付 | using-git-worktrees、finishing-a-development-branch |
| 品牌、设计与 UI | ui-ux-pro-max、brand、design-system、ui-styling、design、canvas-design、excalidraw-diagrams |
| 写作与内容 | podcast-to-article、work-humanizer |
| 知识图谱与安全研究 | graphify、reverse-skill |
| 技能维护与运行效率 | skill-scanner、writing-skills、token-efficient-workflow、waiting-and-async、toolkit-map（外部） |
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
docs/          分类索引、安装维护指南与公开来源登记
scripts/       仓库检查与生成工具
tests/         离线回归测试
```

`catalog.json` 保存人工判断，`manifest.json` 管理安装目标，`external.json` 登记独立维护的技能。维护步骤和自动检查范围见 [维护指南](docs/guides/maintenance.md)。

每个 skill 的价值、依赖、重复与升级建议记录在维护者的内部审查里；入口收敛（合并与归档）分批实施。
**每项技能都登记来源**：第三方引入、本仓原创、原创改进（基于上游）或待核验，见 [署名说明](ATTRIBUTION.md) 与 [逐项来源登记](docs/sources/skill-provenance.json)。
原创改进保留上游作者和许可；原创声明仅覆盖本仓贡献。新引入第三方技能需固定上游版本并保留许可证，历史尚未查明的版本与许可如实标为待核验。
