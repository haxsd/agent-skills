---
name: agent-evals
description: 为 LLM/agent 应用建立回归评估：从真实轨迹做错误分析、按失败类型建金标准用例、先写确定性评分器再用经过校准的 LLM 评审、多次试验看置信区间、和基线对比并在 CI 里拦截回退。Use when building or changing an agent/LLM app (prompts plus tools, retrieval, memory, model swap) and you need evidence it got better, when asked to 做评估集、eval harness、LLM-as-judge、回归测试 agent, or before switching models. 只改一段可复用 prompt 用 prompt-optimizer；评估技能改动用 writing-skills；普通代码单元测试用 test-driven-development。
---

# Agent / LLM 应用评估

模型输出不确定，“我试了几次看着更好”不算证据。评估要回答：在固定用例上，改动后哪些失败类型变好、哪些变坏，差异是否超出噪声。

## 0. 先定评估对象

- 被测系统：哪个入口（函数、CLI、HTTP、bot 会话），含哪些 prompt、工具、检索、记忆、模型与参数。
- 一次运行的输入与可观测结果：最终回答、工具调用序列、写入的文件/状态、花费与耗时。
- 运行隔离：每次试验从干净状态开始（临时目录、测试账号、假的外部服务）；不可逆的外部动作（发消息、付款、推送）一律替换为桩或只读模式。
- 预算：模型、试验次数、超时、单次与总费用上限，跑之前写下来。

## 1. 错误分析先于指标

- 有真实轨迹就从轨迹开始：读 30~100 条（越多越好），逐条用一句话写“哪里不对”（开放编码），再归并成 4~8 个失败类型。
- 没有轨迹时，按功能和已知风险手写多样化输入，先跑一轮再做同样的分析。
- 指标从失败类型来，而不是先选“有用性/流畅度”这类通用维度。

## 2. 金标准用例

- 每个失败类型至少几条用例；也放“应当成功”的常规用例，防止只优化难例。
- 用例是数据文件（JSONL/YAML），带 `case`、`bucket`、输入、期望（或评分说明），和代码一样提交、评审、版本化。
- 修过的线上问题补成用例；不要把评估用例拿去当 few-shot 示例或训练数据（留出一部分只用于最终确认）。
- 用例里不放真实个人数据和密钥。

## 3. 评分器：确定性优先

- 能用代码判就用代码：JSON schema、正则、精确字段、工具是否被调用及参数、文件是否生成、单元测试是否通过、是否超出步数/费用。
- 只有确实主观的维度才用 LLM 评审，并且：
  - 二元判定（通过/不通过 + 理由），不用 1~10 分；
  - 评审 prompt 写清标准和反例，一次只判一个维度；
  - 固定评审模型版本，最好与被测模型不同家族；
  - **先校准**：拿人工标注的样本（通过、不通过各至少 20 条）算真阳性率和真阴性率，`scripts/eval_report.py judge labels.jsonl`；不达标先改评审，不要拿它做决定。
- 评分器自己也要测：一个明确正确的结果、一个不同写法但正确的结果、一个错误结果、一个无效运行，分别得到预期判定。
- 区分“失败”和“无效运行”（超时、限流、环境坏了）：无效运行记 `error`，不计入通过率，但要报告数量。

## 4. 运行与对比

- 每条用例多次试验（常见 3~5 次），看通过率而不是单次结果。
- 先在当前版本上跑出**基线**并保存结果；改动后用同一用例、同一评分器、同一参数再跑。
- 汇总与对比（每行一条试验记录 `{"case","bucket","pass"}`）：

```bash
python scripts/eval_report.py summary results.jsonl
python scripts/eval_report.py compare baseline.jsonl candidate.jsonl --tolerance 0.05 --fail-on-regression
python scripts/eval_report.py --json compare baseline.jsonl candidate.jsonl
```

- `compare` 按失败类型给 95% 置信区间：下降超过容差且区间上界低于基线才标 `REGRESSION`；只下降不显著标 `drop-not-significant`，需要加试验次数再判。同时列出“基线多数通过、现在多数失败”的用例。
- 读失败样本，而不只看数字：分数变了要能说出是哪类行为变了。

## 5. 接入 CI 与维护

- 快的确定性用例进每次 CI；调用付费模型的完整评估按需或定时跑，并有费用上限。
- 基线结果和用例一起版本化；有意接受的回退要在提交说明里写明原因。
- 定期把新的线上失败归类：落入已有类型就补用例，出现新类型就新建类型和评分器。

## 交付时报告

- 被测版本、模型与参数、用例数、试验次数、无效运行数、花费。
- 各失败类型的基线 → 候选通过率与区间，回退和新失败用例。
- 评审模型的校准结果（若使用）。
- 结论只说数据支持的部分；样本不足就说样本不足。

更多设计细节见 [references/checklist.md](references/checklist.md)。

<!-- provenance:start -->
> 创作归属：原创改进（基于上游）。来源、署名与许可见 [来源说明](../../ATTRIBUTION.md#agent-evals)。
<!-- provenance:end -->
