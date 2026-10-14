---
name: env-doctor
description: 应用起不来、启动报错、依赖或运行环境可疑时，先只读诊断本机环境再改代码。覆盖宿主/容器/WSL 与 monorepo 目录定位、包管理器与锁文件、toolkit-map 工具解析、真实端口与进程归属、环境变量来源与键状态、服务依赖与文件权限。Use when 用户说“为什么跑不起来”“帮我看看环境”“检查一下环境”“it works on my machine”，或遇到依赖缺失、运行时版本、端口冲突、.env 变量、权限与后台服务等问题。
license: MIT; 仅覆盖本轮原创内容, 见 LICENSE.txt
---

# env-doctor

在改应用代码之前，先只读诊断本机环境。默认假设**环境里还有没排除的变量**，而不是应用有问题。

## 边界与分工

- 只诊断、只报告。安装依赖、启动服务、迁移、杀进程都不在诊断范围内，各自需要明确授权。
- **AI 不读取环境文件原文**；用户明确授权的文件由只读脚本在程序内读取、只回键名与状态，完整容器配置、inspect、带密钥的进程命令行同样不整段读入。
- 本次运行命令前，按 `toolkit-map` 的流程确认要用的解释器/运行时解析到绝对路径。
- 代码本身的缺陷排查用 `systematic-debugging`；只看一份变更用 `code-review`；找本机工具用 `toolkit-map`。

## 工作流

### 1. 先确定“在哪里跑、怎么启动”

- 判定运行位置：宿主、WSL 发行版、容器内，还是远程；目录是 monorepo 的哪个包。混用宿主命令查容器内进程会得出错误结论。
- 找到**实际启动命令与配置**：`package.json` 的 `dev`/`start`、`docker compose` 服务、`Makefile`、Procfile、`.vscode/launch.json` 等。用户已说明的入口优先，不要猜。
- 需要细化宿主识别与启动入口检查时读 [references/checks.md](references/checks.md)。

### 2. 运行时与包管理器：先读项目声明，再谈本机

分三层记录，不要混成一句“本机只有 X”：

| 层次 | 依据 |
|---|---|
| 声明 | `packageManager`、`engines`、`engines.node`、`requires-python`、`mise.toml`/`.tool-versions`/`.nvmrc`、锁文件 |
| 可用 | toolkit-map 给出的本机候选清单 |
| 解析 | 当前命令实际解析到的绝对路径与版本 |

- Node 系：`packageManager` + 锁文件（`package-lock.json` → npm，`pnpm-lock.yaml` → pnpm，`yarn.lock` → yarn，`bun.lockb` → bun）。两者冲突时不要无依据选边：查 CI 配置、README/贡献指南、仓库历史、实际执行入口；证据不足按未知报告，不安装、不改锁文件。
- Yarn PnP（`.pnp.cjs`/`.pnp.js`）下没有 `node_modules` 是正常状态；`workspaces`/`pnpm-workspace.yaml` 子包也可能没有自己的 `node_modules`。缺目录不能推断“要装依赖”。
- Python 系：识别 uv / poetry / pipenv / 系统环境（`uv.lock`、`poetry.lock`、`Pipfile.lock`、`requires-python`、`.python-version`）。无 `.venv/` 不代表环境缺失，需要确认解释器与依赖来源。
- 不凭 `node_modules`/`.venv` 缺失建议安装；不在未经授权时运行 `npm install`、`pip install`；不用 `npx`/`corepack`/`pipx` 自动获取工具。

### 3. 用工具地图解析要执行的命令

- 调用本机命令前查地图，拿到 `verification: verified` 的绝对路径再执行；只用地图返回的 `path`，不通过 PATH 猜测。
- 地图 `find` 的真实状态（schemaVersion 2）：
  - `version_mismatch`：确认没有满足项目要求的候选。报告"要求未满足"，不降级、不自动更换版本、不自动安装。
  - `no_usable_candidate`：有候选但没有通过验证的可用副本。这是**证据缺口**，不能写成"要求确证未满足"，标注未知。
  - `not_found`：本次搜索范围内没有候选；不代表全盘不存在，标注未知并按现场发现流程继续。
  - `requirement_unsupported`：项目声明用了地图不支持的语法；报告限制，用显式 `-Version` 或由管理器执行，不猜版本。
  - `ok: true` 且 `verification: verified` 才可直接采用返回的 `path`；验证失败或未知都按未知处理。
