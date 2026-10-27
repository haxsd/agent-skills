# Prompt Optimizer 规格

## 目标

`prompt-optimizer` 用契约先行、对照评估的方式改进可复用 prompt。
成功不是“读起来更专业”，而是在明确目标上有可复现的行为证据，并且没有隐藏回归。

## 范围内

- 新建或重写 system/developer/user prompt、agent 指令与复用模板。
- 修复歧义、冲突、输出漂移、工具选择、停止条件和注入边界。
- 设计 prompt eval、比较候选、冻结留出题和报告残余风险。
- 在模型家族之间迁移时保留 portable base 与最小 adapter。

## 范围外

- 选择模型架构、微调、训练数据配比或推理参数调优。
- 把一次性任务包装成 prompt 工程。
- 编写或审查 agent 技能本身；使用 `writing-skills`。
- 需求澄清；使用 `requirement-understanding`。
- 要求模型输出隐藏思维链，或把 prompt 当作权限/沙箱的替代品。

## 运行契约

- 改动前记录目标、非目标、模型、作用层、输入、工具、输出和预算。
- 同一行为规则只有一个权威所有者。
- 不可信内容用稳定边界包裹，并明确只能作为数据。
- 工具有 allowlist、权限范围、失败停止和审批边界。
- 没有证据时不得声称行为改善；必须区分静态检查、冒烟观察和成对比较。

## 文件职责

- `SKILL.md`：执行流程、停止条件和交付格式。
- `references/prompt-contract.md`：prompt 分层、变量、输出与上下文契约。
- `references/evaluation.md`：eval 设计、评分、预算和对照方法。
- `references/security-and-tools.md`：注入、工具、秘密和执行边界。
- `references/patterns.md`：症状到改法、结构骨架和 provider adapter 原则。
- `scripts/prompt_audit.py`：只读静态检查、eval 夹具校验和记录结果比较。
- `SOURCES.md`：来源、许可决策、覆盖与维护记录。
- `EVAL.md` / `evals/cases.json`：技能自身的合成验收场景，不代表已执行结果。

## 验收

- 触发描述覆盖 prompt 优化、诊断、迁移和 eval，同时排除一次性写作与技能编写。
- 改动有 baseline、candidate、固定输入和明确的评分方式。
- 至少一个 held-out 用例未参与调优；报告区分已运行与未覆盖。
- 输出包包含最终 prompt、上下文/工具清单、证据和残余风险。
- 脚本只读、标准库、无网络；任何启发式结果都不冒充安全或质量认证。

## 已知限制

- 模型快照和 provider 行为会漂移；跨版本必须重跑评估。
- 小样本只能支持局部、可复现的工程判断，不能提供统计置信度。
- 没有目标模型或真实失败样本时，只能做合理的 prompt 结构改进。
- 静态扫描无法证明注入防护有效；实际安全依赖权限、沙箱和数据边界。
