# agent-skills

本机 agent 技能的单一事实来源（single source of truth）。私有仓库。

## 为什么存在

这台机器上的 skill 原本分散在三个目录，而且已经出现**同名 skill 内容不一致**：

| 目录 | 数量 | 性质 |
|---|---|---|
| `%USERPROFILE%\.agents\skills` | 25 | Cursor 实际加载；本地改造过的版本 |
| `%USERPROFILE%\.codex\skills` | 3 | Codex 侧入口 |
| `%USERPROFILE%\.dsh\skills` | 18 | DSH Desktop（网页版数据根）从第三方市场同步而来，**不归本仓库管**；该目录已于 2026-09-20 迁至 `%APPDATA%\dsh-desktop\harness\skills`，见下方记录 |

`.agents\skills` 与 `.dsh\skills` 有 11 个同名 skill，且**全部文件内容不同**。这不是"新版本覆盖旧版本"，
而是两条血脉：前者是英文上游系 + 本地改造，后者是市场的中文翻译系（来源 `gitcode.com/weibaohui/ntd-resource.git`，
由 `.dsh/skills-market-sync.json` 自动同步）。

本仓库的做法：**只做 `.agents` / `.codex` 的权威来源，不碰 `.dsh`**。`.dsh\skills` 交给它自己的同步机制，
往那里建联接会被下次同步覆盖。

> **2026-09-20 记录**：本仓库建立当天，整个 `%USERPROFILE%\.dsh` 目录（含 `skills\`、`skills-management\market\`
> 市场克隆、`skills-market-sync.json`）从磁盘上消失，不在回收站中。查明如下：
>
> - `~\.dsh` 是 DSH Desktop（DeepSeek 客户端）**网页版**的数据根 —— 见 `main\index.js:17158`
>   `defaultWebHome() { return join(homedir(), ".dsh") }`。桌面版的数据根是
>   `%APPDATA%\dsh-desktop\harness`。
> - 桌面版自带一个"把网页版数据导入桌面版"的流程，其决策记录 `harness\.web-import-decision.json`
>   写的是 `{"decision":"skipped","source":"C:\\Users\\Administrator\\.dsh","at":"2026-09-20T06:24:46Z"}`，
>   即**那次导入被跳过**，不是它搬的。
> - 客户端插件市场的日志 `harness\profiles\web\.dsh-market\log.ndjson` 显示，14:33–15:02 期间
>   正在连续安装插件，其中 14:52:31 更新了 `dshmarket -> dshmarket@1.50.0`。`.dsh` 的消失
>   （14:41 尚在、14:57 已无）正落在这个窗口内。
> - 多个已装 UI 插件把 `homedir()/.dsh` 作为 home 回退路径（`dsh-client-ui-skill-explorer:853`、
>   `dsh-client-ui-market:76`、`dsh-client-ui-plugin-manager:473`、`dsh-client-ui-preset-center:75`、
>   `dsh-client-ui-git-graph:621`），其中 `preset-center` 的 `moveDirectory()` 会在校验复制结果一致后
>   删除源目录。**无法指认具体是哪一行执行的删除**，但可确定删除来自客户端的技能/插件管理这一层。
> - **内容没有丢失**：18 个中文 skill 原样存在于 `%APPDATA%\dsh-desktop\harness\skills\`，逐个
>   `SKILL.md` 字节数与迁移前一致；`settings.yaml`、`.credentials.yaml`、`sessions`、`storages`、
>   `attachments` 也都在。
> - 未随迁的：`skills-management`（`gitcode.com/weibaohui/ntd-resource.git` 的 47 个集合克隆）、
>   `skills-market-sync.json`、`session-index.db`、`undo-snapshots`、`xray`、`cordis.patch.yml`、
>   `npm-deepseek-ai-scope.txt`。它们不在客户端导入流程的清单里（见 `main\index.js:17141` 的
>   `HOME_FILES` / `HOME_DIRECTORIES`）。市场克隆可重新 clone 复原。
>
> 这条记录的用途：DSH Desktop 的数据根**不稳定**（今天刚整体迁走一次），任何放在 `~\.dsh` 下的东西
> 都不该被当作长期存储。

## 目录结构

```
skills/<name>/          27 个技能，每个是一个真目录（install.ps1 接管）
shared/                 被 skill 正文引用为「唯一权威来源」的共享文件
archive/                保全但不激活：5 个孤本 skill + 2 个休眠的 Cursor 规则
manifest.json           每个技能的原始归属（origin）与默认安装目标（defaultTargets）
install.ps1             安装/卸载器，用目录联接把仓库挂到各 agent 的技能目录
ATTRIBUTION.md          第三方来源与署名
```

`skills/` 是**激活集**，`archive/` 是**存档集**，区别在于 `install.ps1` 只接管前者。
两者的详细区分见 `archive/README.md`。

## 收录判据

**收录（27 个，9.8 MB）**

1. **市场取不到**（7 个）：`env-doctor`、`graphify`、`requirement-understanding`、`reverse-skill`、
   `token-efficient-workflow`、`deepseek-subagent-orchestration`、`suggesting-cursor-rules`。
   第三方市场仓库 `weibaohui/ntd-resource` 里没有同名条目，丢了没地方找。
2. **市场有但本地已改造**（20 个）：逐个与市场版比对过 `SKILL.md` 哈希，**全部不同**。差异不是细节级的：

   | skill | 市场版 | 本地版 |
   |---|---|---|
   | `design-system` | 3 KB | 175 KB |
   | `brainstorming` | 5 KB | 79 KB |
   | `writing-skills` | 123 KB | 105 KB |
   | `canvas-design` | 5,427 KB | 5,427 KB（字体相同，`SKILL.md` 不同） |

   重新同步市场得到的不是同一份东西，所以必须归档。

**排除**

| 对象 | 理由 |
|---|---|
| `.dsh\skills` 全部 18 个 | 市场自动同步的第三方中文译本，重同步即可复原；建联接会被同步覆盖 |
| `toolkit-map` | 已经是独立公开仓库 `haxsd/toolkit-map`，纳进来会变成两处管理。恢复方式见下 |
| `canvas-design` 的字体等二进制资产 | 未排除，但占了 5.4 MB / 9.8 MB。若想让仓库瘦身，这是首选裁剪对象 |

**存档集（额外 5 个 + 2 个规则）**

2026-09-20 清理手工备份目录 `%USERPROFILE%\tools\skill-backup-20260918\` 时，发现其中 5 个 skill
与 2 个 Cursor 规则（`.mdc`）在别处**没有第二份**，抢救进 `archive/`：

| 对象 | 情况 |
|---|---|
| `ask-questions-if-underspecified` | 出自 Trail of Bits 技能集（带该组织标识） |
| `banner-design`、`slides` | `author: claudekit`，MIT；`banner-design` 依赖 `frontend-design`、`ai-artist`、`ai-multimodal`，仓库里不全 |
| `best-of-n-solving`、`dispatching-parallel-agents` | superpowers 一系；你后来写的 `parallel-agents` 已覆盖同一场景，故存档而不启用 |
| `deepseek-speed.mdc` | 全局提速规则（前缀缓存、精简上下文），当前未安装在任何位置 |
| `graphify.mdc` | 项目级模板，告知 agent 项目在 `graphify-out/` 有知识图谱 |

判定"没有第二份"的方法：逐个在 `.agents\skills`、`.codex\skills`、本仓库、以及当时的 `.dsh\skills`
四处查同名目录。抢救后逐文件比对文件清单与字节数，确认与原备份一致。

## 安装

```powershell
# 先看会做什么，不落盘
.\install.ps1 -DryRun

