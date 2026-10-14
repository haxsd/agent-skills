# env-doctor 历史来源说明

本文件只记录历史来源线索与核验状态，**不是** `UPSTREAM.json`：本技能没有已核验、可固定的上游仓库与
提交，因此不提供 `repository`/`commit`/`license` 这类固定版本字段，也不进入
`docs/sources/skill-provenance.json` 的 `upstreamFiles` 登记。

## 本目录内容

- `SKILL.md`、`references/`、`EVAL.md`、`evals/cases.json`、`scripts/env_key_status.py` 与本文件，是本仓
  2026 年独立编写的中文内容与实现，按本目录 `LICENSE.txt` 的 MIT 授权发布（仅覆盖上述本轮原创文件）。
- 本轮重写没有复制、没有打包、也没有执行任何第三方技能文件；键状态脚本是标准库独立实现。

## 历史来源（待核验，如实保留）

- 历史版本 `SKILL.md` 的 frontmatter 署名：JustHandled Labs，并声明 `license: MIT`。
- 该署名的原始仓库地址、收录版本与再分发授权均待核验；本仓保留此线索，不把当前重写当作该来源已核验，
  也不代它授权。
- 查证入口（仅线索，未确认对应仓库）：
  `https://github.com/search?q=%22env-doctor%22+%22JustHandled%22&type=code`

## 边界

- 本包与任何历史署名方无隶属、背书或认证关系。
- 诊断规则只用于只读检查；不授予对任何机器、项目或服务执行修复的权限。
