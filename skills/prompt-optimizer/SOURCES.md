# 来源与维护记录

## 方法与复用边界

本技能是独立编写的中文实现，方法参考了以下公开资料：

1. **Sentry `prompt-optimizer`**
   - 仓库：`https://github.com/getsentry/skills`
   - 固定提交：`d12f250460ffd961f549dbebf7eeb0cf4afd4c2e`
   - 路径：`skills/prompt-optimizer`
   - 许可：Apache-2.0
   - 参考点：契约先行、候选对照、holdout、上下文分层、provider adapter、
     停止条件与“prompt 不总是瓶颈”的边界。
   - 未搬运其 `SKILL.md`、`SPEC.md`、`SOURCES.md`、references 原文或示例。

2. **本仓 `writing-skills`**
   - 参考点：触发与执行分开、公平对照、预算感知、冻结留出题、证据与许可边界。
   - 本技能只使用评估纪律，不复制技能编写流程。

3. **Trail of Bits `static-analysis`（仅方法审阅）**
   - 仓库：`https://github.com/trailofbits/skills`
   - 固定提交：`196a9073ab10d35bacf111f945e02c00b2c6883a`
   - 许可：CC-BY-SA-4.0
   - 参考点：工具执行前后要有可验证质量门、失败/跳过必须进入报告、
     不能把“运行完”当成“结果有效”。
   - 未导入其插件、脚本、SARIF 工具或大段文本；这些理念在本技能中独立重写。

## 本轮新增

- 中文入口、契约模板、评估方法、安全与工具边界、模式映射。
- `scripts/prompt_audit.py`：标准库只读静态检查、eval 夹具校验和记录结果比较。
- `tests` 之外的离线回归位于仓库根 `tests/test_prompt_audit.py`。
- 合成验收场景 `EVAL.md` / `evals/cases.json`。

## 许可决策

为避免把方法来源的许可边界写窄，本技能按 Apache-2.0 提供；上游 Sentry
署名与完整许可保存在 `UPSTREAM.json`、`NOTICE.txt`、`LICENSE.txt`。
本仓新增实现和文档的版权为 agent-skills contributors。

## Provider 事实

provider 细节（模型快照、上下文限制、工具参数、reasoning 默认值）容易漂移。
本技能不内置未经本轮核验的硬编码值；迁移前应查对应官方文档并把日期、
版本与 adapter 结论写进项目记录。

## 评估覆盖

| 维度 | 状态 | 证据 |
|---|---|---|
| 静态 prompt 结构风险 | 已覆盖 | `tests/test_prompt_audit.py` |
| eval 夹具结构与秘密检查 | 已覆盖 | 同上 |
| 结果记录比较与回归识别 | 已覆盖 | 同上 |
| 真实模型行为改善 | 未运行 | 需要目标模型、固定预算和隔离会话 |
| 触发命中率 | 未运行 | 需要只读技能清单的正反例测试 |
| 多 provider 适配 | 未运行 | 需要逐 provider 的官方资料与实际调用 |

## 维护

- 方法流程或交付格式变化：更新 `SKILL.md` 与 `SPEC.md`。
- eval 字段或脚本行为变化：同步 `references/evaluation.md`、脚本和根测试。
- 新来源或许可变化：更新 `SOURCES.md`、`UPSTREAM.json`、`NOTICE.txt`。
- 模型或 provider 事实变化：记录核验日期，不把旧结论伪装成当前事实。

## 变更记录

- 2026-10-27：创建独立实现；新增安全边界、静态审计、eval 校验、
  blocking 回归比较和合成验收场景。
