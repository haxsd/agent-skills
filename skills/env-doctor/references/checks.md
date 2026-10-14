# env-doctor 检查清单

按需查阅。每条检查写清"看什么、缺什么、不能据此推断什么"。本清单是**线索集**，不是必须全做；
只执行与本次故障相关的部分，并记录未做的部分。

## 1. 宿主 / 容器 / WSL / monorepo 定位

- 运行位置：宿主？WSL 发行版？容器内？远程？同一台机器上三者的进程、端口与环境变量互不相通。
- monorepo：先确认属于哪个包（`workspaces`、`pnpm-workspace.yaml`、`lerna.json`、`nx.json`、`turbo.json`、
  各自 `package.json`），再决定在根目录还是子目录检查。子包缺 `node_modules` 可能是被提升到了根目录。
- 容器内诊断：用 `docker compose exec <svc> ...`（需要授权）；宿主命令看不到容器内的监听端口与环境变量。
- 不要用宿主的 `Get-NetTCPConnection`/`lsof` 结果去解释容器内应用，也不要把 WSL 内进程当宿主进程。

## 2. 启动入口

- 找实际入口：`package.json` 的 `scripts.dev`/`start`、`docker-compose.yml`/`compose.yaml` 的 `command`/`entrypoint`、
  `Makefile` 目标、`Procfile`、`.vscode/launch.json`、`mise.toml` 的 `tasks`、README 的运行说明。
- 注意脚本可能再委托：`dev` → `vite`/`next dev`/`nodemon`，`start` → `node dist/main.js`；配置里的端口信息以最终
  消费处为准（如 `vite.config.*` 的 `server.port`、`--port` 参数、`.env` 的 `PORT` 键名）。
- 用户已给出启动命令时优先沿用，不按框架常识改写。

## 3. Node 系：声明、锁文件、workspace、PnP

- 声明：`package.json` 的 `packageManager`、`engines.node`、`volta`；根目录 `mise.toml`/`.tool-versions`/`.nvmrc`。
- 锁文件 → 包管理器：
  - `package-lock.json` / `npm-shrinkwrap.json` → npm
  - `pnpm-lock.yaml` → pnpm；`pnpm-workspace.yaml` 说明 workspace 结构
  - `yarn.lock` → yarn（`.yarnrc.yml` 里 `nodeLinker: pnp` 即 PnP；有 `.pnp.cjs` 同理）
  - `bun.lockb` / `bun.lock` → bun
- 冲突处理：`packageManager` 与锁文件不一致时，**不要无依据选一边**。找证据判定：CI 配置（`.github/workflows`、
  `Jenkinsfile`）、README/贡献指南、仓库历史、实际执行入口（`Makefile`、compose `command`、mise tasks）。证据仍不足时
  按未知报告，不安装、不生成/改任何锁文件。
- PnP：没有 `node_modules` 是预期状态；依赖 bug 应看 `.pnp.cjs` 是否存在、是否是 PnP 未被工具识别。
- workspace：根 `node_modules` 存在即可支撑子包；子包目录没有 `node_modules` 不能报"依赖缺失"。
- 缺依赖的判断证据：安装报错、`Cannot find module`、锁文件与 `node_modules` 明显脱节。缺目录本身不是证据。

## 4. Python 系：管理器与环境

- 管理器线索：`uv.lock` → uv；`poetry.lock` + `[tool.poetry]` → poetry；`Pipfile.lock` → pipenv；只有
  `requirements.txt` 时需再确认谁在执行安装。
- 版本声明：`requires-python`、`.python-version`、`mise.toml`；与工具地图解析到的解释器版本分开记录。
- `.venv/`、`venv/`、`env/` 都没有时，先确认：解释器是系统 Python？容器内？conda？还是被 PDM/Hatch 放在别处。
- 依赖缺失的证据：导入报错（`ModuleNotFoundError`）、`pip check`/`uv pip check` 结果；不用目录存在性推断。

## 5. 工具地图（toolkit-map）解析

- 调用任何本机工具前：`map.ps1 status -Json` 确认地图可用且不 stale；`map.ps1 find <工具> -Project <工作区> -Json`
  取 `path`。只有 `ok: true` 且 `verification: verified` 的结果才能直接执行。
- `find` 的真实状态（schemaVersion 2）与口径：
  - `ok` + `verification: verified`：可直接采用返回的 `path`。
  - `version_mismatch`：确认没有满足项目要求的候选（有已核验副本但版本不符）。报告"要求未满足"；不降级、不换版本、不安装。
  - `no_usable_candidate`：有候选但无通过验证的可用副本。属于**证据缺口**，标未知；不要写成"要求确证未满足"。
  - `not_found`：本次搜索范围内没有候选。不代表全盘不存在，标未知并继续现场发现。
  - `requirement_unsupported`：项目声明语法地图不支持（如无法判定的版本范围）。报告限制；用支持的显式 `-Version`
    或交由管理器执行，不猜一个版本替代。
  - 验证失败、`verification` 为空或候选 `usable: null`：一律按未知处理，不当作满足也不当作失败。