- 机器上有其他候选副本，不等于项目要求被满足。
- 地图不可用时如实说明发现层缺失，再按常规路径处理，并提醒用户地图缺失。

### 4. 端口与进程

- 端口以**报错信息与实际启动配置**为准：报错说 18080 被占用就查 18080；不给固定常用端口清单。
- 区分宿主 published 端口与容器内 listening 端口。看到 `18080:8080` 只能说明映射关系，不能断定应用必须监听 8080。
- 发现占用后先确认 PID、可执行文件/服务名与归属证据；归属未确认前不停止任何进程。
- 普通停止（`kill <PID>`、`Stop-Process -Id <PID>`、`docker compose stop <svc>`）需要用户对该 PID/服务的明确授权；`kill -9`/`-Force` 只能在普通停止失败后**另行**授权。不按进程名批量杀。

### 5. 环境变量：来源、状态、缺口

变量可能来自进程环境、CI、`docker compose`（`environment`/`env_file`/`secrets`）、secret store。本地无 `.env` 或变量为空，不能直接判定实际环境缺失该变量。

- 只输出**键名 + 状态**（present / empty / missing / unknown），绝不输出值、整行内容或命令回显原文。
- **AI 不读取环境文件原文**（不用 `Read`/`cat`/`Get-Content`/`grep` 读 `.env` 内容）；用户明确指定的文件由 [scripts/env_key_status.py](scripts/env_key_status.py) 在程序内读取，只把键名与状态回给模型——这种隔离正是为了不让值进入上下文。
- 禁止 `docker compose config`、`docker inspect` 全量输出、`ps` 带敏感命令行等可能带出密钥的读法。
- `.env.example` 是线索而不是完整 required 清单：其中出现 ≠ 运行必填，未出现 ≠ 不需要。
- 键存在 ≠ 已注入进程。键状态脚本只说明文件里有什么；进程实际取值标为未知，除非另有授权观测。
- 需要键状态时用该脚本（只读、只报状态）；解析不完整时相关键标 unknown，见 checks.md。

### 6. 权限、服务与常见环境点

- 确认项目目录可写、脚本有执行位（Unix）；不要未授权就 `chmod`。
- Postgres / Redis / MySQL 等依赖：先做非破坏性状态检查（是否在监听、compose 服务状态），再报告，不自动启动或清理。
- 磁盘空间、只读文件系统、dll/共享库缺失、系统代理与证书等常见点按需检查。

## 输出结构

按影响排序，每条给出证据与缺口：

````markdown
**Env Doctor Findings**

1. [High] <问题>
   Evidence: `<命令、配置或文件引用的最小证据>`
   Fix:
   ```powershell
   <与当前宿主匹配的命令>
   ```

**声明 / 可用 / 解析**：`<三层结果各一句>`
**环境变量**：`<键名 + 状态列表；unknown 与未观测部分明确标注>`
**未验证**：`<没做的事与原因，例如未启动容器、未观测进程环境>`
````

没有任何问题时，说明环境侧未发现阻断，再给出下一步应用层排查建议（转 `systematic-debugging` 或读日志），不硬凑结论。

## 参考加载

- [references/checks.md](references/checks.md)：宿主识别、启动入口、包管理器/PnP/workspace 判定、端口与进程、环境变量来源、服务与权限检查清单。
- [references/safety-fixtures.md](references/safety-fixtures.md)：修改本技能行为前必须通过的安全与对抗案例。
- [EVAL.md](EVAL.md) 与 [evals/cases.json](evals/cases.json)：行为评估方法与案例。

<!-- provenance:start -->
> 创作归属：原创改进（基于上游）。来源、署名与许可见 [来源说明](../../ATTRIBUTION.md#env-doctor)。
<!-- provenance:end -->
