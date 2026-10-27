# Prompt Optimizer 合成验收场景

这些是维护用合成场景，**尚未在本轮真实模型会话中执行**。用于检查触发与执行行为，
不是已完成的行为评估或效果认证。

`evals/cases.json` 是人工审查场景库，不是 `prompt_audit.py validate-evals` 的机器
fixture schema。需要验证 fixture 结构时，使用 `examples/eval-fixture.json`；需要把
fixture 绑定到具体 prompt 时，fixture 必须包含 `promptSha256`，再传 `--prompt`。

## 触发正例

- “把这个 coding agent 的 system prompt 改好，并证明改动有效。”
- “诊断这个 prompt 为什么经常漏掉输出字段。”
- “把这段提示词从 OpenAI 迁到另一个模型，保留 portable base。”
- “帮我设计 prompt eval 和 held-out 用例。”
- “这个工具型 prompt 会不会被网页里的指令劫持？”

## 触发反例

- “帮我写一封邮件。”
- “创建一个新的 Codex skill。”
- “审查这个 PR。”
- “把 temperature 从 0.2 调到 0。”
- “总结这份文档。”
- “直接回答这个问题，不要改提示词。”

## 执行判定

逐条对照 `evals/cases.json`：

1. 是否先判断瓶颈，而不是直接重写？
2. 是否记录模型、输入、工具、输出和预算？
3. 是否把不可信内容与指令分开？
4. 是否给出可执行输出契约，而不是形容词？
5. 是否有 baseline、candidate、留出题或明确“未运行”的边界？
6. 是否报告回归、成本和未覆盖范围？

评估时用新会话、同任务、同工具和同预算；触发测试只提供技能名称与描述。
静态 lint 通过只说明结构线索，不替代执行测试。
