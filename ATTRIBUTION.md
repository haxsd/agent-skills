# 来源与署名

本仓库收藏和改造第三方技能，同时保留本机专用技能。各技能的许可按原来源分别适用，不能用某一项的许可证覆盖整个仓库。

| 已追溯内容 | 来源 | 许可 |
|---|---|---|
| webapp-testing、mcp-builder | [Anthropic](https://github.com/anthropics/skills) | 各技能 Apache-2.0 |
| supabase-postgres-best-practices | [Supabase](https://github.com/supabase/agent-skills) | MIT |
| property-based-testing | [Trail of Bits](https://github.com/trailofbits/skills) | CC-BY-SA-4.0 |
| podcast-to-article | [orange2ai/podcast-to-article](https://github.com/orange2ai/podcast-to-article) | MIT |
| excalidraw-diagrams（wrapper；CLI 不入库） | [@excalidraw/cli](https://github.com/excalidraw/cli) | CLI 为 MIT；skill 文本由本仓库维护 |
| work-humanizer（slim：SKILL.md / tells.md / check.py） | [phuryn/work-humanizer](https://github.com/phuryn/work-humanizer) | MIT |
| windows-powershell-safe（slim；另附团队 repros） | [Misaka-Mikoto-Tech/agent-skills · powershell-safe-invocation](https://github.com/Misaka-Mikoto-Tech/agent-skills)（stop rules 文字借鉴 [agent-shells/powershell-skills](https://github.com/agent-shells/powershell-skills)） | MIT |

完整许可证随技能目录保留；固定上游 commit、路径、作者及本地改动见各项 `UPSTREAM.json` 和 [来源清单](docs/sources/curation-sources.json)。

原有技能的市场对应关系、来源判断与历史许可限制完整保存在 [署名历史快照](docs/history/attribution-snapshot-2026-09-30.md)。市场中存在同名条目不代表同一作者或同一版本；原有内容的许可未全部重新核验，仓库保持私有。

安全研究技能只在用户已授权的目标和范围内使用；具体依赖与使用边界见对应 skill。归档目录里的规则和草稿不自动安装。

2026-10-06：新增本机自有 development-workflow、code-review、deepseek-subagents；web-design-guidelines 保留原 Vercel 作者元数据，规范源为 https://github.com/vercel-labs/web-interface-guidelines ，尚未重新核验其分发许可，不改变仓库私有状态。
2026-10-09：新增 podcast-to-article（MIT，固定上游 commit）；新增本仓库维护的 excalidraw-diagrams wrapper（依赖官方 MIT CLI，不 vendoring 源码）。
2026-10-11：新增 work-humanizer（MIT，slim 固定上游 commit；不含 evidence/）。
2026-10-11：新增 windows-powershell-safe（MIT slim，固定上游 commit；另借鉴 agent-shells stop rules 文字；附团队经验/文档翻车样例）。
