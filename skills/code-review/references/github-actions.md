<!--
本文件基于 Sentry skills（commit d18b7aa8ba878354e5c348310230e652f7690f9c）的 gha-security-review 改写。
Copyright 2025 Functional Software, Inc. dba Sentry；许可：Apache-2.0。
完整许可文本见 ../LICENSES/Apache-2.0.txt；版权与修改说明见 ../NOTICE.txt。
本仓修改：中文重写；按本仓校准要求重写风险评估（证据先于结论、严重程度与置信度分开）；参数按下游执行器追踪、
威胁模型可按任务扩展；只读审查，不执行工作流，PoC 载荷用假 canary。
-->

# GitHub Actions 差异审查

审查 `.github/workflows/*.yml`、`action.yml`、本地复合动作及被工作流加载的配置文件（Makefile、shell 脚本、CI 用 agent 指令文件）。
默认威胁模型是**外部攻击者**——能开 fork PR、建 issue、发评论但没有写权限的人。任务指定内部人员、自托管 runner 或部署/发布供应链时，把假设扩展并写进审查记录，再按新模型核对；不能把"需要写权限"当作永久排除此类问题的理由。`workflow_dispatch` 输入、受保护分支 `push`、内部 `workflow_call` 等模式在默认模型下不构成外部攻击面，在扩展模型下按实际权限与影响重估。

每条发现都要能给出具体利用场景；构造不出就降为待确认或不报。**读工作流不等于运行工作流**：不执行工作流、不跑 `npm ci`/项目测试（安装与测试会触发第三方生命周期脚本）、不上传源码、不代发 PR 评论。证据不输出真实凭据值。

## 追踪链：从触发到影响

对每个工作流按数据流走一遍，任何一环缺失都改变结论：

1. **触发**：`pull_request`、`pull_request_target`、`issue_comment`、`workflow_run` 等；谁能触发（fork PR？任何 GitHub 用户？）。
2. **不可信输入**：PR 标题/正文/分支名/文件名、issue/评论正文、上次运行的 artifact/cache、被 checkout 的 PR 代码，以及经 `with:` 传给动作的值。
3. **checkout**：`ref` 是否指向 PR head 或 fork 代码；本地动作 `./.github/actions/...`、Makefile、脚本是否来自该 checkout。
4. **执行**：checkout 之后是否有 `run:` 步骤会执行这些代码（构建、测试、`npm ci`/`npm install` 的 pre/postinstall、`go run` 的 init()、`setup.py`、`make`、被改写的本地动作）。
5. **实际权限与秘密**：工作流/job 的 `permissions:` 声明；未声明时仓库默认权限模式（read-only 还是 read-write，未知即待确认）；job 是否真的引用 `secrets.*`、是否有 environment 保护与审批；可复用工作流的权限传递。
6. **影响**：拿到什么（token 范围、秘密、仓库写、发布、部署、OIDC 云角色）。

## pull_request_target 的校准

`pull_request_target` 在**基仓上下文**运行，是不可信输入可能接触基仓权限与秘密的风险上下文；但它本身不是漏洞，也不证明写 token 或秘密存在：

- 没有 checkout fork 代码、没有执行 PR 内容时（如只读元数据打标签），不构成 pwn request。
- 有 fork checkout 与执行时，风险成立；是否 Critical 取决于第 5 步证据：job 有写权限或可达秘密才按最高档；只有只读 token 且无秘密时按实际影响降档。
- 权限、秘密、受众（仓库是否接受外部 fork PR）任一未证实，就标**待确认**并写清需要什么证据（如仓库默认权限设置、`permissions:` 全文、secrets 引用与 environment 配置），不要因为事件名直接给 Critical。
- 危险形态：`pull_request_target`（或 `workflow_run` 等基仓上下文触发）+ fork 代码 checkout + 执行。

## 表达式注入

`${{ }}` 出现在 `run:` 里，且值由外部攻击者控制时（PR 标题/正文/分支名/文件名、issue 或评论正文等），Actions 运行时会先做替换，shell 元字符随之执行。`run:` 之外，被下游解释器消费的值（动作 `script:`、被拼进 shell/命令行的参数）同理要追踪。

- `if:` 由 Actions 运行时求值，不直接把值交给 shell；但它按值做判断，条件语义仍可能被攻击者影响（如依据 PR 标题匹配、放行或跳过校验），要按业务含义核对。
- **`with:` 不是安全上下文**：参数由动作或下游执行器消费，字段位置不决定安全性。"不自动判为注入"和"看成安全"是两回事——按谁解释这个值追踪到最终执行器：

    ```yaml
    # 仍构成注入：值被 github-script 解释为 JavaScript
    - uses: actions/github-script@v7
      with:
        script: |
          core.info('${{ github.event.pull_request.title }}')

    # 参数是否进入 shell/命令行取决于动作实现，要读 action.yml 或本地复合动作再定论
    - uses: some-org/some-action@<固定版本>
      with:
        args: ${{ github.event.issue.title }}
    ```

    本地复合动作同样要在它自己的 `action.yml` 里找消费点，例如 `run: ./scripts/comment.sh "${{ inputs.message }}"`——注入在那一端成立。
