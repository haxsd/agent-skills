# 查论文（arXiv / Hugging Face Papers）

接口用法改编自 huggingface/skills 的 `huggingface-papers`（固定版本 25910b3d0ba31a2ba102f901cdc9e008c278a69c，Apache-2.0，Copyright Hugging Face；完整许可见 `../LICENSES/Apache-2.0.txt`）。本仓中文改写，只保留只读查询，加入版本与引用要求。

## 先取论文 ID

`https://arxiv.org/abs/2305.10601`、`.../pdf/2305.10601v2`、`https://huggingface.co/papers/2305.10601` 都对应 ID `2305.10601`（带 `vN` 表示具体版本）。引用时写明版本：论文的 v1 与 v3 结论可能不同。

## 读全文与元数据（只读，无需令牌）

```bash
# 论文 Markdown（基于 arXiv HTML 版；没有 HTML 版时退回论文页内容）
curl -s "https://huggingface.co/papers/2305.10601.md"

# 结构化元数据：标题、作者、摘要、发布日期、GitHub 仓库、项目页
curl -s "https://huggingface.co/api/papers/2305.10601"

# 关键词搜索
curl -s "https://huggingface.co/api/papers/search?q=tree+of+thoughts"

# 关联的模型 / 数据集 / Space
curl -s "https://huggingface.co/api/models?filter=arxiv:2305.10601"
curl -s "https://huggingface.co/api/datasets?filter=arxiv:2305.10601"
```

- 返回 404：论文尚未被 Hugging Face 收录，改读 `https://arxiv.org/abs/<ID>`（摘要页列出全部版本和日期）。
- arXiv 官方 API `https://export.arxiv.org/api/query?id_list=<ID>` 有严格限流（遇到 429 就等待并降低频率，批量请求间隔几秒），不要循环重试。
- 认领作者、提交论文等写操作不在本技能范围。

## 读论文时的来源规则

- 结论引用论文里的具体位置（章节、表、图编号），不引用 AI 生成的摘要。
- 区分论文**声称**的结果和**独立复现**的结果；有官方代码仓库时记下提交或发布版本。
- 预印本未经同行评审要注明；发表版本（会议/期刊）与 arXiv 版本不同时以发表版本为准并写明。
