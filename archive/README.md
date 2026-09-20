# archive —— 保全但未激活

这里的东西**不在 `install.ps1` 的接管范围内**，不会被联接到任何 agent 的技能目录。
它们曾经只存在于 `%USERPROFILE%\tools\skill-backup-20260918\`——一个不受版本控制的手工备份目录——
在那个目录被清理前抢救进来。

要启用其中某一项，把它移进 `skills/`（skill）或按下面的说明安置（规则），然后跑 `install.ps1`。

## skills/（5 个）

全部是英文第三方产物，来源见下表。逐个与备份原件比对过文件清单与字节数，一致。

| skill | 文件 | 来源 |
|---|---|---|
| `ask-questions-if-underspecified` | `SKILL.md`、`openai.yaml`、`trail-of-bits-mark.svg` | 含 Trail of Bits 标识，出自该组织的技能集 |
| `banner-design` | `SKILL.md`、`banner-sizes-and-styles.md` | `metadata.author: claudekit`，`license: MIT`，v1.0.0 |
| `slides` | `SKILL.md` + 5 个参考文档 | `metadata.author: claudekit`，v1.0.0 |
| `best-of-n-solving` | `SKILL.md` | superpowers 一系 |
| `dispatching-parallel-agents` | `SKILL.md` | superpowers 一系 |

依赖提示：`banner-design` 的正文声明自己要调用 `ui-ux-pro-max`、`frontend-design`、`ai-artist`、
`ai-multimodal`。前两个在仓库里（`ui-ux-pro-max` 已收录；`frontend-design` 没有），后两个没有。
单独启用它会缺依赖。

你后来自己写的 `parallel-agents` 覆盖了同样的场景（并行子代理、多方案择优），
而 `best-of-n-solving` 与 `dispatching-parallel-agents` 是它的两个上游原型，所以留在这里存档而非启用。

## rules/（2 个）

Cursor 规则文件（`.mdc`）。当前 `~\.cursor` 下**没有任何 `.mdc`**，也就是说这两条规则现在处于休眠状态。

| 文件 | 用途 |
|---|---|
| `deepseek-speed.mdc` | 全局提速规则（`alwaysApply: true`）：精简上下文、利用 DeepSeek 官方 API 前缀缓存、减少输出与重复读取 |
| `graphify.mdc` | **项目级**模板（`alwaysApply: true`）：告知 agent 本项目在 `graphify-out/` 有知识图谱 |

安置方式不在 `install.ps1` 的职责范围内：

- `deepseek-speed.mdc` 是全局行为规则 → 放入 Cursor 设置的全局规则，或某个项目的 `.cursor\rules\`
- `graphify.mdc` 是每个项目各自生成的模板 → 当某个项目跑过 `graphify` 后，把它复制进该项目的 `.cursor\rules\`
