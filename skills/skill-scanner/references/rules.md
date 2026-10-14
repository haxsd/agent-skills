# 规则清单

`scan_skill.py` 的所有规则都是**静态模式匹配**，只产出"待复核"条目。下表说明每条看什么、
为什么不能直接当结论、以及最常见的误报来源。命中的行如果落在 Markdown 代码块内（`context` 为
`markdown-code-block`），或上下行有"示例/不要运行"一类措辞（`context` 为 `documentation-example`），
只降一档置信度，条目不删除。

## 提示词注入与隐瞒

| ruleId | 默认置信度 | 检测什么 | 为什么只算待复核 |
|---|---|---|---|
| `instruction-override` | high | 要求读者忽略/忘记/覆盖"之前的指令、规则、提示词"（中英文） | 安全文档、审查清单会引用这类话术做反例 |
| `instruction-concealment` | medium | 要求"不要告诉用户/对用户隐瞒" | 测试或演练文案可能这么写 |
| `instruction-extraction` | medium | 要求输出/泄露系统提示词、隐藏指令 | 常见于讨论提示词安全的文档 |
| `invisible-unicode` | medium | 行内出现零宽或双向控制字符 | 某些复制粘贴的文本会带进来；不含 emoji 用的 ZWJ |

## 凭据与数据外发

| ruleId | 默认置信度 | 检测什么 | 为什么只算待复核 |
|---|---|---|---|
| `credential-private-key` | high | 引用 SSH 私钥（`.ssh/id_rsa` 等）或 `id_ed25519` 一类名字 | 密钥轮换、备份类脚本的正常操作 |
| `credential-store` | medium | 引用 `.aws/credentials`、`.netrc`、`.git-credentials`、Docker/Kube 配置、浏览器登录数据、钥匙串查询命令 | 有些工具确实要读云凭据 |
| `env-secret-read` | medium | 同一行既有环境变量读取，又有 TOKEN/SECRET/PASSWORD 一类名字 | CI 脚本里很常见；看它把值发去哪里 |
| `exfiltration-combined` | medium | 同一行既有凭据来源，又有带请求体的网络发送 | 正常的 API 上传也可能长这样 |

## 全局 agent 配置写入

| ruleId | 默认置信度 | 检测什么 | 为什么只算待复核 |
|---|---|---|---|
| `global-agent-config-write` | medium | 同一行既有 `.claude/`、`.cursor/`、`.codex/`、`.agents/`、`CLAUDE.md`、`AGENTS.md`、`mcp.json` 一类路径，又有写入动作 | 技能文档讲"如何安装到全局"时也会同时出现 |

判断要点：写入发生在**用户自己的项目里**通常正常；改写用户**全局** agent 配置、往别的技能目录里
塞东西，才需要重点看。

## 执行类

