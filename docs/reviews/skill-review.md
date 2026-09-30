# 逐项价值与升级审查

审查日期：2026-09-30。基线提交：`d79b0c11b3dd1c89a3c39e596c8cb62ccc938f07`。

31 个启用和 5 个归档 SKILL.md 已逐一通读；关键脚本、参考和现有测试按风险抽查，未穷尽执行所有资源。
toolkit-map 仅评估外部接入，未把独立仓库当成本仓库已审完的内容。合并判断基于职责、输入输出和实质内容，不以同名或文字相似率定论。

**评分尺度**：高＝有非显然方法、可复用工具/数据或可验证操作约束；中＝有帮助但偏通用、依赖环境或流程偏重；低＝缺少独立产出、被现有入口覆盖或主要重复宿主规则。
**证据边界**：静态问题可由链接定位；运行结论仅覆盖 [整改路线里的实测记录](roadmap.md)。没有做真实用户任务的全量 A/B，价值评级属于专业判断。

## 01. requirement-understanding

需求与规划 · 启用 · 价值：中 · 规则需改造 · P1 · 合并候选

先读项目再识别需求缺口，与 brainstorming 统一成一个按复杂度分流的入口。

**真正的增益**：结合现有代码定位范围、避免向用户询问可自行查明的信息，有实际帮助；内容短，适合作为共用的需求澄清参考。

**体量**：入口 65 行 / 2,952 字节（LF）；整个目录 1 个文件 / 2,952 规范化字节；生产 scripts 文件 0，Python 测试文件 0。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- 引用 ask-questions-if-underspecified，但它只在 archive 中，默认安装不可发现。
- 中大型修改固定等待确认，与已有授权下持续执行的工作方式冲突。
- 在执行任何命令之前要求浏览项目和阅读代码，字面顺序自相矛盾。

**优化方案**

- 将澄清规则和验收标准并入统一需求入口；明确只有影响结果的必需信息缺失才等待。
- 保留简单任务直接执行、复杂任务提供可审阅方案的分流。

**关联/合并候选**：`brainstorming`、`ask-questions-if-underspecified`。此字段也包含只迁出重叠模块的关系，不代表整个技能都要合并。

**升级后的验收场景（尚未全量执行）**

- 明确的一行文案修改不追问，直接修改并验证。
- 含两个互斥需求的请求只问决定方向的问题，同时继续独立调查。

**来源定位**

