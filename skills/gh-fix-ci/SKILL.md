---
name: gh-fix-ci
description: 用 gh 只读定位 GitHub Actions 失败：PR 检查、分支上的 push/定时运行或某个 run；拉失败步骤日志、给出失败摘要和根因判断，再按授权修复并复查。Use when a GitHub PR check or Actions run is red, "CI 挂了"、"修一下 CI"、"为什么 main 红了"、"看看这个 run 的日志"。外部 CI（Buildkite 等）只报链接；工作流安全审查转 code-review，删除/清理运行记录不属于本技能。
---

# 修复 GitHub Actions 失败

先拿到真实失败日志，再判断根因，最后才改代码。没有日志证据不要猜修。

## 1. 准备

- `gh auth status` 确认已登录且对目标仓库有读权限；未登录就停下请用户登录，不在本技能里代为登录。
- 确认目标：PR（编号/URL，或当前分支的 PR）、分支（如 `main` 的 push 运行）、或单个 run（ID/URL）。

## 2. 拉失败摘要（只读）

脚本只发 `gh` 读命令，不重跑、不取消、不删除任何运行：

```bash
python scripts/inspect_ci_failures.py --repo . --pr 123      # PR 检查（省略 --pr 用当前分支的 PR）
python scripts/inspect_ci_failures.py --repo . --branch main # 分支上每个工作流最近一次已完成的运行，只报仍是红的
python scripts/inspect_ci_failures.py --repo . --run 41420929310   # 或 run URL
```

加 `--json` 便于汇总；`--max-lines`/`--context` 控制片段长度。退出码：0 = 没有失败，1 = 有失败或出错。
脚本按 job 先取 `--log-failed`（只含失败步骤），取不到再退回完整日志或 job 日志接口；Windows 上按 UTF-8 解码。

脚本不可用时手动等价命令：

```bash
gh pr checks <pr> --json name,state,link,workflow
gh run list --branch main --limit 10 --json databaseId,workflowName,status,conclusion,headSha,createdAt
gh run view <run_id> --json jobs,url,headSha,event
gh run view <run_id> --job <job_id> --log-failed
```

`--branch` 只看每个工作流最新一次已完成运行：旧的红运行已被后续绿运行取代时不算当前失败。
运行仍在进行或日志未就绪时报 `log_pending`，按 `waiting-and-async` 的规则等待，不要猜时长 sleep。

## 3. 判断根因

逐个失败 job 写一行：检查名、run 链接、关键报错片段、初步归类。

| 类别 | 典型信号 | 处理 |
|---|---|---|
| 代码/测试回归 | 断言失败、编译/类型错误，本地能复现 | 本地先复现再修 |
| 依赖或工具链漂移 | `BackendUnavailable`、版本解析失败、上游镜像/Action 版本变动 | 固定或补齐依赖，说明为什么只在 CI 出现 |
| 平台差异 | 只在 Windows/macOS 挂：路径、换行、编码、可执行位 | 按平台修，必要时补对应平台测试 |
| 偶发/基础设施 | 网络超时、runner 被取消、同一提交重跑能过 | 有证据才判偶发，需要时请求重跑，不要把真实失败当偶发 |
| 外部 CI | detailsUrl 不是 GitHub Actions | 只报告链接，不进入外部系统 |

先在本地或隔离工作区复现（用项目自己的测试命令）；复现不了就如实说明，并写清依据的日志行。
同一提交上多个 job 同因失败只算一个根因；`cancelled` 多半是 fail-fast 连带，不单独修。

## 4. 修复与复查

- 改动遵循仓库约定和当前授权：可以直接改的仓库就改；需要评审的走分支/PR。不强推、不改历史。
- 修复后跑对应本地检查，再推送并用同一脚本或 `gh run watch <run_id> --exit-status` 等新运行结束，拿到绿色结果再报告完成。
- 汇报：失败检查与根因（附日志关键行）、改动、本地验证、新 run 链接与结论。
- 修工作流文件本身（`.github/workflows`、权限、secrets、触发器）时按 `code-review` 的 GitHub Actions 参考核对安全影响。
- 不在这里删除失败运行、取消别人的运行或改仓库设置；那属于仓库管理，需要另行授权。

<!-- provenance:start -->
> 创作归属：原创改进（基于上游）。来源、署名与许可见 [来源说明](../../ATTRIBUTION.md#gh-fix-ci)。
<!-- provenance:end -->