- **`env:` 中转也不是万能 sanitizer**：它只避免表达式直接拼进命令文本；shell 里仍要安全引用（`"$PR_TITLE"`），且一旦用 `eval`、`bash -c "$VAR"`、`source`、未引用展开或把值写入被当作脚本执行的文件，注入依然成立。
- 数字、SHA、仓库名等非攻击者可控值不构成注入；但若下游又把它当代码、命令或路径解释，按下游语义重估。
- 修复：不可信值不拼进命令或代码文本——shell 侧经 `env:` 传入并安全引用，`actions/github-script` 侧从 `process.env` 读取而不是拼进 `script:` 字符串。

## 供应链与固定版本

- 只对**第三方**动作/可复用工作流提固定到完整 SHA 的要求；第一方 `actions/*`、`github/*` 的版本标签和本地 `./.github/actions` 不作为 pin 问题（本地动作按上面的信任链看）。
- 只在 job 有秘密、OIDC、写 token、发布、部署、签名等权力时才报未固定引用；无特权的只读 CI 不报。
- **固定 SHA 不是唯一安全证明**：被固定的动作仍可能在运行时下载可变外部脚本（`curl | bash`），或在源码里有问题；此时按行为报告。
- 没有证据不要臆造"已知漏洞版本"或具体 CVE；版本可变是风险依据，结论要落在数据流与权限上。

## 秘密与产物

- 派生值（base64、截断、变换后的秘密）不会被日志掩码覆盖；写进文件的秘密可能随 artifact 或 cache 离开运行。
- 秘密应限定在需要的 job/environment；OIDC `sub` 通配（如 `repo:org/repo:*`）允许任意分支/PR 承担云角色。
- 默认只报外部攻击者可利用的问题；任务把威胁模型扩展为内部人员、自托管或部署供应链时，按扩展后的假设核对，不要为写权限者力所能及且不涉供应链的操作凑数。

## 不自动判漏洞的形态（仍需核对）

下表是"不要仅凭这个形态就报"和"也不要当成安全保证"：每行右侧是仍要核对什么。

| 形态 | 为什么不能自动判为漏洞 | 仍需核对 |
|---|---|---|
| `pull_request_target` 不 checkout fork 代码 | pwn-request 形态不成立 | 元数据是否进 `run:`/`script:`，`permissions:` 实际范围与 job 引用的 secrets |
| 数字类表达式（PR number、run id、SHA）进 `run:` | 值本身不可控 | 是否被拼进其他解释器，或用作路径/命令参数 |
| `if:` 条件 | Actions 运行时求值，不直接进 shell | 条件语义能否被攻击者影响（放行、跳过校验） |
| `with:` 参数 | 只是把值交给动作 | 动作/下游执行器怎么消费（JS、shell、命令行） |
| 第一方 `actions/*`、`github/*` 用版本标签 | 不在第三方固定策略内，不作为 pin 发现 | 动作行为，以及所在 job 的权限与秘密 |
| 第三方动作已固定完整 SHA | 引用不可变 | 动作代码本身与运行时下载的脚本（`curl \| bash`）；固定不构成安全保证 |
| `pull_request`（非 `_target`）触发 | 来自 fork 的 PR 在只读 token 上下文运行 | 自托管 runner、cache/artifact 污染、同仓分支的正常权限；按运行环境与影响看，不预设安全 |
| `workflow_dispatch`/`schedule`/受保护分支 `push` 的表达式 | 默认外部威胁模型下需要写权限 | 任务扩展为内部人员/自托管/部署供应链时按新模型重估 |

## 验证与报告

报告前读完整 YAML（不只看 grep 结果），确认触发器与 `if:` 门控、表达式确实进入被解释的位置（`run:`、动作 `script:`、往 shell/命令行拼接参数的实现），值确实由攻击者控制，已有缓解（env 中转、author_association 检查、权限限制、SHA 固定）。任何一环不成立：降为待确认或撤下；没有发现就写零发现，不凑数。

- 每条 HIGH 发现给出五要素：入口、载荷、执行机制、影响、PoC 概要。构造不全的按待确认（中置信度）。
- 载荷与 PoC 示例用假 canary（如 `CANARY-NOT-REAL`）表达，不回显真实 secret；不鼓励为演示输出真实值。
- 输出分开列**严重程度**与**置信度**；待确认条目写清缺哪一步证据。
- 报告结构：发现（工作流:行号、触发器、置信度、利用场景、影响、修复）、待确认、已审阅并排除的工作流。