- [skills/requirement-understanding/SKILL.md:16](../../skills/requirement-understanding/SKILL.md#L16)：`在写任何代码或执行任何命令之前`
- [skills/requirement-understanding/SKILL.md:35](../../skills/requirement-understanding/SKILL.md#L35)：`ask-questions-if-underspecified`

## 02. brainstorming

需求与规划 · 启用 · 价值：中 · 规则需改造 · P1 · 合并候选

保留方案比较和复杂度分流，移除所有任务都需重新审批的通用门禁。

**真正的增益**：spike / bounded / architectural 分流、方案权衡、架构规格自检和浏览器视觉辅助，适合复杂产品设计。

**体量**：入口 250 行 / 15,456 字节（LF）；整个目录 8 个文件 / 80,159 规范化字节；生产 scripts 文件 5，Python 测试文件 0。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- HARD-GATE 对每条路径和每个任务都要求批准，包括明确、可逆的小改动。
- 只允许升级流程复杂度，不能简化；规格、逐节设计、计划形成多重审批。
- 默认提交设计文档和固定调用 writing-plans，把探索任务扩展成开发流程。
- 视觉辅助服务器由 Bash 脚本启动，需要额外 Windows 适配。

**优化方案**

- 主入口只保留任务分流、关键问题和验收条件；架构与视觉辅助细节按需读取。
- 确认已有授权；方案比较只在存在真实取舍时进行，取消固定审批和自动提交。

**关联/合并候选**：`requirement-understanding`、`ask-questions-if-underspecified`。此字段也包含只迁出重叠模块的关系，不代表整个技能都要合并。

**升级后的验收场景（尚未全量执行）**

- 明确 bug 修复不经过产品设计审批。
- 新系统能输出架构取舍和可验证规格，用户指定直接执行时继续工作。

**来源定位**

- [skills/brainstorming/SKILL.md:14](../../skills/brainstorming/SKILL.md#L14)：`<HARD-GATE>`
- [skills/brainstorming/SKILL.md:52](../../skills/brainstorming/SKILL.md#L52)：`Nothing downgrades mid-task`

## 03. writing-plans

需求与规划 · 启用 · 价值：中 · 条件可用 · P1 · 升级

复杂任务的接口与验收规划值得保留，去掉预先写全实现代码的要求。

**真正的增益**：全局约束、任务输入输出接口、规格覆盖检查，能减少多任务执行中的签名和类型漂移。

**体量**：入口 171 行 / 7,053 字节（LF）；整个目录 2 个文件 / 8,766 规范化字节；生产 scripts 文件 0，Python 测试文件 0。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- 每个代码步骤必须提供完整实际代码，规划阶段容易重复实现并固化尚未验证的方案。
- 固定 2–5 分钟步骤、测试先行和逐步提交并不适用于所有任务。
- 最后再次要求选择执行方式，可能重复用户已有指令。

**优化方案**

- 计划写目标、文件范围、依赖、接口和验收，代码示例只覆盖难点。
- 按任务复杂度决定是否落盘；保留用户已选执行方式，避免重复确认。

**升级后的验收场景（尚未全量执行）**

- 多模块任务的计划能发现接口不一致。
- 小配置修改不生成完整实施计划或样板测试。

**来源定位**

- [skills/writing-plans/SKILL.md:133](../../skills/writing-plans/SKILL.md#L133)：`Every step must contain the actual content`
- [skills/writing-plans/SKILL.md:92](../../skills/writing-plans/SKILL.md#L92)：`**Interfaces:**`

## 04. executing-plans

实现与代理编排 · 启用 · 价值：中 · 规则需改造 · P1 · 合并候选

与 subagent-driven-development 合成同一执行入口，分别提供顺序和委派模式。

**真正的增益**：执行前检查计划、逐项验证、遇到真实阻塞重新评估，适合无子代理环境。

**体量**：入口 64 行 / 2,305 字节（LF）；整个目录 1 个文件 / 2,305 规范化字节；生产 scripts 文件 0，Python 测试文件 0。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- 描述说 separate session，正文又在可用时强制转到子代理开发，边界不稳定。
- 要求隔离工作区、固定 todo 和收尾技能，即使当前任务已准备就绪。
- 任何测试失败或指令不清就停止询问，缺少可自行修复的判断。

**优化方案**

- 统一 execute-plan 入口，按依赖和工具能力选择顺序执行或委派。
- 保留状态与证据，用明确的权限、缺失信息和失败停止条件替代泛化停工规则。

**关联/合并候选**：`subagent-driven-development`。此字段也包含只迁出重叠模块的关系，不代表整个技能都要合并。

**升级后的验收场景（尚未全量执行）**

- 子代理不可用时按相同验收标准顺序完成计划。
- 已在隔离工作区时不再次创建 worktree。

**来源定位**

- [skills/executing-plans/SKILL.md:14](../../skills/executing-plans/SKILL.md#L14)：`If subagents are available`
- [skills/executing-plans/SKILL.md:43](../../skills/executing-plans/SKILL.md#L43)：`Hit a blocker`

## 05. subagent-driven-development

实现与代理编排 · 启用 · 价值：高 · 条件可用 · P1 · 合并候选

保留任务契约、恢复账本和审查包，整合到统一计划执行技能。

**真正的增益**：按计划记录状态以防上下文压缩后重做任务；真实 BASE..HEAD 审查包避免多次提交被 HEAD~1 截断；修复复审范围和上限明确。

**体量**：入口 568 行 / 32,339 字节（LF）；整个目录 7 个文件 / 56,664 规范化字节；生产 scripts 文件 3，Python 测试文件 0。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- 568 行入口、复杂五轮修复机制、无条件逐任务审查，普通实现成本偏高。
- 要求一直重试到上限才能裁决明显错误的审查结论。
- 删除工作目录前只收集 Ruling，完整账本和报告未证明已进入 Git 历史，证据可能丢失。
- sdd-workspace 仅以计划 basename 标识，同名不同目录的计划会碰撞。
- 脚本为 Bash；模型和等待策略强依赖运行时。

**优化方案**

- 抽出 references：派发、审查、恢复、修复循环；主入口保持短。
- 任务量与风险决定审查频率，证据落盘保留后再清理临时产物。
- 工作目录标识包含计划规范路径的哈希；以当前工具 schema 为准。

**关联/合并候选**：`executing-plans`。此字段也包含只迁出重叠模块的关系，不代表整个技能都要合并。

**升级后的验收场景（尚未全量执行）**

- 中断后从首个未完成任务恢复，不重复已提交任务。
- 两份同名计划不会共享账本；多提交任务被完整审查。

**来源定位**

- [skills/subagent-driven-development/SKILL.md:373](../../skills/subagent-driven-development/SKILL.md#L373)：`Five rounds maximum per task`
- [skills/subagent-driven-development/scripts/sdd-workspace:31](../../skills/subagent-driven-development/scripts/sdd-workspace#L31)：`slug=$(basename`
- [skills/subagent-driven-development/SKILL.md:90](../../skills/subagent-driven-development/SKILL.md#L90)：`delete this plan's workspace`

## 06. parallel-agents

实现与代理编排 · 启用 · 价值：高 · 条件可用 · P1 · 升级

已成功整合两种并行情形，但必须把 Cursor 专用角色改成能力适配。

**真正的增益**：区分独立任务并行和同一问题多方案探索，强调文件归属、隔离、成功判据与整合证据。

**体量**：入口 139 行 / 5,740 字节（LF）；整个目录 1 个文件 / 5,740 规范化字节；生产 scripts 文件 0，Python 测试文件 0。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- generalPurpose 与 best-of-n-runner 是特定宿主角色，不能默认所有平台具备。
- 同一条消息才能并发的说法依赖运行时，并不是一般性规则。
- 多方案模式默认合并胜者并清理其余分支，缺少成果保留和授权边界。

**优化方案**

- 保留一个入口，把角色、并发数量、隔离实现放进平台适配层。
- 区分共享目录分工与真正隔离的方案试验；整合和清理遵守用户已授权范围。

**关联/合并候选**：`best-of-n-solving`、`dispatching-parallel-agents`。此字段也包含只迁出重叠模块的关系，不代表整个技能都要合并。

**升级后的验收场景（尚未全量执行）**

- 独立只读任务并行，重叠写任务先分配归属。
- 不支持专用 runner 的环境选择原生子代理和隔离目录，或退回顺序探索。

**来源定位**

- [skills/parallel-agents/SKILL.md:3](../../skills/parallel-agents/SKILL.md#L3)：`best-of-n-runner`
- [skills/parallel-agents/SKILL.md:15](../../skills/parallel-agents/SKILL.md#L15)：`所有派发必须写在同一条消息里`

## 07. deepseek-subagent-orchestration

实现与代理编排 · 启用 · 价值：中 · 局部实测可运行 · P2 · 保留

已升级并实测：GPT 主代理保持当前模型，DeepSeek 默认承接独立工作块，可在复制目录读写授权文件并执行命名检查。

**真正的增益**：标准库外部 API 工具循环避开宿主模型白名单；独立文件副本、精确写权限、固定检查 argv、DPAPI 凭据保护与真实操作日志构成可验收的执行助手。

**体量**：入口 88 行 / 5,386 字节（LF）；整个目录 5 个文件 / 56,867 规范化字节；生产 scripts 文件 2，Python 测试文件 0。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- 命名检查进程不是 OS 沙箱，只适合已授权的可信项目命令；文件工具边界不能限制检查代码的所有宿主访问。
- 多轮长上下文可能触及预算，需要任务级配置；连通和局部执行实测不证明整项任务节省 GPT 额度或加速。

**优化方案**

- 用真实工作块比较派发、验收与直接执行的总成本及耗时。
- 滚动别名升级时复核返回型号；复杂任务显式调整预算与 thinking。

**升级后的验收场景（尚未全量执行）**

- 独立实现助手实际读文件、修改实现、添加测试、执行命名检查，主工作区不被文件工具修改。
- 越界写入、未知检查、密钥上下文被拒绝；截断或预算耗尽不接受为完整结果。

**来源定位**

- [skills/deepseek-subagent-orchestration/SKILL.md:8](../../skills/deepseek-subagent-orchestration/SKILL.md#L8)：`Keep the current conversation's GPT model, provider, and reasoning settings.`
- [skills/deepseek-subagent-orchestration/scripts/deepseek_worker.py:279](../../skills/deepseek-subagent-orchestration/scripts/deepseek_worker.py#L279)：`Batch stopped after authentication failure`
- [skills/deepseek-subagent-orchestration/scripts/deepseek_worker.py:216](../../skills/deepseek-subagent-orchestration/scripts/deepseek_worker.py#L216)：`Possible credential in job context`
- [docs/validation/deepseek-validation.json:14](../../docs/validation/deepseek-validation.json#L14)：`total_tokens`
- [skills/deepseek-subagent-orchestration/scripts/agent_runtime.py:390](../../skills/deepseek-subagent-orchestration/scripts/agent_runtime.py#L390)：`A check modified a path outside the owned files; do not integrate`

## 08. env-doctor

质量、调试与审查 · 启用 · 价值：高 · 条件可用 · P2 · 保留

保留为启动与运行环境诊断，和代码根因调试互补。

**真正的增益**：Windows/POSIX 端口检查、进程归属、只检查 .env 键名、对应对抗性场景，是具体且有用的运行约束。

**体量**：入口 99 行 / 6,031 字节（LF）；整个目录 3 个文件 / 15,975 规范化字节；生产 scripts 文件 0，Python 测试文件 0。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- 没有 node_modules 或 .venv 就判定异常，未覆盖 PnP、容器和全局/管理器环境。
- 固定常见端口可能漏掉项目实际配置；要求 Node 缺依赖时统一 npm install，未按锁文件选管理器。
- 安全场景是文档 fixtures，未形成可执行行为评估。

**优化方案**

- 从项目配置和锁文件推导端口、运行环境及包管理器。
- 将键名检查和端口归属提取为只读脚本，保留未知归属不停止进程的约束。

**升级后的验收场景（尚未全量执行）**

- 端口被无关视频会议进程占用时只报告，不终止。
- .env 含 canary 密钥时输出只包含键名与空/有值状态。
- PnP 项目不会因没有 node_modules 被误诊。

**来源定位**

- [skills/env-doctor/SKILL.md:50](../../skills/env-doctor/SKILL.md#L50)：`Parse only key names`
- [skills/env-doctor/references/safety-fixtures.md:5](../../skills/env-doctor/references/safety-fixtures.md#L5)：`Unrelated Process Owns Port`

## 09. systematic-debugging

质量、调试与审查 · 启用 · 价值：高 · 条件可用 · P1 · 升级

根因追踪和基于条件的等待有价值，需要缩短入口并修诊断输出示例。

**真正的增益**：复现、边界定位、单一假设、最小验证；附带 root-cause-tracing、condition-based-waiting 和 polluter 排查工具。

**体量**：入口 283 行 / 9,465 字节（LF）；整个目录 11 个文件 / 40,772 规范化字节；生产 scripts 文件 0，Python 测试文件 0。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- 示例 env | grep IDENTITY 会输出变量值，与 env-doctor 的键名原则不一致。
- 每种故障都走四阶段、读完整参考、三次失败必讨论架构，边界过硬。
- 95% 无根因案例的断言未附测量证据；多段反合理化表重复。

**优化方案**

- 诊断日志仅输出脱敏后的存在性、长度或状态。
- 入口保留证据→假设→最小实验→修复；复杂并发、跨系统和测试污染按需读参考。
- 重复失败时按证据重估假设，不固定归因于架构。

**升级后的验收场景（尚未全量执行）**

- 多服务故障定位到丢失配置的边界，不输出配置值。
- 时序故障用状态/事件等待复现，不仅增加 sleep。

**来源定位**

- [skills/systematic-debugging/SKILL.md:95](../../skills/systematic-debugging/SKILL.md#L95)：`env | grep IDENTITY`
- [skills/systematic-debugging/SKILL.md:275](../../skills/systematic-debugging/SKILL.md#L275)：`95%`

## 10. test-driven-development

质量、调试与审查 · 启用 · 价值：中 · 规则需改造 · P1 · 升级

保留能证明回归的测试设计，取消无条件删除已有实现的规定。

**真正的增益**：先定义可观察行为、确认测试能抓住错误、避免只验证 mock；writing-good-tests 参考值得保留。

**体量**：入口 320 行 / 9,015 字节（LF）；整个目录 2 个文件 / 17,283 规范化字节；生产 scripts 文件 0，Python 测试文件 0。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- 未先写失败测试就 Delete code，并对文档/配置等小改动要求额外豁免批准。
- 每个新函数必须测试和全套输出零警告，并不等同于行为覆盖。
- 大段重复禁令把测试方法变成适用于所有任务的纪律入口。

**优化方案**

- 新业务行为和 bug 回归优先测试先行，已有代码用最小回归测试验证。
- 按风险选择单元、集成或人工验证，不删除用户或其他任务的实现。

**升级后的验收场景（尚未全量执行）**

- 给已有 bug 加能复现的测试并修复，不删除无关实现。
- 改注释/文案时不生成镜像实现的测试。

**来源定位**

- [skills/test-driven-development/SKILL.md:37](../../skills/test-driven-development/SKILL.md#L37)：`Write code before the test? Delete it.`
- [skills/test-driven-development/SKILL.md:287](../../skills/test-driven-development/SKILL.md#L287)：`Every new function/method has a test`

## 11. verification-before-completion

质量、调试与审查 · 启用 · 价值：中 · 规则需改造 · P1 · 合并候选

证据先于完成声明值得保留，精简后放到质量公共参考。

**真正的增益**：区分测试、lint、构建、需求覆盖和委派声明的证据，不把一种通过外推为全部通过。

**体量**：入口 120 行 / 3,646 字节（LF）；整个目录 1 个文件 / 3,646 规范化字节；生产 scripts 文件 0，Python 测试文件 0。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- 要求在同一条消息中重新运行验证，可能重复同一代码状态的已有效证据。
- ANY positive statement、进入下一任务和派发代理都强制全量检查，造成重复验证。
- 没有脚本或领域资料，主要重复宿主已有完成声明规则。

**优化方案**

- 记录代码状态/提交、验证命令和结果；相关代码变更后才使证据失效。
- 作为共享 verification 参考由执行和收尾入口引用，不独立广泛触发。

**关联/合并候选**：`finishing-a-development-branch`。此字段也包含只迁出重叠模块的关系，不代表整个技能都要合并。

**升级后的验收场景（尚未全量执行）**

- 已对当前代码通过测试时准确引用证据，之后的代码修改要求重验相关行为。
- lint 通过时不声称构建和业务验收已通过。

**来源定位**

- [skills/verification-before-completion/SKILL.md:20](../../skills/verification-before-completion/SKILL.md#L20)：`in this message`
- [skills/verification-before-completion/SKILL.md:114](../../skills/verification-before-completion/SKILL.md#L114)：`Delegating to agents`

## 12. requesting-code-review

质量、调试与审查 · 启用 · 价值：中 · 条件可用 · P1 · 合并候选

与 receiving-code-review 统一为 code-review 的审查和反馈两种模式。

**真正的增益**：code-reviewer 模板包含只读审查、需求比对、缺陷严重度与禁止评审者递归派发，值得复用。

**体量**：入口 95 行 / 2,956 字节（LF）；整个目录 2 个文件 / 8,625 规范化字节；生产 scripts 文件 0，Python 测试文件 0。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- 默认 HEAD~1 会截断多提交任务；只看提交区间会遗漏未提交修改。
- 普通任务也强制子代理审查，与无代理环境和小任务成本不匹配。
- 固定 general-purpose 角色是宿主约定。

**优化方案**

- 记录任务起始 BASE，并声明是否包含 staged/unstaged/untracked 工作成果。
- 大任务用独立审查，小任务按风险自查；工具不可用时有明确降级。

**关联/合并候选**：`receiving-code-review`。此字段也包含只迁出重叠模块的关系，不代表整个技能都要合并。

**升级后的验收场景（尚未全量执行）**

- 一个任务包含三次提交和未提交修复时，审查包覆盖所有成果。
- 只读审查不改变原 checkout 的 HEAD 或文件。

**来源定位**

- [skills/requesting-code-review/SKILL.md:28](../../skills/requesting-code-review/SKILL.md#L28)：`BASE_SHA=$(git rev-parse HEAD~1)`
- [skills/requesting-code-review/code-reviewer.md:33](../../skills/requesting-code-review/code-reviewer.md#L33)：`Read-Only Review`

## 13. receiving-code-review

质量、调试与审查 · 启用 · 价值：中 · 规则需改造 · P1 · 合并候选

保留建议核验与有证据的异议，合并到 code-review 的反馈模式。

**真正的增益**：检查建议是否适用于当前平台和架构、区分有效修复与无用功能、回复具体审查线程。

**体量**：入口 205 行 / 6,203 字节（LF）；整个目录 1 个文件 / 6,203 规范化字节；生产 scripts 文件 0，Python 测试文件 0。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- 任意一项不清楚就停止所有修复，即使其他项完全独立。
- 禁止任何感谢表达属于沟通风格约束，对技术判断没有额外价值。
- 把先前某位用户的偏好写成所有人的规则。

**优化方案**

- 不明项独立澄清，已明确且无依赖的项继续处理。
- 报告建议、证据、决定和验证；删去普遍化的语气禁令。

**关联/合并候选**：`requesting-code-review`。此字段也包含只迁出重叠模块的关系，不代表整个技能都要合并。

**升级后的验收场景（尚未全量执行）**

- 外部审查者建议删除兼容代码时先验证支持目标。
- 五条意见里一条待确认，其余独立修改可完成。

**来源定位**

- [skills/receiving-code-review/SKILL.md:44](../../skills/receiving-code-review/SKILL.md#L44)：`STOP - do not implement anything yet`
- [skills/receiving-code-review/SKILL.md:143](../../skills/receiving-code-review/SKILL.md#L143)：`ANY gratitude expression`

## 14. using-git-worktrees

Git 隔离与交付 · 启用 · 价值：高 · 条件可用 · P1 · 保留

保留 Git 隔离专门知识，改成按已有环境和实际需求决定创建。

**真正的增益**：先检测既有 worktree、排除 submodule、优先宿主管理、校验目录被忽略，属于不明显且易踩坑的操作知识。

**体量**：入口 167 行 / 6,813 字节（LF）；整个目录 1 个文件 / 6,813 规范化字节；生产 scripts 文件 0，Python 测试文件 0。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- 正常 checkout 默认先询问是否创建，会给普通任务增加门禁。
- 自动 npm install、cargo build、poetry install 未依据锁文件和项目实际工具。
- 手工 fallback 默认提交 .gitignore；基线失败一律停工。

**优化方案**

- 已有隔离直接复用；只有任务确需隔离才创建，沿用已有偏好和授权。
- 优先项目声明的初始化命令；既有基线失败记录后判断与当前任务的关系。

**升级后的验收场景（尚未全量执行）**

- Git submodule 不被误判为 linked worktree。
- 宿主管理的 detached worktree 不再创建第二份。

**来源定位**

- [skills/using-git-worktrees/SKILL.md:26](../../skills/using-git-worktrees/SKILL.md#L26)：`Submodule guard`
- [skills/using-git-worktrees/SKILL.md:108](../../skills/using-git-worktrees/SKILL.md#L108)：`npm install`

## 15. finishing-a-development-branch

Git 隔离与交付 · 启用 · 价值：高 · 条件可用 · P1 · 升级

保留交付与成果保护，整合精简后的验证规则。

**真正的增益**：区分命名分支、detached HEAD 和外部管理 worktree；PR 后保留工作区；拒绝强制删除未提交成果。

**体量**：入口 225 行 / 7,781 字节（LF）；整个目录 1 个文件 / 7,781 规范化字节；生产 scripts 文件 0，Python 测试文件 0。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- 无条件重新运行全量测试并再次展示固定菜单，忽略已选交付方式。
- 以路径位于 .worktrees/worktrees 推断归属，目录名不能证明由谁创建。
- 没有 using-git-worktrees 中的 submodule 保护，GIT_DIR/GIT_COMMON 判断可能误分。

**优化方案**

- 沿用已授权的 PR/交付选择；只补缺少或已失效的验证。
- 使用宿主 attachment 或明确创建记录判断 worktree 归属；加入 submodule 判别。
- 破坏性操作保留成果检查和真实授权，提交描述围绕最终改动。

**关联/合并候选**：`verification-before-completion`。此字段也包含只迁出重叠模块的关系，不代表整个技能都要合并。

**升级后的验收场景（尚未全量执行）**

- 已有创建 PR 指令时直接准备交付，无重复菜单。
- 有未提交文件的工作区在清理失败后完整保留。

**来源定位**

- [skills/finishing-a-development-branch/SKILL.md:169](../../skills/finishing-a-development-branch/SKILL.md#L169)：`Superpowers`
- [skills/finishing-a-development-branch/SKILL.md:78](../../skills/finishing-a-development-branch/SKILL.md#L78)：`Present the menu exactly`

## 16. ui-ux-pro-max

品牌、设计与 UI · 启用 · 价值：高 · 收录/引用不完整 · P0 · 升级

本仓库最值得投入的资产之一：保留本地检索数据，补齐维护链和失效引用。

**真正的增益**：标准库 BM25、产品/配色/字体/图标/UX/22 技术栈数据、检索契约、MASTER/page overrides、相关性和数据回归场景。

**体量**：入口 425 行 / 28,066 字节（LF）；整个目录 68 个文件 / 3,539,346 规范化字节；生产 scripts 文件 5，Python 测试文件 10。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- 正文引用 Quick Reference §1–§9，但当前 SKILL.md 没有该章节。
- catalog refresh 与 relevance evaluator 测试依赖未收录的 refresh-google-fonts.py、refresh-icon-catalog.py、evaluate-relevance.py。
- baseline Windows 检出将数据改为 CRLF，4 个字节哈希校验失败；本轮通过 LF 属性修复。
- 入口长且广，移动端与 web/desktop 规则仍需进一步分流。

**优化方案**

- 补回真实上游维护脚本或明确划分运行包和维护包；不要删除失败测试来制造通过。
- 恢复短 checklist 或改成实际存在的章节链接。
- 将固定栈和格式细节拆成按需参考；数据更新保留来源、真实验证日期和相关性门槛。

**升级后的验收场景（尚未全量执行）**

- Windows fresh clone 的 validate_data 校验通过。
- 完整测试可收集；字体与图标离线 refresh 以及相关性门槛可复现。
- 中文单一意图查询返回相关结果；普通 UI 修复不重建设计系统。

**来源定位**

- [skills/ui-ux-pro-max/SKILL.md:292](../../skills/ui-ux-pro-max/SKILL.md#L292)：`Quick Reference §6`
- [skills/ui-ux-pro-max/scripts/tests/test_catalog_refresh.py:16](../../skills/ui-ux-pro-max/scripts/tests/test_catalog_refresh.py#L16)：`refresh-google-fonts.py`
- [skills/ui-ux-pro-max/scripts/tests/test_relevance_evaluator.py:10](../../skills/ui-ux-pro-max/scripts/tests/test_relevance_evaluator.py#L10)：`scripts/evaluate-relevance.py`

## 17. brand

品牌、设计与 UI · 启用 · 价值：高 · 条件可用 · P2 · 保留

保留品牌语气、视觉规范和品牌到 token 的同步职责。

**真正的增益**：品牌指南模板、语气与 messaging 参考、4 个 Node 工具、模板同步回归测试，超出通用设计建议。

**体量**：入口 97 行 / 2,939 字节（LF）；整个目录 18 个文件 / 88,892 规范化字节；生产 scripts 文件 4，Python 测试文件 1。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- 同步工具默认写项目 docs/assets，需先确认用户项目结构，避免强制采用固定目录。
- Markdown 表格解析依赖模板结构，对多样真实品牌指南还需覆盖。
- 项目根目录执行 scripts/... 可能指向不存在的路径，应明确 skill-root 与 project-root。

**优化方案**

- 支持显式指南、输入输出路径，并在同步前展示差异。
- 保留模板 happy path，增加已有用户品牌不被覆盖的场景。

**升级后的验收场景（尚未全量执行）**

- 官方 starter 模板能生成预期品牌原色和 CSS。
- 已有项目自定义 token 时只更新授权品牌字段。

**来源定位**

- [skills/brand/SKILL.md:47](../../skills/brand/SKILL.md#L47)：`sync-brand-to-tokens.cjs`
- [skills/brand/scripts/tests/test_sync_brand_to_tokens.py:27](../../skills/brand/scripts/tests/test_sync_brand_to_tokens.py#L27)：`test_sync_parses_bundled_starter_template`

## 18. design-system

品牌、设计与 UI · 启用 · 价值：高 · 条件可用 · P1 · 升级

保留 token 与组件规范；把幻灯片制作迁到 design 的单一模块。

**真正的增益**：primitive→semantic→component 模型、token 生成/校验脚本、starter、组件状态参考，以及 slide 结构化策略数据。

**体量**：入口 244 行 / 6,875 字节（LF）；整个目录 27 个文件 / 179,018 规范化字节；生产 scripts 文件 9，Python 测试文件 1。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- token 职责与 slide 制作混在入口，和 design 的 slides 模块重叠。
- 所有 slides 必须居中、说服转化和 Chart.js，把营销例子变成通用约束。
- 引用 assets/css/slide-animations.css、示例 pitch HTML 是项目产物，本仓库不提供，未明确作为可选示例。
- token 示例禁止原始 hex，而 Chart.js 示例直接硬编码配色，契约不一致。

**优化方案**

- token 入口只处理生成、映射和一致性；slide 数据与脚本收敛到单一实现，先检查引用再移动。
- 对图表库、对齐和目标保留项目选择；补 token 引用循环、缺失 alias 和零值测试。

**关联/合并候选**：`design`、`slides`。此字段也包含只迁出重叠模块的关系，不代表整个技能都要合并。

**升级后的验收场景（尚未全量执行）**

- starter JSON 生成 CSS，校验可发现与 var() 同行的硬编码。
- 缺失 token 或循环引用产生可定位错误，不无限递归。

**来源定位**

- [skills/design-system/SKILL.md:184](../../skills/design-system/SKILL.md#L184)：`Center align content`
- [skills/design-system/scripts/generate-tokens.cjs:64](../../skills/design-system/scripts/generate-tokens.cjs#L64)：`return resolveReference(result.$value, tokens)`

## 19. ui-styling

品牌、设计与 UI · 启用 · 价值：中 · 条件可用 · P1 · 升级

缩窄为 shadcn/Tailwind 实现，移除海报和艺术创作职责。

**真正的增益**：可访问组件组合、Tailwind 响应式与主题参考、组件添加和配置生成脚本。

**体量**：入口 324 行 / 10,045 字节（LF）；整个目录 16 个文件 / 170,925 规范化字节；生产 scripts 文件 3，Python 测试文件 2。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- poster/canvas 触发与 canvas-design 重叠，一般 UI 知识与 ui-ux-pro-max 重叠。
- 入口介绍 CSS-first @theme/Vite 方案，配置生成器仍输出 darkMode/content/theme JS 配置，需要按项目版本分流。
- 多个代码示例和工具路径假设 React/特定包管理器，应按实际项目调整。

**优化方案**

- 描述只覆盖 shadcn/Tailwind 具体实现；设计决策按需用 ui-ux-pro-max。
- 检测 Tailwind 主版本和现有组件，分别生成合适配置；艺术参考收敛到 canvas-design。

**关联/合并候选**：`canvas-design`。此字段也包含只迁出重叠模块的关系，不代表整个技能都要合并。

**升级后的验收场景（尚未全量执行）**

- 现有 shadcn 项目只添加所需组件，保留主题和 aliases。
- 不同 Tailwind 配置模式的生成结果能被对应项目实际编译。

**来源定位**

- [skills/ui-styling/SKILL.md:29](../../skills/ui-styling/SKILL.md#L29)：`Generating visual designs, posters`
- [skills/ui-styling/scripts/tailwind_config_gen.py:52](../../skills/ui-styling/scripts/tailwind_config_gen.py#L52)：`"darkMode": ["class"]`

## 20. design

品牌、设计与 UI · 启用 · 价值：高 · 收录/引用不完整 · P0 · 升级

收敛为 logo、CIP、icon、banner、HTML slides 的视觉资产入口。

**真正的增益**：Logo/CIP 的 BM25 数据、Gemini 生成器、CIP HTML 输出、SVG 图标和营销资产参考；存在可复用工具资产。

**体量**：入口 313 行 / 12,322 字节（LF）；整个目录 35 个文件 / 241,945 规范化字节；生产 scripts 文件 8，Python 测试文件 0。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- brand/tokens/UI/海报同时抢占另外五个设计技能的触发。
- banner/social 依赖 frontend-design、ai-artist、ai-multimodal、chrome-devtools、assets-organizing 等，本仓库未提供完整链。
- ~/.claude 固定路径、AskUserQuestion 和 /ckm 命令依赖特定宿主。
- Logo 永远白底、随机挑选设计技能和固定数量创意，可能违背用户需求。
- Gemini model IDs 与广告平台规则需在实际执行时核实，不能把仓库快照当实时可用性证明。

**优化方案**

- 缩短为视觉资产路由，brand/tokens/UI 直接转向各自技能，slides 只保留一套来源。
- 图像与截图改成当前宿主能力适配；缺少工具先说明能力边界，避免固定技能名硬依赖。
- 模型可配置；尊重透明背景、已有品牌和用户指定数量。

**关联/合并候选**：`banner-design`、`slides`。此字段也包含只迁出重叠模块的关系，不代表整个技能都要合并。

**升级后的验收场景（尚未全量执行）**

- 离线 Logo/CIP search 能输出相关 brief。
- 透明 logo 请求保持透明；无 Gemini key 时不声称图像已生成。
- HTML slides 只有一个创建流程并通过实际视觉检查。

**来源定位**

- [skills/design/SKILL.md:60](../../skills/design/SKILL.md#L60)：`ALWAYS** generate output logo images with white background`
- [skills/design/SKILL.md:228](../../skills/design/SKILL.md#L228)：`randomly invoke`

## 21. canvas-design

品牌、设计与 UI · 启用 · 价值：中 · 条件可用 · P2 · 升级

保留静态艺术构图和字体资产，取消虚构用户意见与固定审美限制。

**真正的增益**：视觉层次、间距、概念到构图的转化、二次精修流程及带字体许可文本的本地字体库。

**体量**：入口 130 行 / 11,939 字节（LF）；整个目录 83 个文件 / 5,554,003 规范化字节；生产 scripts 文件 0，Python 测试文件 0。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- 声称用户 ALREADY said 某段审美评价，实际是模板虚构的用户指令。
- 把原始输入降格为 subtle foundation、强制抽象和少文本，可能丢失海报必需信息。
- 固定输出 md/pdf/png、4–6 段宣言与 museum quality 重复强调，增加成本但缺少验收指标。
- 字体库有多项许可文本，但是否满足当前中文项目字形覆盖未验证。

**优化方案**

- 先锁定文字、尺寸、格式和品牌要求；风格由任务决定。
- 哲学说明改成可选的短设计 brief；视觉复核用边界、对比、字形和必需信息完整性。
- 维护字体用途与许可索引，保留原许可文件。

**关联/合并候选**：`ui-styling`。此字段也包含只迁出重叠模块的关系，不代表整个技能都要合并。

**升级后的验收场景（尚未全量执行）**

- 活动海报完整保留日期地点和主办方，不因 minimal text 丢信息。
- 中文海报没有缺字，输出尺寸正确，无文字越界。

**来源定位**

- [skills/canvas-design/SKILL.md:122](../../skills/canvas-design/SKILL.md#L122)：`The user ALREADY said`
- [skills/canvas-design/SKILL.md:23](../../skills/canvas-design/SKILL.md#L23)：`it should not constrain creative freedom`

## 22. graphify

知识图谱与安全研究 · 启用 · 价值：高 · 依赖外部环境 · P0 · 升级

知识图谱是独特能力，缩窄触发并改为可复现的外部工具适配。

**真正的增益**：AST/语义分离、EXTRACTED/INFERRED/AMBIGUOUS 证据类型、缓存 prompt 归属、增量图完整性与词汇扩展，适合多文件知识导航。

**体量**：入口 711 行 / 41,342 字节（LF）；整个目录 10 个文件 / 82,125 规范化字节；生产 scripts 文件 0，Python 测试文件 0。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- 任意代码库问题都优先 graphify，普通查找也可能启动重型构图。
- 依赖 graphifyy 外部包但未锁定版本；.graphify_version 是技能快照，不是已安装包证明。
- Bash 流程不适配原生 PowerShell；安装含 --break-system-packages。
- Codex 段写 spawn_agent(agent_type=...)、wait_agent(handle)、close_agent，和当前可用工具 schema 不一致。
- 已有图查询未先检查源文件是否已变化；部分失败 chunk 可继续产出，报告须标明覆盖缺口。

**优化方案**

- 仅在用户要求知识图谱或现有有效图能显著帮助跨文件问题时使用；小查找用原生搜索。
- 外部包使用项目环境和明确版本，重型流程做成可测试脚本；平台适配不写死生命周期。
- 查询之前检查 freshness，保留未完整抽取的源文件清单和未知 token 使用量。

**升级后的验收场景（尚未全量执行）**

- 一个符号定位不构建知识图谱。
- 代码变化后图被标记过期；失效工具调用能降级。
- 抽取失败不会静默把不完整报告标成完成。

**来源定位**

- [skills/graphify/SKILL.md:3](../../skills/graphify/SKILL.md#L3)：`Use for any question`
- [skills/graphify/SKILL.md:94](../../skills/graphify/SKILL.md#L94)：`--break-system-packages`
- [skills/graphify/SKILL.md:268](../../skills/graphify/SKILL.md#L268)：`close_agent(handle)`

## 23. reverse-skill

知识图谱与安全研究 · 启用 · 价值：中 · 依赖外部环境 · P0 · 升级

保留安全研究路由入口，实际价值取决于独立技能包与工具链。

**真正的增益**：按任务路由到专项方法、案例证据链、授权 scope 和交付自检；无需把大型技能包复制进本仓库。

**体量**：入口 82 行 / 5,161 字节（LF）；整个目录 1 个文件 / 5,161 规范化字节；生产 scripts 文件 0，Python 测试文件 0。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- 固定 C:\Users\Administrator\tools\reverse-skill，在当前账户无法直接使用。
- 49 模块/89 入口与工具具备清单是历史快照，不能代表现状。
- 依赖的 RULES、路由、建案、bootstrap 和复核均不在本仓库，需外部版本记录。

**优化方案**

- 通过 REVERSE_SKILL_ROOT 或当前用户位置解析依赖，预检规则/路由脚本后再执行。
- 记录上游仓库、期望版本和本地验证状态；工具状态用 toolkit-map 动态查询。

**升级后的验收场景（尚未全量执行）**

- 外部目录缺失时指出具体依赖，不猜工具可用。
- 离线样本按本地 scope 建案，未授权外部目标不启动网络动作。

**来源定位**

- [skills/reverse-skill/SKILL.md:15](../../skills/reverse-skill/SKILL.md#L15)：`C:\Users\Administrator\tools\reverse-skill`
- [skills/reverse-skill/SKILL.md:57](../../skills/reverse-skill/SKILL.md#L57)：`本机工具链现状`

## 24. writing-skills

技能维护与运行效率 · 启用 · 价值：中 · 规则需改造 · P1 · 升级

保留现实场景对照评估，缩短为技能质量指南，避免每次小改都昂贵多代理测试。

**真正的增益**：有/无技能对照、真实压力场景、模板输出与行为遗漏的区别、微测试方法，能帮助证明技能是否改善结果。

**体量**：入口 679 行 / 26,360 字节（LF）；整个目录 7 个文件 / 107,377 规范化字节；生产 scripts 文件 0，Python 测试文件 0。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- 679 行入口，并要求任意编辑都先出现失败、5+ 次重复，未按改动风险调整成本。
- description 必须只写 when、frontmatter 总共 1024 字等规定与当前开放规范不一致。
- 要求反复封堵 rationalization，容易制造越来越多绝对化指令。
- 文档默认提交和 push 是额外交付动作，不应由技能自行扩大授权。

**优化方案**

- 用当前开放格式规范和平台可用字段；把完整评估方法移到 references。
- 重大行为改变用 A/B 场景；引用、路径、格式修复做静态校验。
- 同时测成功率、误触发、等待次数、token/时延和维护成本，避免只测服从。

**升级后的验收场景（尚未全量执行）**

- 技能能提升新任务的正确率，而非仅复述禁止条款。
- 一处引用修复通过静态检查即可，不触发批量付费评估。

**来源定位**

- [skills/writing-skills/SKILL.md:97](../../skills/writing-skills/SKILL.md#L97)：`Max 1024 characters total`
- [skills/writing-skills/SKILL.md:581](../../skills/writing-skills/SKILL.md#L581)：`5+ reps per variant`

## 25. using-superpowers

技能维护与运行效率 · 启用 · 价值：低 · 规则需改造 · P1 · 建议归档

建议退出默认激活集；保留有用的平台说明为维护参考。

**真正的增益**：跨宿主技能发现与平台适配参考有历史价值；主入口没有独立任务产出。

**体量**：入口 63 行 / 3,108 字节（LF）；整个目录 6 个文件 / 17,169 规范化字节；生产 scripts 文件 0，Python 测试文件 0。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- starting any conversation 和 1% chance 强制加载技能，扩大误触发与上下文开销。
- 要求任何回复前调用 skill，与宿主已经提供的技能发现机制重复。
- 平台参考包含与当前 schema 相反的 full-history model override 说明及固定配置建议。

**优化方案**

- 移到 archive 前检查所有 REQUIRED 引用；把平台说明改成工具能力探测参考。
- 自动技能选择依靠精准 description，移除普遍强制调用与额外配置修改要求。

**关联/合并候选**：`writing-skills`。此字段也包含只迁出重叠模块的关系，不代表整个技能都要合并。

**升级后的验收场景（尚未全量执行）**

- 普通知识问答不加载开发流程链。
- 维护参考以实际工具 schema 为准，不运行不存在的参数。

**来源定位**

- [skills/using-superpowers/SKILL.md:11](../../skills/using-superpowers/SKILL.md#L11)：`1% chance`
- [skills/using-superpowers/references/codex-tools.md:21](../../skills/using-superpowers/references/codex-tools.md#L21)：`Full-history forks accept`

## 26. token-efficient-workflow

技能维护与运行效率 · 启用 · 价值：中 · 依赖外部环境 · P0 · 升级

通用省上下文规则更适合作为运行规则，平台入口修好路径和 UI 元数据。

**真正的增益**：共享准则单一来源、窄搜索与日志摘要、只更新持续项目变化，适合长期约定。

**体量**：入口 43 行 / 2,211 字节（LF）；整个目录 2 个文件 / 2,435 规范化字节；生产 scripts 文件 0，Python 测试文件 0。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- 唯一权威文件固定在 Administrator/tools/shared，当前安装器却按当前 USERPROFILE 联接。
- codex-helpers 四个脚本未收录；上下文固定模板不适用于任意项目。
- agents/openai.yaml 将 UI 字段放在顶层，缺少 interface 包装；本轮修复。
- 广泛触发几乎所有任务；shared 的一次整改后冻结规则会阻止未来合理维护。

**优化方案**

- 从技能根或显式配置定位共享文件，辅助脚本不存在时退回原生搜索。
- 共用内容作为宿主规则，skill 仅提供项目大型日志/上下文整理的特殊流程。
- 不把 CSV 等文件类型永久视为噪声；以当前任务范围决定读取。

**升级后的验收场景（尚未全量执行）**

- 换用户名后能找到共享文件，未安装 helpers 时仍可工作。
- 深入审查任务能够按需完整读取资料，不被短输出规则削弱。

**来源定位**

- [skills/token-efficient-workflow/SKILL.md:9](../../skills/token-efficient-workflow/SKILL.md#L9)：`C:\Users\Administrator\tools\shared`
- [skills/token-efficient-workflow/SKILL.md:24](../../skills/token-efficient-workflow/SKILL.md#L24)：`codex-helpers`

## 27. suggesting-cursor-rules

技能维护与运行效率 · 启用 · 价值：低 · 规则需改造 · P2 · 升级

重复偏好沉淀有用，但名称、文案与写入平台不一致。

**真正的增益**：重复纠正两次以上才提议规则、先查既有规则、一个关注点一条，避免把一次反馈永久化。

**体量**：入口 83 行 / 2,176 字节（LF）；整个目录 1 个文件 / 2,176 规范化字节；生产 scripts 文件 0，Python 测试文件 0。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- 名字和输出 .cursor/rules 属于 Cursor，标题和 description 却写 Codex。
- 默认通用安装到多个平台，实际只有一种规则文件落点。
- 用户表达偏好时可能已有直接写规则授权，应避免再次重复询问。

**优化方案**

- 改成平台无关的重复偏好整理，依据当前宿主选择项目指令或规则文件。
- 先合并已有规则，保留用户直接授权和作用范围，不把局部风格推广成全局。

**升级后的验收场景（尚未全量执行）**

- 用户在 Codex 指定项目习惯，不误写 .cursor/rules。
- 相同规则已有记录时更新现有文件，不新增重复条目。

**来源定位**

- [skills/suggesting-cursor-rules/SKILL.md:7](../../skills/suggesting-cursor-rules/SKILL.md#L7)：`# Suggesting Codex Rules`
- [skills/suggesting-cursor-rules/SKILL.md:31](../../skills/suggesting-cursor-rules/SKILL.md#L31)：`.cursor/rules/<name>.mdc`

## 28. ask-questions-if-underspecified

需求与规划 · 归档 · 价值：中 · 条件可用 · P1 · 维持归档

维持归档，吸收最少关键问题和明确不触发条件。

**真正的增益**：1–5 个可选问题、推荐默认值、已清楚或可通过只读检查查明时不问，有好的澄清边界。

**体量**：入口 85 行 / 3,987 字节（LF）；整个目录 3 个文件 / 7,199 规范化字节；生产 scripts 文件 0，Python 测试文件 0。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- 用户明确要求无答案继续时仍要求再次确认，重复审批。
- requirement-understanding 默认引用它，但安装器不会安装 archive。

**优化方案**

- 将优点合入统一需求入口，改正直接执行授权下的重复确认。
- 归档资源用显式相对引用或移入新入口 references，保留来源署名。

**关联/合并候选**：`requirement-understanding`、`brainstorming`。此字段也包含只迁出重叠模块的关系，不代表整个技能都要合并。

**升级后的验收场景（尚未全量执行）**

- 已明确的需求不追问。
- 必须信息缺失时问最少关键项，可独立调查继续。

**来源定位**

- [archive/skills/ask-questions-if-underspecified/SKILL.md:12](../../archive/skills/ask-questions-if-underspecified/SKILL.md#L12)：`## When NOT to Use`
- [archive/skills/ask-questions-if-underspecified/SKILL.md:55](../../archive/skills/ask-questions-if-underspecified/SKILL.md#L55)：`Ask for confirmation`

## 29. best-of-n-solving

实现与代理编排 · 归档 · 价值：低 · 条件可用 · P2 · 维持归档

parallel-agents 已覆盖多方案模式，维持历史归档。

**真正的增益**：明确候选策略、独立分支、用性能与测试比较结果，能作为概念参考。

**体量**：入口 52 行 / 2,807 字节（LF）；整个目录 1 个文件 / 2,807 规范化字节；生产 scripts 文件 0，Python 测试文件 0。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- 与 parallel-agents 场景 B 高度重叠，且写死 Cursor best-of-n-runner。
- 正文是短方法说明，无独立脚本或额外数据，不必再启用。

**优化方案**

- 只迁入当前入口缺少的实验评价条件；保留原文出处。

**关联/合并候选**：`parallel-agents`。此字段也包含只迁出重叠模块的关系，不代表整个技能都要合并。

**升级后的验收场景（尚未全量执行）**

- 当前 parallel-agents 的多方案说明完整覆盖原版判据。

**来源定位**

- [archive/skills/best-of-n-solving/SKILL.md:12](../../archive/skills/best-of-n-solving/SKILL.md#L12)：`Cursor's `best-of-n-runner``

## 30. dispatching-parallel-agents

实现与代理编排 · 归档 · 价值：低 · 条件可用 · P2 · 维持归档

parallel-agents 已覆盖独立任务模式，无需恢复启用。

**真正的增益**：聚焦、自包含、有归属和输出约定的派发方法，仍可供对照。

**体量**：入口 167 行 / 6,078 字节（LF）；整个目录 1 个文件 / 6,078 规范化字节；生产 scripts 文件 0，Python 测试文件 0。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- 场景和示例与 parallel-agents A 重叠，没有独立能力。
- 并发规则和 general-purpose 角色依赖宿主。

**优化方案**

- 作为来源快照保留；新入口补能力适配即可。

**关联/合并候选**：`parallel-agents`。此字段也包含只迁出重叠模块的关系，不代表整个技能都要合并。

**升级后的验收场景（尚未全量执行）**

- 三个无共享写状态的任务可正确分工和整合。

**来源定位**

- [archive/skills/dispatching-parallel-agents/SKILL.md:14](../../archive/skills/dispatching-parallel-agents/SKILL.md#L14)：`Dispatch one agent per independent problem domain`

## 31. slides

品牌、设计与 UI · 归档 · 价值：中 · 条件可用 · P1 · 维持归档

维持归档；HTML slide 参考与 design 内置副本应收敛成一个权威来源。

**真正的增益**：五份 HTML slides 创建、布局、模板、文案与策略参考，适合作为专用视觉资产模块。

**体量**：入口 40 行 / 1,137 字节（LF）；整个目录 6 个文件 / 19,304 规范化字节；生产 scripts 文件 0，Python 测试文件 0。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- 与 design 的 slides-* 参考和 design-system 的 slide 系统重复。
- 不是 PPTX 技能，不应把 HTML 导出承诺成原生 PowerPoint。

**优化方案**

- 逐份比对引用和内容，把 canonical slides 模块放在 design；token 入口只做样式映射。

**关联/合并候选**：`design`、`design-system`。此字段也包含只迁出重叠模块的关系，不代表整个技能都要合并。

**升级后的验收场景（尚未全量执行）**

- 请求 HTML pitch 输出 HTML；请求 PPTX 转向实际可生成 PPTX 的能力。

**来源定位**

- [archive/skills/slides/SKILL.md:12](../../archive/skills/slides/SKILL.md#L12)：`Strategic HTML presentation design`

## 32. banner-design

品牌、设计与 UI · 归档 · 价值：中 · 收录/引用不完整 · P1 · 维持归档

保留尺寸与艺术方向参考，流程并入 design，缺依赖时不恢复启用。

**真正的增益**：多平台画布尺寸、safe zone 和 HTML 到 PNG 的交付流程，具有专项参考价值。

**体量**：入口 196 行 / 8,326 字节（LF）；整个目录 2 个文件 / 13,319 规范化字节；生产 scripts 文件 0，Python 测试文件 0。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- 关键生成与导出依赖缺失：frontend-design、ai-artist、ai-multimodal、chrome-devtools。
- 默认三方案与 Pinterest 调研对单一明确需求增加无关工作。
- Meta 文本比例规则是时效性断言；Never expose file paths 会阻碍用户拿到作品。
- banner-sizes-and-styles 与 design 内置参考存在完全重复。

**优化方案**

- 使用宿主现有图像和截图工具，维护单一尺寸表，执行时核实平台规格。
- 交付预览、尺寸与用户可用文件路径，去掉禁止展示路径等无关规则。

**关联/合并候选**：`design`。此字段也包含只迁出重叠模块的关系，不代表整个技能都要合并。

**升级后的验收场景（尚未全量执行）**

- 明确尺寸的一张 banner 只生成所需数量，并返回 PNG 与实际尺寸。

**来源定位**

- [archive/skills/banner-design/SKILL.md:194](../../archive/skills/banner-design/SKILL.md#L194)：`Never expose env vars, file paths`
- [archive/skills/banner-design/SKILL.md:3](../../archive/skills/banner-design/SKILL.md#L3)：`frontend-design`

## 33. toolkit-map

技能维护与运行效率 · 外部 · 价值：高 · 依赖外部环境 · P0 · 保持外部

继续独立维护，只修本仓库的接入路径与依赖记录。

**真正的增益**：本机工具多副本来源、绝对路径、shim 与安装分离，对这台 Windows 机器有实际用途；不复制进本仓库可避免双处维护。

**问题与限制**

- 外部源需按实际机器配置；当前用户的 Projects/toolkit-map 不保证存在，安装器不下载它。
- 本轮只验证接入和当前工具查询，不代表已全面审计外部实现。

**优化方案**

- external.json 的 path 可用环境变量或仓库相对路径；明确独立维护的源目录。

**升级后的验收场景（尚未全量执行）**

- 新账户安装能定位用户指定外部目录。
- 商店别名不被误报为有效 Python，外部安装缺失时只报告。

**来源定位**

- [external.json:4](../../external.json#L4)：`%USERPROFILE%`

## 34. webapp-testing

质量、调试与审查 · 启用 · 价值：高 · 条件可用 · P2 · 保留

浏览器验证本地 Web 功能，提供 DOM 检查、截图、日志示例与服务器辅助脚本。

**真正的增益**：与 TDD 的测试方法分工不同：这里提供浏览器操作和实际界面证据。

**体量**：入口 98 行 / 4,541 字节（LF）；整个目录 7 个文件 / 23,599 规范化字节；生产 scripts 文件 1，Python 测试文件 0。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- Python Playwright 和浏览器运行时；服务器辅助脚本的进程清理未在 Windows 验证。

**优化方案**

- 按目标项目验证验收场景；更新时对照 UPSTREAM.json 的固定提交与本地修改。

**升级后的验收场景（尚未全量执行）**

- 登录页面使用 role/label 定位器验证错误提示，保存截图和控制台错误。

**来源定位**

- [skills/webapp-testing/SKILL.md:2](../../skills/webapp-testing/SKILL.md#L2)：`name: webapp-testing`
- [skills/webapp-testing/UPSTREAM.json:4](../../skills/webapp-testing/UPSTREAM.json#L4)：`8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4`

## 35. mcp-builder

实现与代理编排 · 启用 · 价值：高 · 条件可用 · P2 · 保留

开发 Python/TypeScript MCP 服务，覆盖 schema、分页、传输、错误与评估。

**真正的增益**：不同于 writing-skills 或代理编排：产物是可连接的 MCP 服务及其工具接口。

**体量**：入口 240 行 / 9,540 字节（LF）；整个目录 11 个文件 / 122,689 规范化字节；生产 scripts 文件 4，Python 测试文件 0。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- SDK 随版本变化；附带评估脚本需要 anthropic/mcp 依赖和付费 API，未执行。

**优化方案**

- 按目标项目验证验收场景；更新时对照 UPSTREAM.json 的固定提交与本地修改。

**升级后的验收场景（尚未全量执行）**

- 最小只读 MCP 工具经 Inspector 验证输入 schema、分页和错误响应。

**来源定位**

- [skills/mcp-builder/SKILL.md:2](../../skills/mcp-builder/SKILL.md#L2)：`name: mcp-builder`
- [skills/mcp-builder/UPSTREAM.json:4](../../skills/mcp-builder/UPSTREAM.json#L4)：`8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4`

## 36. supabase-postgres-best-practices

数据库与后端 · 启用 · 价值：高 · 条件可用 · P2 · 保留

Postgres 查询、索引、连接池、锁、schema 与 RLS 的具体规则和 SQL 对照。

**真正的增益**：现有库没有数据库专项规则；这些参考可用于普通 Postgres，Supabase 专属部分按环境选用。

**体量**：入口 100 行 / 5,201 字节（LF）；整个目录 38 个文件 / 65,548 规范化字节；生产 scripts 文件 0，Python 测试文件 0。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- 需要目标数据库版本与执行计划；示例性能数值不能当作本项目测量结果。

**优化方案**

- 按目标项目验证验收场景；更新时对照 UPSTREAM.json 的固定提交与本地修改。

**升级后的验收场景（尚未全量执行）**

- 对慢查询比较 EXPLAIN，并验证索引效果及跨租户 RLS 隔离。

**来源定位**

- [skills/supabase-postgres-best-practices/SKILL.md:2](../../skills/supabase-postgres-best-practices/SKILL.md#L2)：`name: supabase-postgres-best-practices`
- [skills/supabase-postgres-best-practices/UPSTREAM.json:4](../../skills/supabase-postgres-best-practices/UPSTREAM.json#L4)：`544bfc56c89afe2b87b20017a59b2c6e9502a1fb`

## 37. property-based-testing

质量、调试与审查 · 启用 · 价值：高 · 条件可用 · P2 · 保留

从输入域和不变量设计属性测试，识别同义反复、空洞断言与最小反例。

**真正的增益**：TDD 规定测试流程，这里补充生成器、缩减、往返/幂等/独立 oracle 的领域方法。

**体量**：入口 68 行 / 4,306 字节（LF）；整个目录 11 个文件 / 60,269 规范化字节；生产 scripts 文件 0，Python 测试文件 0。文本统一 LF，二进制原样计数，字节数不等于 token 数。

**问题与限制**

- 需项目相应的属性测试库；没有合适代数性质时使用普通样例测试。

**优化方案**

- 按目标项目验证验收场景；更新时对照 UPSTREAM.json 的固定提交与本地修改。

**升级后的验收场景（尚未全量执行）**

- 为序列化器设计往返属性，用生成器找到边界反例并保存回归用例。

**来源定位**

- [skills/property-based-testing/SKILL.md:2](../../skills/property-based-testing/SKILL.md#L2)：`name: property-based-testing`
- [skills/property-based-testing/UPSTREAM.json:4](../../skills/property-based-testing/UPSTREAM.json#L4)：`82fe8226252622fa807643bdca1710901198553a`

## 完全重复的文本资源

下表按 LF 规范化后 SHA-256 分组，只收录跨 skill 的相同文本，排除测试 fixtures。完全相同只证明这些资源可统一来源，不证明两个技能整体等价。

- [archive/skills/banner-design/references/banner-sizes-and-styles.md](../../archive/skills/banner-design/references/banner-sizes-and-styles.md)；[skills/design/references/banner-sizes-and-styles.md](../../skills/design/references/banner-sizes-and-styles.md)
- [archive/skills/slides/references/copywriting-formulas.md](../../archive/skills/slides/references/copywriting-formulas.md)；[skills/design/references/slides-copywriting-formulas.md](../../skills/design/references/slides-copywriting-formulas.md)
- [archive/skills/slides/references/create.md](../../archive/skills/slides/references/create.md)；[skills/design/references/slides-create.md](../../skills/design/references/slides-create.md)
- [archive/skills/slides/references/html-template.md](../../archive/skills/slides/references/html-template.md)；[skills/design/references/slides-html-template.md](../../skills/design/references/slides-html-template.md)
- [archive/skills/slides/references/layout-patterns.md](../../archive/skills/slides/references/layout-patterns.md)；[skills/design/references/slides-layout-patterns.md](../../skills/design/references/slides-layout-patterns.md)
- [archive/skills/slides/references/slide-strategies.md](../../archive/skills/slides/references/slide-strategies.md)；[skills/design/references/slides-strategies.md](../../skills/design/references/slides-strategies.md)
