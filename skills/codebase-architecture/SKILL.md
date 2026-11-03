---
name: codebase-architecture
description: 找代码库的结构性摩擦并提出“加深模块”的重构候选：浅模块合并、接缝（seam）位置、可测性与 agent 可读性；也用于“给项目瘦身但不丢功能”的结构评估。产出带证据和推荐强度的候选清单，用户选定后再设计接口与迁移。Use when the user asks to improve architecture, refactor for testability, slim down / 瘦身 a codebase, find where modules are too shallow, or design a module interface. 单个 bug 用 systematic-debugging，差异审查用 code-review，新功能需求先走 requirement-understanding。
---

# 代码库架构改进

目标是更“深”的模块：小接口背后藏住大量行为，改动、缺陷和验证集中在一处。术语与原则见 [references/vocabulary.md](references/vocabulary.md)，所有建议都用这套词（模块、接口、深度、接缝、适配器、杠杆、局部性），不要混用“组件/服务/边界”。

## 1. 先定范围（YAGNI）

- 用户点名了模块、子系统或痛点：只看那里。
- 否则看近期热点：`git log --since=90.days --name-only --pretty=format: | sort | uniq -c | sort -rn | head -30`，优先最近反复改动的文件。改得少的代码加深了也很少回本。
- 先读项目已有的领域词汇（GLOSSARY、README、AGENTS.md）和架构决策记录（ADR、docs/decisions）；不重新争论已有决策，除非摩擦真实到值得重开，并在候选里写明冲突。

## 2. 探索并记录摩擦

只读探索（大仓库可派一个只读子代理）。记录真实遇到的摩擦，不套固定清单：

- 理解一个概念要在很多小模块间来回跳。
- 浅模块：接口几乎和实现一样复杂，只是转发。
- 为测试而抽出的纯函数，真正的缺陷却藏在调用方式里（没有局部性）。
- 紧耦合模块越过接缝互相泄露状态或约定。
- 没有测试，或只能绕过接口测试的部分。

对每个疑似浅模块做**删除测试**：假设删掉它，复杂度是消失（只是转发，可以并入）还是散回 N 个调用方（它在挣钱，保留）？

## 3. 给出候选清单

默认在对话里给 Markdown 清单；用户要可视化报告时，再在系统临时目录写一个自包含 HTML（不放进仓库），并告诉用户绝对路径。每个候选：

- **涉及文件/模块**
- **问题**：摩擦是什么，附具体位置或提交证据
- **方案**：改成什么样（先不写接口细节）
- **收益**：用杠杆与局部性说明，以及测试会怎样变简单
- **能力账本**（瘦身类必填）：现有每项对外行为、开关、修复和边界处理在方案后的去处；说不清去处的项不能删
- **依赖类别**与测试方式（见 vocabulary.md 的“依赖类别”）
- **推荐强度**：强烈推荐 / 值得探索 / 推测性

最后给“首选建议”：先做哪个、为什么。可撤回的工程判断自己拿主意，但改哪个候选、是否改对外接口由用户或项目负责人选定。

## 4. 选定后的设计

- 关键取舍不清时，用 `requirement-understanding` 的拷问模式逐轮确认约束、依赖、接缝位置和要保留的测试。
- 想比较接口方案时用“设计两次”：按 [references/vocabulary.md](references/vocabulary.md) 的约束给 2~3 个独立子代理（宿主支持时用 `parallel-agents`）各出一版截然不同的接口，再按深度、局部性和接缝位置比较，并给出明确推荐或混合方案。
- 新出现的领域名词写进项目词汇表；用户以“需要长期记住”的理由否决某候选时，提议记一条 ADR，避免以后重复提出。
- 实施交给 `writing-plans` / `execute-plan`，行为保护用 `test-driven-development`：先在新接口上写测试，接口稳定后删掉被取代的浅模块单元测试（替换，不叠加）。

## 反模式

- 没定范围就全仓扫描，给一长串理论重构。
- 按代码行数比判断深浅；把一个只有单一实现的接缝当成“解耦”。
- 为了“干净”删掉仍有调用方或用户依赖的能力；瘦身时说不清去处就删。
- 在用户选定候选前直接改代码或写接口细节。

<!-- provenance:start -->
> 创作归属：原创改进（基于上游）。来源、署名与许可见 [来源说明](../../ATTRIBUTION.md#codebase-architecture)。
<!-- provenance:end -->
