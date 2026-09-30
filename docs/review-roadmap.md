# 审查结论与整改路线

审查日期：2026-09-30；原库基线：`d79b0c11b3dd1c89a3c39e596c8cb62ccc938f07`。原有 27 个启用技能与 5 个归档技能已逐项审查，随后合入 4 项带固定上游版本的精选技能，当前共 31 个启用、5 个归档；toolkit-map 只审外部登记与本轮接入表现。

## 判断

值得保留的资产集中在：**本地可检索数据、可执行工具、非显然的操作约束和能复现的验证场景**。主要问题是多个宽泛流程入口同时生效，形成重复确认、重复计划、重复审查；其次是本机历史路径、外部依赖和丢失的维护资源。

“模型本来会做”不是唯一删除理由：环境、证据保护或具体接口约束仍可值得保留。但只重述一般流程、无限扩大触发条件、要求反复证明服从的内容，增益较低。真正价值应通过相同任务有/无技能的结果与成本比较证明；本轮没有做全库真实任务 A/B，所以评级是基于全文和局部工具验证的专业判断。

每项结论、来源与验收场景见 [逐项审查](skill-review.md)。当前安装状态不随建议自动变化。

## 建议保留的能力边界

| 能力 | 处理建议 | 为什么保留 |
|---|---|---|
| UI/UX 检索与设计决策 | ui-ux-pro-max 重点升级 | 本地数据、检索实现、数据契约和回归场景是实质资产 |
| 品牌 / token / 技术栈实现 | brand、design-system、ui-styling 分别保留 | 品牌定义、系统映射、组件实现的输入输出不同；收窄触发即可 |
| 视觉资产 / 静态艺术 | design、canvas-design 分别保留 | logo/CIP/banner 与静态艺术构图不同；移除互相抢占的职责 |
| 环境 / 应用根因 | env-doctor、systematic-debugging 分别保留 | 启动条件和业务缺陷不是同一种问题；保持清晰路由 |
| 并行 / 计划执行 | parallel-agents 与统一 execute-plan 各保留 | 前者解决独立任务与多方案隔离，后者解决依赖、恢复与验收 |
| Git worktree / 交付 | 两个现有入口保留、完善 | 隔离检测和成果保护有专业细节 |
| 图谱 / 安全包路由 | graphify、reverse-skill 专项使用 | 独特能力，应从依赖可验证且任务确需的条件触发 |
| DeepSeek 供应商适配 | 条件使用，保留专用适配 | 用户明确额度与供应商需求时成立，不当通用代理入口 |
| 技能质量评估 | writing-skills 精简 | 真实对照、回归与误触发评估有价值，静态修改不必付费反复测试 |

## 六组去重与合并决策

| 组 | 未来权威入口 | 迁移内容 | 不应丢掉的东西 |
|---|---|---|---|
| requirement-understanding + brainstorming + 归档 ask-questions | 一个需求/方案入口 | 最少问题、范围和验收；复杂度分流；按需架构参考 | 明确需求直接执行；缺失关键信息才等待；复杂方案真实取舍 |
| executing-plans + subagent-driven-development | 一个 execute-plan 入口 | inline / delegated 两种模式；任务账本、契约、审查包放 references/scripts | 压缩后恢复、文件归属、全任务提交区间、风险合比例检查 |
| requesting-code-review + receiving-code-review | 一个 code-review 入口 | 审查模式、反馈落实模式各自参考 | 只读评审、真实证据、有理有据的异议、未提交成果覆盖 |
| verification-before-completion + finishing | finishing 引用共享验证参考 | 简短验证契约移入质量参考，被执行和收尾复用 | 检查到底证明了什么；证据绑定代码状态；真实授权与成果保护 |
| parallel + 归档 best-of-n / dispatching | parallel-agents | 后两者已被 A/B 模式实质覆盖，只补遗漏约束 | 多方案隔离、实际可用角色、预算和成功判据 |
| design 的 banner/slides + 归档 banner/slides + design-system 的 slide 模块 | design 中单一视觉资产模块 | 模板、尺寸、创建流程与 slide 搜索数据；token 技能只做映射 | 来源署名、截图能力、输出格式区别、实际视觉复核 |

以入口为单位，前四组各减少一个启用入口，再把 using-superpowers 从默认集归档，**原 27 可收敛为 22 个入口**；加上 4 个专项新增项，当前 31 可收敛为 26，能力仍保留。归档模块迁移不计入这个数量；token-efficient-workflow 若转成宿主规则，可再少一个入口。数字是方案结果，不是数量目标。

迁移顺序：检查调用者 → 建立/精简权威入口 → 迁移必要参考与署名 → 更新调用者 → 跑契约与真实任务场景 → 更新 manifest/catalog → 旧入口进入 archive。不要直接删除目录，既有安装联接需通过安装器迁移。

