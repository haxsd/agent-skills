# agent-skills

我们收藏与改造的 agent 技能库，也是本机通用与 Codex 技能的维护来源。当前包含 **31 个启用技能、5 个归档技能、1 个外部技能登记**。

本轮精选新增：Web 应用测试、MCP 服务开发、Postgres 最佳实践、属性测试。见 [收录理由、去重与验证边界](docs/curation-2026-09-30.md)；每项附上游固定版本及许可证。

## 从这里查找

- [按用途分类的目录](docs/catalog.md)：8 个类别，包含价值、就绪程度、建议动作与优先级。
- [逐个审查与升级建议](docs/skill-review.md)：36 个库内技能 + 1 个外部接入，每项都有来源定位和验收场景。
- [合并方案与整改路线](docs/review-roadmap.md)：重叠职责、保留能力、整改顺序和实测边界。
- [离线工具验证](docs/smoke-results.json) / [静态检查结果](docs/audit-findings.json)。
- [Codex + DeepSeek API skill](skills/deepseek-subagent-orchestration/SKILL.md) / [真实调用验证](docs/deepseek-validation.json)：主代理保留当前 GPT，小任务走自己的 API。

分类采用逻辑索引，保持 skills/<name>/ 平铺，兼容安装器与现有引用。合并、归档均为审查建议，当前激活集尚未调整。

## 八类技能

| 类别 | 代表技能 |
|---|---|
| 需求与规划 | requirement-understanding / brainstorming / writing-plans |
| 实现与代理编排 | executing-plans / subagent-driven-development / parallel-agents / deepseek-subagent-orchestration |
| 质量、调试与审查 | env-doctor / systematic-debugging / test-driven-development / code review 系列 |
| Git 隔离与交付 | using-git-worktrees / finishing-a-development-branch |
| 品牌、设计与 UI | ui-ux-pro-max / brand / design-system / ui-styling / design / canvas-design |
| 知识图谱与安全研究 | graphify / reverse-skill |
| 技能维护与运行效率 | writing-skills / token-efficient-workflow / suggesting-cursor-rules / 外部 toolkit-map |
| 数据库与后端 | supabase-postgres-best-practices |

## 安装

安装目标的权威来源仍是 manifest.json / external.json。通用 agents 组展开为 agents/cursor/devin/claude；Codex 专属条目只进入 codex。

```powershell
# 先检查会发生的变化
.\install.ps1 -DryRun

# 指定库内技能与平台
.\install.ps1 -Only systematic-debugging,writing-plans -Target codex -DryRun

# 按 manifest 安装全部启用技能
.\install.ps1

# 卸载演练
.\install.ps1 -Uninstall -DryRun
```

安装器使用 Windows junction，现有真实目录先备份。external.json 仍含旧账户路径，使用前按实际 checkout 配置。当前 -Only 不限制 external/shared，演练输出需一起查看。

## 维护与检查

```powershell
# 使用已确认的 Python 3，无第三方库依赖
python scripts/audit_skills.py --write
python scripts/audit_skills.py --check
python -m unittest discover -s tests -q

# Node 必须传入已确认的绝对路径
python scripts/smoke_skills.py --node '<Node 的绝对路径>'

# UI/UX 数据校验
python skills/ui-ux-pro-max/scripts/validate_data.py
```

catalog.json 保存人工分类与判断，派生文档由 audit 脚本生成。检查覆盖、名称、证据和引用线索；不会执行技能，也不替代完整 YAML 校验或真实任务评估。--check 检查派生结果是否同步，已知 warning/hint 不等于新错误。

smoke 在临时项目运行本地工具，不调用付费 API、不安装依赖、不改用户项目。UI/UX 全量测试仍受缺失维护脚本阻塞，不能声称整库测试全通过。

## 结构与来源

```text
skills/<name>/       启用集，install.ps1 接管
archive/             历史技能、规则与草稿，保持不启用
shared/              共享效率规则
catalog.json         分类、人工审查与证据
docs/                分类目录、逐项审查、整改路线与验证记录
scripts/             仓库级审查与离线验证工具
tests/               审查与 API 助手的离线标准库测试
manifest.json        安装目标与原始归属
external.json        独立维护的外部技能
```

多数技能来自第三方并经本地改造，见 [ATTRIBUTION.md](ATTRIBUTION.md)。本轮 4 个新增项已记录版本与许可；历史内容尚未逐项核验，价值审查不代表原创或整库分发许可认证。

旧目录清理、DSH 迁移、原始统计与换机记录完整保存在 [仓库历史说明](docs/repository-history.md)，日期、账号路径和工具版本属于当时记录。
