# 来源与署名

本仓库公开维护技能集合。每项技能分别标注创作归属、上游来源和许可；本仓库的改进不改变上游作品的署名与许可要求。

- **第三方引入**：来源于第三方，主要保留其内容；格式、路径或安装适配不宣称整项原创。
- **本仓原创**：本仓独立编写的技能文本或工具；调用外部工具不等于复制该工具，依赖单独列出。
- **原创改进（基于上游）**：本仓贡献新的流程、实现或测试，同时列出所基于的上游。原创声明仅覆盖本仓贡献。
- **待核验**：证据暂不足以确认原作者、确切版本或许可；保留已知线索，不默认视作原创。

创作归属与许可核验是两回事。公开可读、免费下载或市场同名条目均不等于再分发授权。历史内容未确认的版本或许可明确标为待核验；本次来源标注不构成全仓授权认证。

机器可读的单一登记为 [skill-provenance.json](docs/sources/skill-provenance.json)；已有固定版本继续保存在各项 `UPSTREAM.json`。本文件及各入口来源提示由 `scripts/audit_skills.py` 生成。

## requirement-understanding

[requirement-understanding](skills/requirement-understanding/SKILL.md) · 启用 · **原创改进（基于上游）**

原创贡献者：agent-skills contributors。
- 来源：[Jesse Vincent / obra](https://github.com/obra/superpowers/tree/main/skills/brainstorming)；许可：MIT（上游已核验；收录版本待核验）；收录版本：待核验。
- 来源：[Trail of Bits](https://github.com/trailofbits/skills)；许可：待核验；收录版本：待核验。

本仓贡献：
- 本仓编写中文需求入口，合并复杂度分流、最少关键问题、方案权衡和规格审查参考。

原入口为本地编写；当前目录已吸收归档技能的流程与资源，因此按原创改进标注。

## brainstorming

[brainstorming](archive/skills/brainstorming/SKILL.md) · 归档 · **第三方引入**

- 来源：[Jesse Vincent / obra](https://github.com/obra/superpowers/tree/main/skills/brainstorming)；许可：MIT（上游已核验；收录版本待核验）；收录版本：待核验。

归档保留上游设计流程和视觉辅助资源；本地整理不改变原始归属。

## writing-plans

[writing-plans](skills/writing-plans/SKILL.md) · 启用 · **原创改进（基于上游）**

原创贡献者：agent-skills contributors。
- 来源：[Jesse Vincent / obra](https://github.com/obra/superpowers/tree/main/skills/writing-plans)；许可：MIT（上游已核验；收录版本待核验）；收录版本：待核验。

本仓贡献：
- 按任务规模缩放规划流程，维护接口、依赖、规格覆盖和本地审查模板。

## executing-plans

[executing-plans](archive/skills/executing-plans/SKILL.md) · 归档 · **第三方引入**

- 来源：[Jesse Vincent / obra](https://github.com/obra/superpowers/tree/main/skills/executing-plans)；许可：MIT（上游已核验；收录版本待核验）；收录版本：待核验。

归档的顺序执行流程，当前能力已合入 execute-plan。

## execute-plan

[execute-plan](skills/execute-plan/SKILL.md) · 启用 · **原创改进（基于上游）**

原创贡献者：agent-skills contributors。
- 来源：[Jesse Vincent / obra](https://github.com/obra/superpowers/tree/main/skills/subagent-driven-development)；许可：MIT（上游已核验；收录版本待核验）；收录版本：待核验。
- 来源：[Jesse Vincent / obra](https://github.com/obra/superpowers/tree/main/skills/executing-plans)；许可：MIT（上游已核验；收录版本待核验）；收录版本：待核验。

本仓贡献：
- 统一顺序执行与委派入口，维护任务账本、审查包和工作区辅助脚本。
- 按当前宿主能力适配代理调用，保留恢复执行与成果保护规则。

## parallel-agents

[parallel-agents](skills/parallel-agents/SKILL.md) · 启用 · **原创改进（基于上游）**

原创贡献者：agent-skills contributors。
- 来源：[Jesse Vincent / obra](https://github.com/obra/superpowers/tree/main/skills/dispatching-parallel-agents)；许可：MIT（上游已核验；收录版本待核验）；收录版本：待核验。

本仓贡献：
- 本仓中文重写，区分独立任务并发与同一问题多方案试验，明确隔离和成果整合。

## deepseek-subagent-orchestration

[deepseek-subagent-orchestration](skills/deepseek-subagent-orchestration/SKILL.md) · 启用 · **本仓原创**

原创贡献者：agent-skills contributors。
- 原创维护仓库：[https://github.com/haxsd/agent-skills](https://github.com/haxsd/agent-skills)。

本仓贡献：
- 独立实现外部 DeepSeek API 工具循环、限定文件权限、命名检查、凭据保护及回归测试。

## env-doctor

[env-doctor](skills/env-doctor/SKILL.md) · 启用 · **原创改进（基于上游）**

原创贡献者：agent-skills contributors。
- 来源：[JustHandled Labs（历史入口署名）](https://github.com/search?q=%22env-doctor%22+%22JustHandled%22&type=code)；许可：MIT（历史文件声明；原始仓库、版本与授权仍待核验）；收录版本：待核验。

本仓贡献：
- 独立重写中文诊断入口、检查清单与安全案例，覆盖 PnP、工作区、容器边界、真实端口和变量来源。
- 本仓实现只读键状态工具与真实 CLI 回归，新增预算化行为评估；新 MIT 仅覆盖本轮原创文件。

当前正文和工具为本仓独立重写，历史署名及未核验来源事实保留在 skills/env-doctor/NOTICE.txt 与 SOURCE-NOTES.md；本轮原创声明不代替历史来源核验或授权。

## systematic-debugging

[systematic-debugging](skills/systematic-debugging/SKILL.md) · 启用 · **原创改进（基于上游）**

原创贡献者：agent-skills contributors。
- 来源：[Jesse Vincent / obra](https://github.com/obra/superpowers/tree/main/skills/systematic-debugging)；许可：MIT（上游已核验；收录版本待核验）；收录版本：待核验。

本仓贡献：
- 调整诊断日志和配置检查的安全边界，维护本地根因追踪、条件等待与调试参考。

## test-driven-development

[test-driven-development](skills/test-driven-development/SKILL.md) · 启用 · **第三方引入**

- 来源：[Jesse Vincent / obra](https://github.com/obra/superpowers/tree/main/skills/test-driven-development)；许可：MIT（上游已核验；收录版本待核验）；收录版本：待核验。

测试流程及 writing-good-tests 参考来自上游体系，未因本地收藏而改称原创。

## verification-before-completion

[verification-before-completion](archive/skills/verification-before-completion/SKILL.md) · 归档 · **第三方引入**

- 来源：[Jesse Vincent / obra](https://github.com/obra/superpowers/tree/main/skills/verification-before-completion)；许可：MIT（上游已核验；收录版本待核验）；收录版本：待核验。

归档原流程，验证证据规则已整理进交付技能。

## requesting-code-review

[requesting-code-review](archive/skills/requesting-code-review/SKILL.md) · 归档 · **第三方引入**

- 来源：[Jesse Vincent / obra](https://github.com/obra/superpowers/tree/main/skills/requesting-code-review)；许可：MIT（上游已核验；收录版本待核验）；收录版本：待核验。

## receiving-code-review

[receiving-code-review](archive/skills/receiving-code-review/SKILL.md) · 归档 · **第三方引入**

- 来源：[Jesse Vincent / obra](https://github.com/obra/superpowers/tree/main/skills/receiving-code-review)；许可：MIT（上游已核验；收录版本待核验）；收录版本：待核验。

## using-git-worktrees

[using-git-worktrees](skills/using-git-worktrees/SKILL.md) · 启用 · **原创改进（基于上游）**

原创贡献者：agent-skills contributors。
- 来源：[Jesse Vincent / obra](https://github.com/obra/superpowers/tree/main/skills/using-git-worktrees)；许可：MIT（上游已核验；收录版本待核验）；收录版本：待核验。

本仓贡献：
- 补充宿主管理工作区、detached HEAD 与 submodule 判别，避免重复创建和误清理。

## finishing-a-development-branch

[finishing-a-development-branch](skills/finishing-a-development-branch/SKILL.md) · 启用 · **原创改进（基于上游）**

原创贡献者：agent-skills contributors。
- 来源：[Jesse Vincent / obra](https://github.com/obra/superpowers/tree/main/skills/finishing-a-development-branch)；许可：MIT（上游已核验；收录版本待核验）；收录版本：待核验。
- 来源：[Jesse Vincent / obra](https://github.com/obra/superpowers/tree/main/skills/verification-before-completion)；许可：MIT（上游已核验；收录版本待核验）；收录版本：待核验。

本仓贡献：
- 整合验证证据契约与成果保护，区分命名分支、detached HEAD 和外部管理工作区。

## ui-ux-pro-max

[ui-ux-pro-max](skills/ui-ux-pro-max/SKILL.md) · 启用 · **原创改进（基于上游）**

原创贡献者：agent-skills contributors。
- 来源：[Next Level Builder](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)；许可：MIT（当前上游已核验；本地收录版本待核验）；收录版本：待核验。

本仓贡献：
- 维护本地检索数据、原生桌面技术栈、来源记录、数据契约及回归测试。

本地数据与脚本有扩展，不能用当前上游版本冒充本地内容的完整来源。

## brand

[brand](skills/brand/SKILL.md) · 启用 · **原创改进（基于上游）**

原创贡献者：agent-skills contributors。
- 来源：[Claudekit（原文件署名）](https://github.com/claudekit)；许可：待核验；收录版本：待核验。

本仓贡献：
- 维护品牌模板到设计 token 的同步回归测试，补充项目资源与脚本路径边界。

作者组织已知，精确技能仓库、收录版本和许可仍待核验；同名市场副本不视为原始作者证据。

## design-system

[design-system](skills/design-system/SKILL.md) · 启用 · **原创改进（基于上游）**

原创贡献者：agent-skills contributors。
- 来源：[Claudekit（原文件署名）](https://github.com/claudekit)；许可：待核验（原文件声明 MIT，尚未证实再分发授权）；收录版本：待核验。

本仓贡献：
- 维护分层 token、组件规范、幻灯片数据与生成校验工具，增加相关回归测试。

精确上游技能仓库仍待核验，不把市场同名条目当作同一版本。

## ui-styling

[ui-styling](skills/ui-styling/SKILL.md) · 启用 · **原创改进（基于上游）**

原创贡献者：agent-skills contributors。
- 来源：[Claudekit（原文件署名）](https://github.com/claudekit)；许可：待核验（原文件声明 MIT，尚未证实再分发授权）；收录版本：待核验。

本仓贡献：
- 维护组件添加、Tailwind 配置生成与脚本回归测试，补充技能根目录调用边界。

许可冲突：SKILL.md 声明 MIT，但本目录 LICENSE.txt 是 Apache-2.0；尚未确认两者各自适用范围。Claudekit 原产品为付费分发，公开 CLI 的许可证不等于技能内容授权，精确来源和收录版本待核验。

## design

[design](skills/design/SKILL.md) · 启用 · **原创改进（基于上游）**

原创贡献者：agent-skills contributors。
- 来源：[Claudekit（原文件署名）](https://github.com/claudekit)；许可：待核验（原文件声明 MIT，尚未证实再分发授权）；收录版本：待核验。

本仓贡献：
- 维护视觉资产路由、Logo/CIP 检索数据及本地生成工具，补充资源依赖说明。

精确上游技能仓库与收录版本待核验；聚合市场副本不是原创证明。

## canvas-design

[canvas-design](skills/canvas-design/SKILL.md) · 启用 · **第三方引入**

- 来源：[Anthropic](https://github.com/anthropics/skills/tree/main/skills/canvas-design)；许可：Apache-2.0（目录 LICENSE.txt；精确收录版本待核验）；收录版本：待核验。

字体资产另按 canvas-fonts 中各自许可适用。

## graphify

[graphify](skills/graphify/SKILL.md) · 启用 · **第三方引入**

- 来源：[Graphify Labs / safishamsi](https://github.com/Graphify-Labs/graphify)；许可：Apache-2.0（当前上游已核验；本地收录版本待核验）；收录版本：本地标记 0.9.56；对应提交待核验。

原 safishamsi/graphify 已转为 Graphify-Labs/graphify。保留第三方主体归属；版本标记不等于已确认的固定收录提交。

## reverse-skill

[reverse-skill](skills/reverse-skill/SKILL.md) · 启用 · **本仓原创**

原创贡献者：agent-skills contributors。
- 原创维护仓库：[https://github.com/haxsd/agent-skills](https://github.com/haxsd/agent-skills)。
- 外部依赖（非技能文本来源）：[zhaoxuya520](https://github.com/zhaoxuya520/reverse-skill)；许可：MIT（当前外部仓库已核验；未将包体纳入本仓）。

本仓贡献：
- 本仓编写外部安全研究技能包的路由入口、定位与预检规则；不打包外部技能包本体。

原创声明仅覆盖本仓路由文本，不覆盖外部安全研究技能包。

## writing-skills

[writing-skills](skills/writing-skills/SKILL.md) · 启用 · **原创改进（基于上游）**

原创贡献者：agent-skills contributors。
- 上游：[Anthropic, PBC.](https://github.com/anthropics/skills)；许可：Apache-2.0；固定版本：`dbd4588f9e1033efb41dad4bef2f7947c8993d44`。详情：[skills/writing-skills/UPSTREAM.json](skills/writing-skills/UPSTREAM.json)。
- 来源：[Jesse Vincent / obra](https://github.com/obra/superpowers/tree/main/skills/writing-skills)；许可：MIT（历史来源；原收录版本待核验）；收录版本：待核验。
- 来源：[Functional Software, Inc. dba Sentry](https://github.com/getsentry/skills/tree/d18b7aa8ba878354e5c348310230e652f7690f9c/skills/skill-writer)；许可：Apache-2.0（本轮方法参考）；收录版本：d18b7aa8ba878354e5c348310230e652f7690f9c。

本仓贡献：
- 重写为改动风险分级、旧新公平对照、触发与执行分离、冻结留出题及质量/安全/成本评估，取消无条件昂贵评估规则。
- 新增可重复案例和评估参考；修正旧格式与授权约束，按文件保留 Anthropic/Sentry Apache-2.0 和历史 obra MIT 许可。

固定 Anthropic skill-creator 与 Sentry skill-writer 只作方法参考，未搬运或执行自动模型脚本；未改写旧资源维持历史许可，原始收录版本不冒充当前上游版本。

## using-superpowers

[using-superpowers](archive/skills/using-superpowers/SKILL.md) · 归档 · **第三方引入**

- 来源：[Jesse Vincent / obra](https://github.com/obra/superpowers/tree/main/skills/using-superpowers)；许可：MIT（上游已核验；收录版本待核验）；收录版本：待核验。

归档保留上游技能发现与宿主适配资料。

## token-efficient-workflow

[token-efficient-workflow](skills/token-efficient-workflow/SKILL.md) · 启用 · **本仓原创**

原创贡献者：agent-skills contributors。
- 原创维护仓库：[https://github.com/haxsd/agent-skills](https://github.com/haxsd/agent-skills)。

本仓贡献：
- 本仓维护共用上下文效率规则与 Codex 入口，明确可选项目辅助脚本和持续性状态更新条件。

## suggesting-rules

[suggesting-rules](skills/suggesting-rules/SKILL.md) · 启用 · **本仓原创**

原创贡献者：agent-skills contributors。
- 原创维护仓库：[https://github.com/haxsd/agent-skills](https://github.com/haxsd/agent-skills)。

本仓贡献：
- 本仓编写重复偏好沉淀流程，按宿主选择规则落点，先检查既有规则避免重复。

## ask-questions-if-underspecified

[ask-questions-if-underspecified](archive/skills/ask-questions-if-underspecified/SKILL.md) · 归档 · **第三方引入**

- 来源：[Trail of Bits](https://github.com/trailofbits/skills)；许可：待核验；收录版本：待核验。

保留原组织标识；确切收录提交与对应许可待核验。

## best-of-n-solving

[best-of-n-solving](archive/skills/best-of-n-solving/SKILL.md) · 归档 · **待核验**

- 来源：[原作者待核验；历史归档指向 superpowers 系方法](https://github.com/obra/superpowers)；许可：此具体技能许可待核验；收录版本：待核验。

同上游体系相关不等于已确认由该作者编写；保留来源线索，不宣称原创或已授权。

## dispatching-parallel-agents

[dispatching-parallel-agents](archive/skills/dispatching-parallel-agents/SKILL.md) · 归档 · **第三方引入**

- 来源：[Jesse Vincent / obra](https://github.com/obra/superpowers/tree/main/skills/dispatching-parallel-agents)；许可：MIT（上游已核验；收录版本待核验）；收录版本：待核验。

## slides

[slides](archive/skills/slides/SKILL.md) · 归档 · **第三方引入**

- 来源：[Claudekit（原文件署名）](https://github.com/claudekit)；许可：待核验；收录版本：待核验。

归档 HTML slides 技能；精确上游技能仓库、收录版本与许可待核验。

## banner-design

[banner-design](archive/skills/banner-design/SKILL.md) · 归档 · **第三方引入**

- 来源：[Claudekit（原文件署名）](https://github.com/claudekit)；许可：待核验（原文件声明 MIT，尚未证实再分发授权）；收录版本：待核验。

精确上游技能仓库与收录版本待核验。

## toolkit-map

toolkit-map · 外部 · **本仓原创**

原创贡献者：haxsd / toolkit-map contributors。
- 原创维护仓库：[https://github.com/haxsd/toolkit-map](https://github.com/haxsd/toolkit-map)。

本仓贡献：
- 独立维护的本机工具发现、验证和选择层。

原创作品在独立仓库维护；本仓只登记外部入口和安装目标，不复制技能内容，许可以原仓库为准。

## webapp-testing

[webapp-testing](skills/webapp-testing/SKILL.md) · 启用 · **原创改进（基于上游）**

原创贡献者：agent-skills contributors。
- 上游：[anthropics/skills](https://github.com/anthropics/skills)；许可：Apache-2.0；固定版本：`8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4`。详情：[skills/webapp-testing/UPSTREAM.json](skills/webapp-testing/UPSTREAM.json)。

本仓贡献：
- 将固定等待建议调整为可观察界面状态等待，补充宿主浏览器映射、相对路径和进程清理限制。

## mcp-builder

[mcp-builder](skills/mcp-builder/SKILL.md) · 启用 · **第三方引入**

- 上游：[anthropics/skills](https://github.com/anthropics/skills)；许可：Apache-2.0；固定版本：`8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4`。详情：[skills/mcp-builder/UPSTREAM.json](skills/mcp-builder/UPSTREAM.json)。

本地仅补充宿主工具映射、路径与可选付费评估边界，主体保持上游归属。

## supabase-postgres-best-practices

[supabase-postgres-best-practices](skills/supabase-postgres-best-practices/SKILL.md) · 启用 · **第三方引入**

- 上游：[supabase/agent-skills](https://github.com/supabase/agent-skills)；许可：MIT；固定版本：`544bfc56c89afe2b87b20017a59b2c6e9502a1fb`。详情：[skills/supabase-postgres-best-practices/UPSTREAM.json](skills/supabase-postgres-best-practices/UPSTREAM.json)。

保留上游数据库规则；本地主要补充发现入口，不宣称主体原创。

## property-based-testing

[property-based-testing](skills/property-based-testing/SKILL.md) · 启用 · **第三方引入**

- 上游：[trailofbits/skills](https://github.com/trailofbits/skills)；许可：CC-BY-SA-4.0；固定版本：`82fe8226252622fa807643bdca1710901198553a`。详情：[skills/property-based-testing/UPSTREAM.json](skills/property-based-testing/UPSTREAM.json)。

原许可 CC-BY-SA-4.0 继续适用。

## development-workflow

[development-workflow](skills/development-workflow/SKILL.md) · 启用 · **本仓原创**

原创贡献者：agent-skills contributors。
- 原创维护仓库：[https://github.com/haxsd/agent-skills](https://github.com/haxsd/agent-skills)。

本仓贡献：
- 本仓编写精简开发工作流，按范围组织计划、实施、验证与交付，调用既有专项技能而非复制其主体。

## code-review

[code-review](skills/code-review/SKILL.md) · 启用 · **原创改进（基于上游）**

原创贡献者：agent-skills contributors。
- 上游：[Sentry / Functional Software, Inc.](https://github.com/getsentry/skills)；许可：Apache-2.0；固定版本：`d18b7aa8ba878354e5c348310230e652f7690f9c`。详情：[skills/code-review/UPSTREAM.json](skills/code-review/UPSTREAM.json)。
  - 另借鉴：[https://github.com/trailofbits/skills](https://github.com/trailofbits/skills)；版本：`8e54050ae63c2f62224c35b1616efe71865b4777`；范围：differential-review 的 CC-BY-SA-4.0 派生文件 references/differential-review.md（中文改写、只读化、按本仓校准裁剪）；署名与相同方式共享要求见 LICENSE.txt。
- 来源：[Jesse Vincent / obra](https://github.com/obra/superpowers/tree/main/skills/requesting-code-review)；许可：MIT（上游已核验；收录版本待核验）；收录版本：待核验。
- 来源：[Jesse Vincent / obra](https://github.com/obra/superpowers/tree/main/skills/receiving-code-review)；许可：MIT（上游已核验；收录版本待核验）；收录版本：待核验。
- 来源：[Trail of Bits](https://github.com/trailofbits/skills/tree/8e54050ae63c2f62224c35b1616efe71865b4777/plugins/differential-review/skills/differential-review)；许可：CC-BY-SA-4.0（仅独立差异审查参考）；收录版本：8e54050ae63c2f62224c35b1616efe71865b4777。

本仓贡献：
- 保留只读审查与反馈入口，按差异语义选择差异影响、凭据序列化和 GitHub Actions 专项参考，不把小改动扩大为全仓审计。
- 补充实际权限、数据流与有效防护证据，分开严重程度、置信度和待确认项，新增正反例评估。

通用入口、历史 obra MIT 模板、Sentry Apache-2.0 参考与 Trail of Bits CC-BY-SA-4.0 参考按文件界定许可；原创改进不把整个目录重授单一许可。

## deepseek-subagents

[deepseek-subagents](skills/deepseek-subagents/SKILL.md) · 启用 · **本仓原创**

原创贡献者：agent-skills contributors。
- 原创维护仓库：[https://github.com/haxsd/agent-skills](https://github.com/haxsd/agent-skills)。

本仓贡献：
- 本仓编写 Codex CLI 执行型 DeepSeek 子代理调度、清单校验、进程控制与测试。

## web-design-guidelines

[web-design-guidelines](skills/web-design-guidelines/SKILL.md) · 启用 · **第三方引入**

- 来源：[Vercel](https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines)；许可：待核验（当前仓库无独立许可文件）；收录版本：本地元数据 1.0.0；对应提交待核验。
- 来源：[Vercel](https://github.com/vercel-labs/web-interface-guidelines)；许可：远程规范许可待核验；收录版本：待核验。

技能文本来源于 Vercel agent-skills；远程规范另有来源，二者分别核验。

## podcast-to-article

[podcast-to-article](skills/podcast-to-article/SKILL.md) · 启用 · **原创改进（基于上游）**

原创贡献者：agent-skills contributors。
- 上游：[冯雷 (MarsWave)](https://github.com/orange2ai/podcast-to-article)；许可：MIT；固定版本：`efc43919962e8356058057c4b5fd32c57876e6b7`。详情：[skills/podcast-to-article/UPSTREAM.json](skills/podcast-to-article/UPSTREAM.json)。

本仓贡献：
- 增加 Windows UTF-8 兼容、本地协作说明和脚本调用适配，精简不参与工作流的资源。

## work-humanizer

[work-humanizer](skills/work-humanizer/SKILL.md) · 启用 · **第三方引入**

- 上游：[Pawel Huryn](https://github.com/phuryn/work-humanizer)；许可：MIT；固定版本：`0a9065791d021f3dda695f3887cb2ae4c0eacbcf`。详情：[skills/work-humanizer/UPSTREAM.json](skills/work-humanizer/UPSTREAM.json)。

原文主体来自 Pawel Huryn；本地 slim 打包、中文触发和 Windows 编码修正不宣称整项原创。

## excalidraw-diagrams

[excalidraw-diagrams](skills/excalidraw-diagrams/SKILL.md) · 启用 · **本仓原创**

原创贡献者：agent-skills contributors。
- 原创维护仓库：[https://github.com/haxsd/agent-skills](https://github.com/haxsd/agent-skills)。
- 外部依赖（非技能文本来源）：[excalidraw/cli](https://github.com/excalidraw/cli)；许可：MIT；固定版本：`55fe7f494837078781a062c4d3faf29c159ebec5`。详情：[skills/excalidraw-diagrams/UPSTREAM.json](skills/excalidraw-diagrams/UPSTREAM.json)。

本仓贡献：
- 本仓编写本地渲染 wrapper 技能文本和最小示例，使用官方 CLI 而不复制 CLI 源码。

UPSTREAM.json 记录的是 CLI 依赖，不是本技能文本的上游；CLI 的 MIT 许可不自动覆盖本仓原创文本。

## windows-powershell-safe

[windows-powershell-safe](skills/windows-powershell-safe/SKILL.md) · 启用 · **原创改进（基于上游）**

原创贡献者：agent-skills contributors。
- 上游：[Misaka Mikoto](https://github.com/Misaka-Mikoto-Tech/agent-skills)；许可：MIT；固定版本：`711abaf61e1b8d770d355e05b75e9641afa7b25e`。详情：[skills/windows-powershell-safe/UPSTREAM.json](skills/windows-powershell-safe/UPSTREAM.json)。
  - 另借鉴：[https://github.com/agent-shells/powershell-skills](https://github.com/agent-shells/powershell-skills)；版本：`4f389f0982654b57d04646c19084e40ac7bd2a1a`；范围：Stop rules / failure-retry wording only。

本仓贡献：
- 中文精简改写，加入安全调用决策顺序、宿主版本边界、失败停止规则和经验参考。

## skill-scanner

[skill-scanner](skills/skill-scanner/SKILL.md) · 启用 · **原创改进（基于上游）**

原创贡献者：agent-skills contributors。
- 上游：[Sentry / Functional Software, Inc.](https://github.com/getsentry/skills)；许可：Apache-2.0；固定版本：`d18b7aa8ba878354e5c348310230e652f7690f9c`。详情：[skills/skill-scanner/UPSTREAM.json](skills/skill-scanner/UPSTREAM.json)。

本仓贡献：
- 本仓原创重写标准库只读扫描器、结构化脱敏输出、扫描边界与离线回归测试。
- 基于 Sentry 方法重写中文审查入口，接入 toolkit-map，移除 uv 和特定宿主硬依赖。

原创贡献仅覆盖本仓改写和实现；保留 Sentry 上游署名与 Apache-2.0。静态线索和无命中均不是安全认证。

## variant-analysis

[variant-analysis](skills/variant-analysis/SKILL.md) · 启用 · **原创改进（基于上游）**

原创贡献者：agent-skills contributors。
- 上游：[Trail of Bits](https://github.com/trailofbits/skills)；许可：CC-BY-SA-4.0；固定版本：`8e54050ae63c2f62224c35b1616efe71865b4777`。详情：[skills/variant-analysis/UPSTREAM.json](skills/variant-analysis/UPSTREAM.json)。

本仓贡献：
- 本仓中文改写已知缺陷校准、逐轴泛化、证据分诊与停止条件，加入跨宿主和缺工具回退。
- 新增独立正反例评估场景与报告契约，不绑定 Claude 插件工作流或默认安装 CodeQL/Semgrep。

基于 Trail of Bits 的原创改进；文本与改编参考继续按 CC-BY-SA-4.0 署名、标明修改并相同方式共享。