## 完全重复的资源

LF 规范化字节哈希确认 **6 组**完全相同的跨技能文本：归档 banner 的尺寸风格参考，与 design 内置副本相同；归档 slides 的五份参考，与 design 的五份 slides-* 相同。

完整路径见 [逐项审查末尾](skill-review.md)。归档副本有来源快照价值，实际加载与维护应只走一个版本。职责重叠的其他组属于语义审查结论，不是字节级重复。

## P0：先恢复可用性

1. **UI/UX 维护链**：test_catalog_refresh 寻找 scripts/refresh-google-fonts.py 与 refresh-icon-catalog.py；test_relevance_evaluator 寻找 scripts/evaluate-relevance.py，三者均未收录。两组测试在模块加载阶段 StopIteration。恢复真实维护脚本并适配目录，或显式拆分维护/运行包；不能通过删除失败测试宣称通过。
2. **路径解析**：external.json、reverse-skill、token-efficient-workflow 仍固定旧 Administrator 路径。DeepSeek 的旧 fallback 同样有此问题，现已替换为按当前用户/显式配置定位的 API helper，不再依赖模型目录或 rtk。
3. **失效引用**：UI/UX Quick Reference §1–§9 不存在；requirement-understanding 指向不默认安装的 ask-questions；design/banner 指向未收录技能。明确可选、必需与替代路径。
4. **graphify 接口与环境**：将 Bash 临时流程整理成跨平台工具；避免系统 Python 强制安装；按实际代理 schema 执行，不使用旧版 close_agent / handle 约定。记录 graphifyy 包版本和源文件 freshness，图文件存在不证明图有效。
5. **视觉工具适配**：Gemini、浏览器截图和缺失技能需有实际可用性预检。模型 ID 与平台规格在执行时核验，提供明确失败与替代路径；本轮未调用付费模型，不宣称生成 API 可用。

本轮已修复数据换行哈希失配、token-efficient-workflow UI 元数据结构，并按用户追加请求实质升级 DeepSeek 专属 skill。其他 P0 保留为后续工作。

## P1：控制误触发、冲突与成本

- 按六组方案收敛职责；brand / design-system / ui-styling 调整边界，不整体合成巨型入口。
- using-superpowers 建议归档：starting any conversation / 1% chance 没有独立产出，与宿主发现能力重复；先改 REQUIRED 引用与平台参考。
- 普通明确任务取消重复批准、自动提交文档、固定执行菜单；以已有授权和真正缺失信息判断是否等待。
- TDD 去掉 Delete code 和普通配置修改需批准豁免；审查按风险安排；证据绑定代码状态，代码不变不重复全量验证。
- 超过开放规范建议 500 行的三个入口：graphify 711、writing-skills 679、subagent-driven-development 568。模式流程迁到按需 references，保留关键约束。
- debugging 示例输出变量值需脱敏；分支收尾加入 submodule 判别与真实工作区归属；SDD ledger 使用规范路径哈希避免同名计划碰撞，清理前保存证据。
- 平台参考以当前工具 schema 为准，不固化角色、模型名和等待函数，不从技能安装情况推断工具可用性。

## P2：维护与度量

- 来源记录 primary upstream、license、revision、本地改造原因与复核日期。ATTRIBUTION 的市场集合对应关系不能直接当原作者或已核实版本。
- manifest files/bytes 属历史缓存，与现行规范化统计有差异，也可能含换行口径不同；安装器不读取。未来移除无用缓存或自动生成，安装目标保持单一来源。
- env-doctor 根据真实锁文件、端口与容器/PnP 环境判断；ui-styling 按 Tailwind 配置模式分流；canvas-design 去掉虚构用户反馈，验收必需文本、尺寸与字形。
- suggesting-cursor-rules 统一平台命名与落点；token 共用规则考虑放在宿主规则，减少重复加载。
- 扩展完整 YAML 校验、依赖预检、模板 round trip、误触发任务集和能力探测。当前 audit 明确不以 regex 伪装完整 YAML 验证。

评估卡建议：3 个正常场景、1 个不应触发场景、1 个依赖缺失场景；复杂技能增加故障恢复。比较有/无 skill 的正确率、用户等待次数、token/时间、回归与越界改动，先小样本观察再扩样，不能只统计是否复述“必须”。

## 安装器与仓库治理

保持安装器不变。DryRun 暴露：`-Only` 只过滤库内 skill，不过滤 external；指定两个 skill 仍处理 shared。external 源缺失只打印提示，退出码仍为 0，安装成功不能只看退出码。

静态审查另发现：shared 目标若已是异源联接，shared 分支没有像 skill 分支一样先替换，可能发生创建冲突。未对真实目录试验。后续在临时 USERPROFILE 下测试幂等、过滤、路径、异源联接、源缺失与卸载，不对本机已装技能做试验。

