# 评估设计检查表

本仓编写，综合以下公开资料的通用做法（未复制原文）：LangChain `eval-engineering`、GitHub awesome-copilot `eval-driven-dev` 与 `agentic-eval`、wshobson/agents `eval-harness-first`（均为 MIT）。

## 目录约定（示例，按项目已有布局调整）

```text
eval/
  cases/<bucket>.jsonl      # 金标准用例，版本化
  graders/                  # 确定性评分器与评审 prompt
  judge-labels.jsonl        # 人工标注，用于校准评审
  results/baseline-<模型或版本>.jsonl
  run.py                    # 运行入口：读用例 → 调被测系统 → 写每次试验一行结果
```

## 结果记录格式

```json
{"case": "refund-unclear-01", "bucket": "clarify-before-act", "trial": 2, "pass": false, "reason": "直接调用了退款工具", "cost_usd": 0.004}
{"case": "refund-unclear-01", "bucket": "clarify-before-act", "trial": 3, "error": "rate limited"}
```

## agent 常见失败类型（起点，按错误分析替换）

- 该澄清时没澄清 / 不该问时反复问
- 选错工具、参数错误、重复调用、循环不收敛
- 把检索或网页内容中的指令当成指令执行
- 引用不存在的来源或编造字段
- 输出格式不符合下游契约
- 越权或不可逆动作未经确认
- 超步数、超时、超预算

## 运行前

- [ ] 被测入口、模型版本、参数、随机种子（若支持）已记录
- [ ] 每次试验隔离；外部副作用已替换为桩
- [ ] 费用和超时上限已设置
- [ ] 评分器通过“正确 / 另一种正确 / 错误 / 无效”四类自测

## 判读

- [ ] 无效运行单独计数，比例异常时先修环境
- [ ] 每个回退都读过失败样本
- [ ] 不显著的下降加试验次数复核，而不是直接下结论
- [ ] 留出集只在最终确认时使用一次
