# agent-skills

[中文](README.md) · [English](README-EN.md)

> 按用途分类的 agent 技能库：38 个启用技能、11 个归档技能、10 个用途分类，按目录索引查、按需安装。

## 核心能力

- **38 个启用技能**：覆盖需求与规划、实现与代理编排、质量与调试、Git 交付、设计与 UI、写作、文档与办公、知识图谱与安全研究、技能维护与提示词优化、数据库与后端十类，全部在 `skills/<name>/` 保持稳定路径。
- **11 个归档技能**：历史技能与草稿放在 `archive/`，默认不安装，可作维护参考。
- **目录索引**：分类、价值判断与升级建议写入 `catalog.json`，人读版本见[分类目录](docs/catalog.md)。
- **来源可溯**：每项技能登记来源（第三方引入 / 原创 / 原创改进 / 待核验）与许可证，见[署名说明](ATTRIBUTION.md)与[逐项来源登记](docs/sources/skill-provenance.json)。
- **可卸载安装**：`install.ps1` 用目录联接把技能挂到各 agent 目录，仓库保存内容，卸载只删联接、保留真实目录。

## 安装

在仓库根目录用 Windows PowerShell 先演练：

```powershell
.\install.ps1 -DryRun
.\install.ps1 -Only deepseek-subagent-orchestration -Target codex -DryRun
.\install.ps1 -Only deepseek-subagent-orchestration -Target codex
```

完整安装、卸载与外部源配置见[安装指南](docs/guides/installation.md)。[DeepSeek API 助手](skills/deepseek-subagent-orchestration/SKILL.md)保留当前 GPT 主代理，在用户明确要求 DeepSeek 委派时把独立工作块交给自己的 `deepseek-flash` API；需要 Codex CLI 进程和完整本机工具链时改用 `deepseek-subagents`，两条路线互斥。

## 仓库结构

```text
skills/    启用的技能，按名称保留稳定路径
archive/   历史技能、规则与草稿，默认不安装
shared/    共用资源
docs/      分类索引、安装维护指南与来源登记
scripts/   仓库检查与生成工具
tests/     离线回归测试
```

`catalog.json` 保存人工判断，`manifest.json` 管理安装目标，`external.json` 登记独立维护的 [toolkit-map](https://github.com/haxsd/toolkit-map)。

## 维护

新增或清理技能时先查[分类目录](docs/catalog.md)，按[维护指南](docs/guides/maintenance.md)更新索引并跑仓库检查。第三方技能需固定上游版本、保留许可证；原创改进保留上游作者与许可。

## 文档

- [分类目录](docs/catalog.md)
- [安装指南](docs/guides/installation.md)
- [维护指南](docs/guides/maintenance.md)
- [文档导航](docs/README.md)

## 许可证

本仓库自身内容以 [MIT](LICENSE) 提供；各技能随附的第三方材料仍按其自身许可，见 [NOTICE](NOTICE)。