# 按 manifest 各就各位（24 个 -> .agents\skills，3 个 -> .codex\skills）
.\install.ps1

# 灰度：只装指定的
.\install.ps1 -Only systematic-debugging,writing-plans

# 全部塞进某一个目录
.\install.ps1 -Target agents
```

安装器是幂等的，并且**覆盖真实目录前会先备份**到 `<目录>.backup-<时间戳>\`，不会静默删除现有内容。

卸载只删除本仓库建立的联接，不动真实目录：

```powershell
.\install.ps1 -Uninstall -DryRun
.\install.ps1 -Uninstall
```

**为什么用目录联接（junction）而不是符号链接**：Windows 上 junction 不需要管理员权限或开发者模式；
而且 symlink 提交进 git for Windows 会退化成普通文本文件，联接放在技能目录侧、由脚本生成才是稳的。

## 换机恢复

```powershell
git clone git@github.com:haxsd/agent-skills.git $env:USERPROFILE\Projects\agent-skills
cd $env:USERPROFILE\Projects\agent-skills
.\install.ps1
```

`shared\token-efficiency-rules.md` 会被联接到 `%USERPROFILE%\tools\shared\`——`token-efficient-workflow`
把该文件当作唯一权威来源，而它此前不在任何版本控制里，所以一并收进来了。

## 仓库外的依赖

以下被 skill 正文引用，但**不在本仓库**，换机需另行获取：

| 路径 | 关联 skill | 怎么恢复 |
|---|---|---|
| `%USERPROFILE%\tools\reverse-skill` | `reverse-skill`（本仓库内只是 4.9 KB 的路由入口） | `git clone https://github.com/zhaoxuya520/reverse-skill.git`；技能包本体 49 个模块 / 89 个 `SKILL.md` |
| `%USERPROFILE%\tools\node22` | `reverse-skill` 的 JS 工具链 | 技能包要求 Node 22.12+，系统 `node` 是 16.x |
| `%USERPROFILE%\Projects\toolkit-map` | `toolkit-map` | `git clone https://github.com/haxsd/toolkit-map.git`；或直接 `git clone` 到 `.agents\skills\toolkit-map` |

## 正文里的绝对路径

技能正文刻意写绝对路径（这是 `toolkit-map` 的做法：给 agent 确定路径，不让它靠 PATH 猜）。
三处指向 `C:\Users\Administrator\`：

- `skills\reverse-skill\SKILL.md:15`、`:70`
- `skills\token-efficient-workflow\SKILL.md:8`

同账户重建的机器不受影响；换用户名部署时需改这三处。

## 维护约定

改 skill 请**改本仓库**，不要在 `.agents\skills\<name>` 里改——那里是联接，改的是同一份文件。
但新建 skill 时要注意：`.agents\skills` 不该出现非联接的真实目录，否则它不在版本控制内。
