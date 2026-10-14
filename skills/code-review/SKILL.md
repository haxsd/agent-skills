---
name: code-review
description: 审查代码改动或处理审查反馈；检查需求符合性、真实缺陷、回归风险和验证证据。
---

# 代码审查

两种模式：发起/执行审查，处理收到的审查反馈。在完成任务、较大功能或合并前安排审查。

默认只读：不切换当前 HEAD、不改用户文件、不执行目标项目的工作流或测试（`npm ci` 等安装会先运行第三方脚本）、不上传源码、不代发或回复 PR 评论，除非用户明确授权。专项参考按差异语义按需读取，小改动不强制加载。

## 发起或执行审查

1. 确定改动范围、需求和 base/head；审查未提交改动时明确使用工作区 diff。
2. 读改动与必要调用方，重点检查能复现的问题：逻辑、边界、兼容、状态、安全和错误处理。
3. 差异语义命中下表时才读对应参考；只需一项时不要全读：

| 改动包含 | 读取 |
|---|---|
| 认证/授权、加密、外部调用、值转移，或校验、权限检查被删改 | [references/differential-review.md](references/differential-review.md) |
| 凭据/秘密字段，或 `repr`/`str`/`asdict`/`model_dump`/`toJSON`、日志、遥测、缓存、接口响应、自定义 serializer 串接整对象 | [references/secret-serialization.md](references/secret-serialization.md) |
| `.github/workflows`、`action.yml`、触发器、checkout、`permissions`、secrets、artifact/cache | [references/github-actions.md](references/github-actions.md) |

4. 逐项给出严重程度与置信度（分开）、具体文件与行号、触发条件、影响和修复方向。置信度由证据决定；可达性、权限、受众或调用链不明时标"待确认"并写清缺什么，不因单一模式或事件名直接定 Critical。区分基线已有风险与本次新增，说明覆盖范围与预算。
5. 核对测试是否验证真实行为，区分已运行证据与静态推断；不为凑数提风格偏好。
6. 已确认根因要查其他位置的同族实例时转 variant-analysis；那不属于本次差异审查。
7. 需要独立审查时按当前宿主的代理能力派发，模板见 [references/code-reviewer.md](references/code-reviewer.md)；模板里的只读约束与"不派递归审查者"要求照做。

## 处理反馈

1. 先理解并核对反馈是否适用于当前代码、版本、需求和调用方；不因来源权威而直接照改。
2. 不清楚的项目提出关键问题，同时处理与其无依赖的明确项目。
3. 对错误建议提供可验证证据；对有效问题做最小修复，并运行对应验证。
4. 审查者建议"完善实现"时先 grep 调用方；没有真实使用的功能按 YAGNI 提议删除。
5. 按结果回应：已修复内容、核验依据、未处理项及原因；避免奉承、重复复述或无证据的成功声明。
6. 回复 GitHub 行内审查评论时用评论线程回复接口（`gh api repos/{owner}/{repo}/pulls/{pr}/comments/{id}/replies`），不新建顶层评论。

专项参考是审查方法，不是自动扫描或可达性证明；其许可按文件划分，见 [LICENSE.txt](LICENSE.txt)、[NOTICE.txt](NOTICE.txt) 与 [UPSTREAM.json](UPSTREAM.json)；既有模板不随本次改动重新许可。

<!-- provenance:start -->
> 创作归属：原创改进（基于上游）。来源、署名与许可见 [来源说明](../../ATTRIBUTION.md#code-review)。
<!-- provenance:end -->
