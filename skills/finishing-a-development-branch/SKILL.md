---
name: finishing-a-development-branch
description: 在实现完成、需要合并、创建 PR、保留分支或清理工作时使用。复用已有授权和有效验证证据，正确区分普通仓库、linked worktree、detached HEAD 与 submodule；破坏性操作必须先确认。Use when implementation is complete and integration is the next step.
---

# 完成开发分支

交付的目标不是“再跑一遍所有测试、再问一遍菜单”，而是在不丢成果的前提下，把当前状态安全地变成用户选择的交付结果。

## 0. 先读取已有决定

检查对话、计划、仓库说明和当前任务上下文，确认用户是否已经明确选择：

- 本地合并到某个基线分支
- 推送并创建 PR / MR
- 保留分支和工作区
- 丢弃成果

用户已经选择时，直接沿用它，不再展示菜单。只有交付方式确实未定，才在验证后询问一次。

## 1. 记录状态与验证证据

先采集当前状态：

```bash
git status --porcelain=v1 -uall
git branch --show-current
git rev-parse HEAD
git rev-parse --show-toplevel
git log --oneline --decorate -n 10
```

按 [references/verification.md](references/verification.md) 的证据契约判断：

- 验证必须绑定当前代码状态、命令和真实输出。
- 状态未变且已有通过的证据，可以直接复用，不重复运行只为“再说一遍”。
- 代码、依赖或配置发生变化时，只补跑受影响的检查；合并或推送前再核对目标状态的集成门禁。
- 如果关键验证不可运行，明确报告缺口，不要用“应该没问题”替代。

**测试或构建失败时停止交付。** 保留分支和工作区，报告失败和仍未验证的范围。

## 2. 判断当前环境

```bash
git rev-parse --show-toplevel
git rev-parse --git-dir
git rev-parse --git-common-dir
git rev-parse --show-superproject-working-tree
```

**Submodule guard：** `GIT_DIR != GIT_COMMON` 也出现在 submodule 中。`git rev-parse --show-superproject-working-tree` 返回非空路径时，这是父项目里的 submodule，不要把它当成 linked worktree，也不要清理其工作区。

排除 submodule 后：

| 状态 | 判断 | 默认处理 |
|---|---|---|
| `GIT_DIR == GIT_COMMON` | 普通仓库 | 无额外 worktree 可清理 |
| `GIT_DIR != GIT_COMMON`，有命名分支 | linked worktree | 先确认归属，再决定是否清理 |
| `GIT_DIR != GIT_COMMON`，detached HEAD | 通常是外部管理的试验工作区 | 默认保留，不按自有 worktree 删除 |

路径所在目录、目录名和当前分支都不足以证明 worktree 由谁创建。

## 3. 判断 worktree 归属

按以下顺序取权威证据：

1. 宿主工作区管理工具提供的 attachment、创建记录或工作区清单。
2. 本次对话中明确的创建动作：哪个工具创建、创建了哪个路径、由谁负责清理。
3. 用户明确说明该工作区归当前任务所有。

以下证据**只能证明存在，不能证明归属**：

- 路径在 `.worktrees/`、`worktrees/` 或其他常见目录下
- `git worktree list --porcelain` 中存在该项
- 目录名看起来像当前分支或任务名

没有归属证据时，把 worktree 视为外部管理并保留。不要为了“干净”清理其他任务或人工创建的工作区。

确认归当前任务所有后，清理前仍要检查未提交和未跟踪文件：

```bash
git -C <worktree-path> status --porcelain=v1 -uall
```

有成果时列出文件，让用户选择提交、移出、删除或保留。**不得自行使用 `--force`。**

## 4. 交付选择

只有没有已有决定时才展示一次简短菜单。

普通仓库或命名分支：

```text
实现已完成，验证结果见上。请选择交付方式：
1. 合入本地基线分支
2. 推送并创建 PR/MR
3. 保留当前分支和工作区
```

detached HEAD：

```text
当前是 detached HEAD。请选择：
1. 推送为新分支并创建 PR/MR
2. 保留当前状态
```

丢弃成果不放进常规菜单。只有用户明确要求丢弃时，才单独确认；确认前列出分支、提交和未提交文件，并要求用户明确回复 `discard`。

## 5. 执行交付

### 本地合并

1. 从计划、上游分支或用户说明确定基线；仍不明确时先问，不猜 `main`。
2. 检查基线是否有未处理的上游变更。未经授权不要自动 `pull`、rebase 或覆盖本地提交。
3. 切到基线并合并；冲突时停止，保留分支和工作区。
4. 在合并后的状态运行集成检查。失败时停止并保留证据。
5. 只有合并成功且归属明确时，才清理自有 worktree，再用 `git branch -d` 删除已合并分支。

### 推送并创建 PR/MR

1. 确认远程、分支名和用户授权；不要向错误远程推送。
2. 普通推送失败时调查原因，不自动 force-push。
3. 按仓库模板创建 PR/MR，报告 URL、基线分支和验证证据。
4. 保留 worktree，后续评审修改通常仍在该工作区进行。

detached HEAD 需要新分支时，明确记录新分支名，再按宿主流程推送。

### 保留

报告分支、HEAD、worktree 路径和尚未处理的风险。不要顺手清理“看起来过期”的内容。

### 丢弃

只在用户完成明确确认后执行。先保存或展示将丢失的提交和文件，再清理当前任务确实拥有的 worktree，最后按确认范围删除分支。外部工作区不代为删除。

## 6. 交付报告

用简短结果说明：

- 交付方式与实际发生的外部副作用
- 分支、基线、HEAD 或 PR/MR URL
- 验证命令和关键输出；哪些检查因状态未变而复用
- 尚未运行的检查、未解决风险和保留的工作区

## 快速参考

| 场景 | 合并 | 推送 | 默认保留 worktree | 删除分支 |
|---|---|---|---|---|
| 本地合并成功 | 是 | 否 | 否，仅限确认自有并可安全清理时 | `git branch -d` |
| 创建 PR/MR | 否 | 是 | 是 | 否 |
| 保留 | 否 | 否 | 是 | 否 |
| 明确丢弃 | 否 | 否 | 仅清理确认自有的 | 仅清理确认范围 |

## 常见自我辩解

| 借口 | 实际 |
|---|---|
| “测试之前跑过，再跑一遍最稳” | 同一状态的有效证据可复用；状态变了才补跑受影响检查。 |
| “用户说了完成，肯定想合并” | “完成”不等于选择交付方式；没有明确选择时询问一次。 |
| “目录在 .worktrees/ 下，所以是我们的” | 目录名不证明归属；用宿主记录或明确创建记录判断。 |
| “这是 submodule，也是 GIT_DIR 不同，按 worktree 清理” | submodule 不是 linked worktree，必须单独识别并保留。 |
| “PR 已创建，worktree 可以删了” | PR 反馈通常还要在原工作区修，保留到交付完成。 |
| “移除被拒绝，`--force` 只是收尾” | 拒绝说明有成果只存在这里；先展示并让用户决定。 |
| “推送被拒绝，force-push 更快” | 远程已变化，先调查；force-push 只在用户明确要求时使用。 |
| “基线大概是 main” | 合并错基线的代价高；从计划/上游确认，仍不明确就问。 |

<!-- provenance:start -->
> 创作归属：原创改进（基于上游）。来源、署名与许可见 [来源说明](../../ATTRIBUTION.md#finishing-a-development-branch)。
<!-- provenance:end -->