## 本轮改动

- README 改为导航；原历史与换机记录完整保存到 repository-history.md。
- catalog.json 对 37 个条目八类整理（原有 33 项 + 精选新增 4 项）；派生目录和逐项审查都有证据路径与行号。
- audit 脚本和 5 个标准库测试检查覆盖、证据、入口长度、历史缓存差异与文本重复，不执行技能。
- smoke 脚本在临时项目运行 10 个离线检查；无外部 API 调用。
- .gitattributes 固定 UI/UX 数据 LF；4 个文件恢复 LF 后**全部匹配原有 SHA-256**，未改摘要或 verifiedAt，没有伪造刷新日期。
- token-efficient-workflow UI 字段放入 interface，缩短描述并明确 `$token-efficient-workflow`。
- DeepSeek skill 改为标准库直接 API 助手：只读上下文、并发小任务、输入/输出预算、凭据保护、真实用量与明确失败状态。已在本机安装，并按用户要求在 Codex 全局 AGENTS.md 写入适用 skill、工具地图和 DeepSeek 调用规则。
- 合入另一位 agent 已提交的 4 个精选入口，当前 31 个启用、5 个归档、1 个外部登记。没有实施合并/归档建议，也没有合并默认分支；并行工作停止后完成统一收尾。

## 实测记录与边界

| 检查 | 结果 | 覆盖与限制 |
|---|---|---|
| 仓库 audit 自有测试 | 5/5 通过 | 遗漏技能、证据失效、项目产物不误报硬错误、CRLF/LF 重复识别 |
| 离线 smoke | 10/10 通过 | 42 个库内 Python 语法、数据校验、四类检索、品牌同步、token 生成/混合行回归、Tailwind JS 输出语法 |
| UI/UX 数据校验初始 | 4 项哈希失配 | raw hash 不符，全部 LF 后匹配原摘要 |
| UI/UX 数据校验修复后 | 通过 | 12 个 domain、22 个 stack 与 reasoning；不证明线上源刷新 |
| UI/UX unittest 初始 | 132 个结果中 1 failure + 2 errors | 哈希测试失败；两组模块缺维护脚本无法加载 |
| UI/UX unittest 修复后 | 130 个可加载测试通过，2 个模块加载错误仍在 | 仍为 FAILED(errors=2)，不能称全量通过；无法启动的模块各自可能有多个内部用例 |
| pytest 系测试 | 未跑完整 suite | 当前 Python 无 pytest，未安装依赖；brand/validator 核心回归由 smoke 重现，ui-styling 全部 pytest 未跑 |
| 安装器 DryRun | 返回 0，显示 1 个外部源缺失 | 两个指定 skill 到 codex；未真实安装/卸载，退出 0 不证明全环境可安装 |
| DeepSeek API 助手 | probe + 2 个并发任务成功 | 返回 deepseek-flash；Windows DPAPI；两任务合计 10080 token、约 6 秒；源码 review 和 skill 场景结果经主代理复核，未做 GPT 成本/速度对照 |
| DeepSeek 离线测试 | 11/11 通过 | HTTP 契约、精确片段、预算/密钥/路径预检、截断、错误不重试、401/403 停止未启动任务、模型拒绝、并发与 DPAPI |
| skill-creator quick_validate | 未完成 | 当前 Python 缺少 PyYAML，未为了静态校验安装第三方依赖；入口约束与引用另外核对，不宣称完整 YAML 校验 |
| 其他 API/图像/图谱任务 | 未运行 | 其他技能的供应商、图像输出与图谱构建仍未实测 |

smoke 使用 Python 3.12.14、Node 16.20.2。Node 16 只用于本轮本地脚本，不是对现代 UI 工具链版本要求的建议。机器路径来自运行时与 toolkit-map；后者误把商店别名列为有效 Python 首选，本轮使用已登记的真实 Python 候选。

结果见 [smoke-results.json](smoke-results.json)、[audit-findings.json](audit-findings.json)、[deepseek-validation.json](deepseek-validation.json)。warning/hint 对历史缓存、入口长度和引用线索提供人工检查提示，不作为新错误或完整行为证明。

## 依据

- [Agent Skills 开放规范](https://agentskills.io/specification)：名称/描述、相对引用和渐进加载；500 行是建议，description 的 1024 字符上限不针对整个 frontmatter。
- 已安装 skill-creator 的评审原则：非显然知识、精准触发、尊重范围、按风险定流程、按需加载。它提供框架，不代表第三方技能必须采用统一模板。
- 仓库 SKILL.md、关键脚本、模板、数据与现有测试；来源位置由 audit 自动重新定位。

历史市场可恢复性、机器工具清单和第三方许可未逐项重新证实；不据此宣称已经获得分发许可或投入生产。
