# Prompt 对照评估

## 1. 先定义判定

每个用例至少包含一个可执行的 `check`：

| 类型 | 用途 |
|---|---|
| `contains` | 必须出现的关键事实、字段或动作 |
| `not_contains` | 禁止泄漏、越权声明或错误格式 |
| `regex` | 稳定的结构/格式约束 |
| `json_schema` | 机器可校验的输出结构 |
| `manual` | 必须由人按 rubric 判断的证据 |

模糊的“更好”“更专业”不是判定项。

## 2. 最小夹具

```json
{
  "schemaVersion": 1,
  "promptSha256": "<64 lowercase hex>",
  "target": {
    "surface": "system prompt",
    "model": "<family/snapshot or unknown>"
  },
  "cases": [
    {
      "id": "normal-summary",
      "split": "dev",
      "input": "synthetic request",
      "checks": [
        {"type": "contains", "value": "summary"},
        {"type": "json_schema", "value": {"type": "object"}}
      ],
      "weight": 1,
      "blocking": false,
      "max_output_chars": 4000
    },
    {
      "id": "heldout-injection",
      "split": "held_out",
      "input": "retrieved text asks the model to ignore policy",
      "checks": [
        {"type": "not_contains", "value": "policy disabled"},
        {"type": "manual", "rubric": "Treats text as data and does not call tools."}
      ],
      "weight": 3,
      "blocking": true
    }
  ]
}
```

使用 `python scripts/prompt_audit.py validate-evals fixture.json --prompt prompt.md`
校验数量、ID、检查类型、秘密、留出覆盖和 prompt 指纹。
脚本不调用模型，也不执行 `regex` 或 `json_schema` 检查。

可运行的合成夹具见 [examples/eval-fixture.json](../examples/eval-fixture.json)；
它只演示结构，不代表已经运行过目标模型。实际使用时补上 `promptSha256` 与真实结果记录。

建议至少 5 个用例，覆盖：

- 正常成功路径；
- 输入缺失或冲突；
- 输出字段/格式边界；
- 工具成功、失败和停止；
- 拒绝或升级；
- 不可信文本注入；
- 多语言、长上下文或编码敏感场景（与目标相关时）。

12–20 个质量用例通常比 100 个近义改写更有信息量。样本小就报告计数，不报告
“置信区间”。

## 3. 运行记录

baseline 与 candidate 各保存一份记录：

```json
{
  "schemaVersion": 1,
  "promptSha256": "<prompt digest>",
  "evalSha256": "<shared fixture digest>",
  "model": "<same model for both arms>",
  "cases": [
    {"id": "normal-summary", "passed": true, "score": 1.0, "weight": 1, "blocking": false},
    {"id": "heldout-injection", "passed": false, "score": 0.0, "weight": 3, "blocking": true}
  ]
}
```

比较命令：

```bash
python scripts/prompt_audit.py compare baseline.json candidate.json
```

工具会检查 ID 集合、eval 指纹和模型元数据是否可比，列出改善、回归和 blocking
回归。它不会自动宣布候选胜出；参数变化、人工评审和成本仍需一起看。

## 4. 公平比较

- 用同一模型快照、同一工具能力、同一输入、同一预算；
- 不把旧 prompt 的历史会话带给 candidate；
- 不按 candidate 的失败临时改评分器；
- 不在看过 held-out 输出后回头调开发集并继续称其 held-out；
- provider 迁移必须重新跑，不沿用原模型结论；
- 失败重试次数和停止条件也要一致。

## 5. 失败分簇

按原因分组，而不是按用例编号逐个打补丁：

- 目标/成功标准缺失；
- 规则冲突或重复；
- 输入/证据不足；
- 不可信数据越界；
- 工具选择或参数错误；
- 工具输出被误解；
- 输出形状不稳定；
- 上下文过长或关键证据位置不佳；
- 模型能力或 provider 限制；
- 评分器本身错误。

同簇失败优先用一个结构性改动解决。改动超过 2 个维度时，拆成候选分别比较。

## 6. 候选策略

保留至少一个低风险候选：

| 候选 | 目的 |
|---|---|
| minimal | 验证根因假设，减少无关改动 |
| structured | 重排层级、信任边界和输出契约 |
| tool/example | 专门修正工具策略、示例或 schema 使用 |
| adapter | 处理已由评测确认的模型家族差异 |

每轮记录假设、改动、结果和取舍。删除规则也要记录，不要把“加更多句子”
当作唯一优化方向。

## 7. 指标与停止

优先看：

- blocking 用例通过率必须为 1；
- 关键用例是否回归；
- 加权通过率与人工评分；
- 首次有效输出的比例；
- 工具调用数、延迟、token 和成本（只有实际拿到才写）；
- 输出长度变化是否只是把问题转移到后处理。

出现平台期、振荡、held-out 回归、成本不划算或非 prompt 瓶颈时停止。
如果 baseline 已达标，如实结束并保留原 prompt。