- 机器上的其他候选副本 ≠ 项目要求被满足；PATH 解析 ≠ 机器盘点。
- 地图缺失或跑不起来：按常规做法完成诊断，明确标注发现层缺失并提醒用户安装 toolkit-map。

## 6. 端口与进程

- 证据优先级：应用报错信息 > 实际启动配置 > 框架默认值。不要把 3000/8080 之类常用端口当固定清单逐个体检。
- 宿主检查：

```powershell
Get-NetTCPConnection -LocalPort 18080 -ErrorAction SilentlyContinue |
  Select-Object LocalAddress,LocalPort,State,OwningProcess
Get-Process -Id <PID> | Select-Object Id,ProcessName,Path
```

（macOS/Linux 用 `lsof -nP -iTCP:18080 -sTCP:LISTEN`，再用 `ps -p <PID> -o pid=,ppid=,user=,comm=`。）
注意：带完整命令行的 `ps` 输出可能包含密钥参数，只取判断归属所需的最小字段。

- 容器：`docker compose ps`（服务与端口映射）优先；`docker port <container>` 也只看端口映射。
  `18080:8080` 只说明宿主 18080 → 容器 8080 的转发，容器内应用监听什么要看它自己的配置。
- 停止权限：报出 PID + 进程/服务归属证据后，**明确请求**对该目标的停止授权；`-Force`/`kill -9`/批量杀进程
  需要用户在普通停止失败后另行授权。容器场景用 `docker compose stop <svc>` 而不是 `docker kill`。

## 7. 环境变量：来源与键状态

来源顺序（能观测到什么就写什么）：

1. 进程/服务管理器注入（systemd、pm2、Windows 服务、容器 `environment`/`secrets`、k8s）——通常需要授权才能观测。
2. CI 变量与仓库 secret 配置——报告"由 CI 注入，本地不可见"。
3. `docker compose` 的 `env_file` 指向的文件——只看键名状态，不读值。
4. 本地 `.env` 类文件——**AI 不读原文**；用户明确指定的文件交给下面的脚本在程序内读取。

键状态脚本（标准库、只读、只回键名与状态）：

```powershell
& '<toolkit-map 给的 python 绝对路径>' '<技能目录>\scripts\env_key_status.py' `
  --env '<用户明确指定的环境文件>' --example '<example 文件>'
```

- 只接受用户明确指定的路径，程序内部读取，stdout 只有键名、状态（present/empty/missing/unknown）与 gap；
  exit 0=ok，1=refused/incomplete，2=参数错误。
- **不跟随链接**：路径本身或任一级父目录是符号链接或 Windows reparse point（含 junction）时保守拒绝。
- 路径检查和打开不是原子操作，不保护并发文件系统替换；这不是 OS 沙箱，应在稳定、授权的文件上使用。
- 明确缺口：插值、续行、引号内多行、转义序列、引号值后的额外文本（含注释）都不求值，相关键标 unknown 并列 gap；出现缺口后**停止解析后续行**，
  避免把多行值的内部行误当成键；env 有缺口时 example 中未见到的键标 unknown，而不是确认 missing。
- 文件级拒绝：超过 1 MiB、非普通文件（目录/FIFO/设备）、无法按 UTF-8/UTF-16 解码或解码后含 NUL 的内容，给静态 gap，不输出异常原文。
- 该脚本只说明“文件里有什么”，不证明运行时注入；进程环境是否真的有这些键仍是未知，除非另行授权观测。

无法观测某个来源时写"未知"，不写"缺失"。`.env.example` 只作线索：其中的键可能带默认值、可能过时；
未列入的键也可能由部署环境注入。

## 8. 服务依赖、权限与文件系统

- 服务依赖线索：`DATABASE_URL`/`REDIS_URL` 等键是否被引用、依赖包（`pg`、`psycopg`、`redis`、`mysql2`）、
  compose 服务名。先非破坏性检查（端口是否在监听、`docker compose ps`），再决定是否建议启动。
- 权限：项目目录是否可写（安装/构建需要）；Unix 脚本是否有可执行位（`test -x`）；不未授权 `chmod`。
- 文件系统：磁盘空间、inode、大小写敏感路径差异（容器 Linux 与宿主 Windows）、挂载是否只读。
- 网络：代理/证书配置、hosts 解析、VPN 对依赖下载的影响；只观测与本次故障相关的部分。

## 9. 不要做（反模式）

- 无 `node_modules`/`.venv` 就建议安装依赖；用 `npx`/`corepack`/`pipx` 顺带获取工具。
- 按固定端口清单体检；把映射端口当应用端口；未确认归属就停止进程。
- 用 `Read`/`cat`/`Get-Content` 把 `.env` 原文带进上下文；`docker compose config`、`docker inspect`、带 argv 的
  `ps` 直接粘进报告。
- 把 `.env.example` 当完整 required 清单；把键存在当已注入进程；解析有缺口仍报"确认 missing"。
- `packageManager` 与锁文件冲突时无依据选一边、顺手改锁文件或直接安装。
- 地图报 `version_mismatch`/`no_usable_candidate`/`not_found`/`requirement_unsupported` 时另挑一个版本或自动安装；
  把证据缺口写成"要求已确证未满足"。
- 越权修复：装依赖、重启服务、改 PATH、改全局配置——需要单独授权。
