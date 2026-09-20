# agent-skills

本机 agent 技能的单一事实来源（single source of truth）。私有仓库。

## 为什么存在

这台机器上的 skill 分散在三个目录，而且已经出现**同名 skill 内容不一致**：

| 目录 | 数量 | 性质 |
|---|---|---|
| `%USERPROFILE%\.agents\skills` | 25 | Cursor 实际加载；本地改造过的版本 |
| `%USERPROFILE%\.codex\skills` | 3 | Codex 侧入口 |
| `%USERPROFILE%\.dsh\skills` | 18 | 从第三方市场同步而来，**不归本仓库管** |

`.agents\skills` 与 `.dsh\skills` 有 11 个同名 skill，且**全部文件内容不同**。这不是"新版本覆盖旧版本"，
而是两条血脉：前者是英文上游系 + 本地改造，后者是市场的中文翻译系（来源 `gitcode.com/weibaohui/ntd-resource.git`，
由 `.dsh/skills-market-sync.json` 自动同步）。

本仓库的做法：**只做 `.agents` / `.codex` 的权威来源，不碰 `.dsh`**。`.dsh\skills` 交给它自己的同步机制，
往那里建联接会被下次同步覆盖。

## 目录结构

```
skills/<name>/          27 个技能，每个是一个真目录
shared/                 被 skill 正文引用为「唯一权威来源」的共享文件
manifest.json           每个技能的原始归属（origin）与默认安装目标（defaultTargets）
install.ps1             安装/卸载器，用目录联接把仓库挂到各 agent 的技能目录
ATTRIBUTION.md          第三方来源与署名
```

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