| ruleId | 默认置信度 | 检测什么 | 为什么只算待复核 |
|---|---|---|---|
| `download-execute` | high | 下载结果直接管道给解释器（bash/sh/python/node/iex 等）、`iex(iwr ...)`、`mshta` 加载远程脚本、`certutil` 拉取远程内容 | 安装脚本、引导脚本的常见写法；要看下载源是否为官方地址 |
| `obfuscated-execution` | high | PowerShell `-EncodedCommand`、长 base64 命令、base64 解码后交给解释器、`eval(atob(...))` 一类 | 有些封装工具确实用编码传参 |
| `unsafe-deserialization` | medium | `pickle.loads`、`marshal.loads`、`yaml.unsafe_load` | 本地可信数据的反序列化也这么写 |
| `destructive-filesystem` | medium | `rm -rf /`、`rm -rf ~`、`rm -rf *`、`rd /s /q C:\`、`Remove-Item -Recurse` 指向根/家目录、`shutil.rmtree("/")`、`dd of=/dev/...`、`mkfs` | 只在目标是根/家目录/整盘时才报；`rm -rf ./build` 不报 |

## 语言/文件特定规则

| ruleId | 适用 | 默认置信度 | 检测什么 |
|---|---|---|---|
| `python-dynamic-exec` | `.py` 等 | medium | `eval(` / `exec(`（排除 `xxx.eval(` 这类成员调用） |
| `python-subprocess-shell` | `.py` 等 | medium | `subprocess.*(..., shell=True)` |
| `python-os-command` | `.py` 等 | medium | `os.system` / `os.popen` / `os.exec*` |
| `js-child-process` | `.js/.ts` 等 | medium | 同行出现 `child_process` 与 `exec/spawn` |
| `js-dynamic-exec` | `.js/.ts` 等 | medium | `eval(` / `new Function(` |
| `ps-invoke-expression` | `.ps1` 等 | medium | `Invoke-Expression` / `iex` |
| `ps-policy-bypass` | `.ps1` 等 | low | `-ExecutionPolicy Bypass/Unrestricted` |
| `shell-eval` | `.sh` 等 | medium | `eval "$(...)"` 一类求值 |
| `package-lifecycle-script` | `package.json` | medium（脚本值含网络/执行词时升到 high） | 用 `json` 解析后在 `scripts` 下找 `preinstall/install/postinstall/prepare`；minified 单行文件同样定位，同名键不在 `scripts` 下不算，无法解析记 `invalid-json` 缺口 |
| `package-install-from-url` | 所有文本 | medium | `pip/npm/yarn/pnpm/deno/npx` 直接从 URL 或 `git+` 安装 |

## 动态内容（frontmatter 与正文）

frontmatter 部分只对 Markdown（含 `.mdc`）和 `SKILL.md` 生效，按行解析，不引入 YAML 依赖；
正文里的 `!`command`` 用同一套模式匹配，因此代码块里的示例同样会被报出（只降置信度）。

| ruleId | 默认置信度 | 检测什么 |
|---|---|---|
| `frontmatter-hook-field` | medium | 键为 `hooks/hook/on_load/on_start/on_install`，或顶层直接写钩子事件名（`PreToolUse`、`PostToolUse`、`Notification`、`SubagentStop`、`UserPromptSubmit`、`PreCompact`、`SessionStart`、`SessionEnd`）且值非空 |
| `frontmatter-command-field` | medium | 键为 `command/commands/exec/run/script` 等且值非空 |
| `frontmatter-dynamic-command` | medium | frontmatter 里出现 `!` 加反引号的动态命令写法 |
| `dynamic-command` | medium | Markdown 正文（含代码块示例）里出现 `!` 加反引号的动态命令写法 |

## 覆盖缺口（`coverage.gaps[].reason`）

| reason | 含义 | 怎么处理 |
|---|---|---|
| `binary` | 含 NUL 或无法按文本解码（含"能按 UTF-8 解码但带 NUL"的伪文本） | 人工确认二进制来源；必要时抬 `--max-file-bytes` |
| `unknown-format` | 非 UTF-8 但像文本（如本地编码） | 转成 UTF-8 后重扫 |
| `oversize` | 超过 `--max-file-bytes` | 抬高上限重扫，或人工看 |
| `unreadable` | 打不开（权限等） | 修权限后重扫 |
| `invalid-json` | `package.json` 无法解析（语法错误或嵌套过深） | 修正或人工读该文件；此时 lifecycle 视图不完整 |
| `internal-link` | 内部 symlink/junction、其他 Windows reparse point，或链接检查时 stat 失败 | 扫描器保守跳过；人工核对链接目标、OneDrive 等云占位状态或读取权限 |
| `special-file` | FIFO、设备等 | 一般与技能无关，人工确认 |
| `file-limit` | 文件数超过 `--max-files`（`path` 为第一个未检查的文件） | 抬高上限重扫；注意此时未必扫到全部文件 |
| `entry-limit` | 目录枚举条目数超过 `--max-entries`（`path` 为超限的那个目录，该目录整体不读） | 抬高 `--max-entries` 重扫 |

根目录本身枚举超限时不是缺口而是拒绝：`refusal: root-entry-limit`。

## 上下文与置信度

- `context: "markdown-code-block"`：该行在 fenced 代码块内，置信度降一档。
- `context: "documentation-example"`：匹配行上下各一行内出现 `example/fixture/示例/不要运行`
  一类措辞（URL 里的 `example` 不算），置信度降一档。
- 两者都只降一档、不删条目：任何发现都必须回到原文件那一行人工判断。
- `package.json` 的发现由解析后的 JSON 语义得出，不套用示例措辞降档；它的置信度只由脚本内容
  （是否含网络/执行词）决定。
