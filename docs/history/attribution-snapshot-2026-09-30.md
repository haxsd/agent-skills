# 来源与署名

本仓库是**归档**，不是原创作品集。多数 `SKILL.md` 的作者是别人，其中一部分经过本地改造。

## 2026-09-30 新增的已追溯内容

| 技能 | 作者 / 上游 | 许可 |
|---|---|---|
| webapp-testing、mcp-builder | [Anthropic](https://github.com/anthropics/skills) | 各技能 Apache-2.0 |
| supabase-postgres-best-practices | [Supabase](https://github.com/supabase/agent-skills) | MIT |
| property-based-testing | [Trail of Bits](https://github.com/trailofbits/skills) | CC-BY-SA-4.0 |

完整许可证随各技能目录保留；作者、固定 commit、上游路径及本地改动见每项 `UPSTREAM.json` 与 [来源汇总](../sources/curation-sources.json)。改动内容继续按对应上游许可分发，不能用这 4 项的许可覆盖历史内容。下文历史许可未核实的说明仍适用于原有技能。

判断依据是 `.dsh\skills-management\market\skills\`——第三方技能市场 `gitcode.com/weibaohui/ntd-resource.git`
的本地克隆，含 47 个上游集合。下表区分「能否从这个市场重新取回」，**不等于**「是否本人原创」。

## 一、市场无同名条目（14 个）

从该市场重新同步取不回来，只能靠本仓库保全。

其中一部分明确是本机自研/改编（中文撰写、依赖本机路径）：

- `env-doctor`
- `requirement-understanding`
- `reverse-skill`（只是 4.9 KB 的路由入口；技能包本体是 `zhaoxuya520/reverse-skill`，见下）
- `token-efficient-workflow`（依赖 `shared/token-efficiency-rules.md`）
- `deepseek-subagent-orchestration`
- `suggesting-cursor-rules`

另一部分属 superpowers 一系的开发流程技能，市场恰好没有收录，但上游另有出处（未逐一考证版本）：

- `executing-plans`、`writing-plans`
- `requesting-code-review`、`receiving-code-review`
- `finishing-a-development-branch`
- `using-git-worktrees`
- `verification-before-completion`

`graphify` 单独说明：市场无对应条目，但它是第三方产物（`/graphify` 命令式结构、含 `.graphify_version`），
上游出处未能确定。

## 二、市场有同名条目，但本地版内容不同（13 个）

逐个比对过 `SKILL.md` 的 MD5，**全部不一致**，所以重新同步市场得到的不是同一份东西。差异不是细节级的：
`design-system` 市场 3 KB / 本地 175 KB，`brainstorming` 市场 5 KB / 本地 79 KB。

| 本仓库 skill | 市场侧对应集合 |
|---|---|
| `brainstorming` | `mohitagw15856-pm-claude-skills` |
| `subagent-driven-development` | `sickn33-agentic-awesome-skills` |
| `systematic-debugging` | `sickn33-agentic-awesome-skills` |
| `using-superpowers` | `sickn33-agentic-awesome-skills` |
| `writing-skills` | `sickn33-agentic-awesome-skills` |
| `ui-ux-pro-max` | `sickn33-agentic-awesome-skills` |
| `test-driven-development` | `addyosmani-agent-skills` |
| `parallel-agents` | `sickn33-agentic-awesome-skills`（本地改写为中文） |
| `canvas-design` | `anthropics-skills` |
| `ui-styling` | `nextlevelbuilder-ui-ux-pro-max-skill` |
| `brand` | `nextlevelbuilder-ui-ux-pro-max-skill` |
| `design-system` | `affaan-m-ECC` |
| `design` | `mxyhi-ok-skills`（`minimax-pdf/design`） |

`using-superpowers`、`writing-skills`、`brainstorming`、`subagent-driven-development`、
`systematic-debugging`、`test-driven-development` 等的命名与结构指向 obra/superpowers 一系。

## 三、署名与许可证

上面这些上游集合的许可证**未逐一核实**，也没有随仓库携带许可证副本。仓库设为私有正是出于这个考虑：
第三方内容未经许可不适合重新公开分发。若日后要转为公开，需要先：

1. 逐个确认上游许可证与署名要求；
2. 把自研部分与第三方部分拆开；
3. 第三方部分改用 git submodule 引用上游，或不予收录。

## 四、安全提示

`reverse-skill` 指向的技能包内含渗透与绕过类模块，其中
`skills/pentest-tools/src-hunter/references/` 下的 payload 参考文档会被 Windows Defender 标记为
`SCRIPT0049 / SCRIPT0065 / SCRIPT0066`（它们是 Markdown 文档，不是可执行文件）。用途限于对自有目标的
授权测试、CTF 与防御性分析；不要为了绕过杀软告警而关闭防护。
