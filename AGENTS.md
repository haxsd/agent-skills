# AGENTS.md

## 仓库边界：内部资料不进公开仓库

本仓库对陌生人可见，只放技能集本身与贡献者需要的内容。**内部资料**——逐项审查、整改路线、
机器检查与验证记录、仓库历史（含当时的账号与路径）、早期草稿——写进私有记录仓库
`haxsd/haxsd-dev-records` 的 `agent-skills/` 分区。

公开仓库不得出现这些路径：`docs/history/**`、`docs/reviews/**`、`docs/validation/**`、
`archive/legacy/**`、`HANDOFF.md`、`BRANCH_ISOLATION.md`、`docs/plans/**`、`docs/superpowers/**`、
`docs/devin-router-vendor-evidence.md`。CI 的 `records-guard` 任务会在当前树或历史里发现它们时失败。

`scripts/audit_skills.py` 仍然把审查与检查报告写到 `docs/reviews/`、`docs/validation/`，这两处已在
`.gitignore` 里：报告是本机/内部的产物，不要提交。公开的派生文档只有 `docs/catalog.md`。

提交信息里也别写内部细节（账号、机器路径、真实用量数字），这些写进记录仓库的提交信息。
收尾检查：在记录仓库里跑 `sync-records.ps1`（扫描五个公开仓库的当前树与历史，发现内部资料即报错）。
