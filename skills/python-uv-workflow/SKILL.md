---
name: python-uv-workflow
description: 用 uv 搭建、运行和迁移 Python 项目与单文件脚本：PEP 723 内联依赖、pyproject 依赖组、锁文件、uv run 代替手动激活虚拟环境、ruff 检查与格式化、pytest，以及 Windows 上的路径、编码和解释器选择。Use when creating a Python project or script with dependencies, adding/removing deps, setting up lint/test/CI for Python, or migrating from requirements.txt/pip/Poetry/black/flake8. 已有项目明确使用其他工具链时沿用它；诊断“装了却找不到”之类环境问题用 env-doctor。
---

# Python + uv 工作流

先看项目已有什么：有 `uv.lock` 就用 uv；有 `poetry.lock`、`Pipfile`、`requirements*.txt` 或 conda 环境且用户没要求迁移，就沿用原工具，只借用下面不冲突的做法。只用标准库的脚本不需要任何项目文件。

## 选路线

| 情况 | 做法 |
|---|---|
| 单文件脚本，带第三方依赖 | PEP 723 内联元数据：`uv add --script tool.py requests`，`uv run tool.py` |
| 一次性试用某个包 | `uv run --with httpx python -c "..."`，不写进项目 |
| 运行命令行工具 | `uvx ruff check .`（临时环境），项目内工具用 `uv run ruff` |
| 新的多文件应用 | `uv init` → `uv add <包>` → `uv run ...` |
| 要发布的库 | `uv init --package`（src 布局）→ `uv build` |
| 已有项目迁移 | 见下方“迁移” |

## 基本规则

- 依赖用 `uv add` / `uv remove` 改，不手改 `pyproject.toml` 的依赖列表，也不用 `uv pip install` 往项目环境里塞包。
- 开发工具放 `[dependency-groups]`（`uv add --group dev pytest ruff`），不放 `[project.optional-dependencies]`；后者留给用户可选功能。
- 命令一律 `uv run <cmd>`，不手动 `activate`；它会先按锁文件同步环境。
- `uv.lock` 提交进版本库；CI 用 `uv sync --locked`（锁文件过期就失败），`uv lock --check` 可单独检查。
- 用 `.python-version`（`uv python pin 3.12`）和 `requires-python` 固定解释器范围；不要依赖系统 PATH 上碰巧是哪个 Python。
- 改完依赖跑一次 `uv run pytest` 或项目自己的检查命令，再报告完成。

## 检查与测试

- ruff 同时做 lint 和格式化：`uv run ruff check --fix .`、`uv run ruff format .`；CI 用 `ruff format --check` 和 `ruff check`。
- 规则集从项目现有配置出发；新项目可先用默认规则再逐步加，不要一上来全开再大面积忽略。
- 测试用 pytest；项目已有 `unittest` 就继续用，`uv run python -m unittest` 即可。
- 类型检查沿用项目已有的 mypy/pyright；ty 目前仍是 Beta（0.0.x），只在用户愿意时试用，不替换已在 CI 中的检查器。

## Windows 注意

- 虚拟环境的可执行文件在 `.venv\Scripts\`，不是 `bin/`；用 `uv run` 就不必关心。
- 控制台和管道编码：脚本读写文件时显式 `encoding="utf-8"`；子进程输出用 `encoding="utf-8", errors="replace"` 解码；必要时设 `PYTHONUTF8=1`。
- 不用 `py`/`python` 猜版本：`uv run` 用项目固定的解释器；临时指定用 `uv run --python 3.12 ...`。
- PowerShell 里调用 uv 的引号、参数和退出码规则见 windows-powershell-safe。
- 路径用 `pathlib`，不要手拼 `\` 或 `/`。

## 迁移

只在用户要求时做，一次只换一样，换完跑测试：

1. **requirements.txt → pyproject**：`uv init --bare`，逐个 `uv add`（复杂版本约束人工核对；`-r`、`-e`、索引地址单独处理），`uv sync`，测试通过后再删旧文件。
2. **setup.py / setup.cfg**：元数据搬进 `[project]`，依赖用 `uv add`，开发依赖进依赖组。
3. **Poetry**：依赖与组逐项迁到 `[project]` 与 `[dependency-groups]`，保留原版本约束，迁移后对比 `uv tree` 与旧锁文件里的关键版本。
4. **black / isort / flake8 → ruff**：先加 ruff 并配置等价规则，确认 `ruff format` 的 diff 只是格式，再移除旧工具和配置。

## 完成前核对

- `uv lock --check` 通过；`uv run` 下测试与检查通过。
- 新增依赖都有用途；没有把开发工具放进运行时依赖。
- README 或 AGENTS.md 里的安装/运行命令已同步更新。

<!-- provenance:start -->
> 创作归属：原创改进（基于上游）。来源、署名与许可见 [来源说明](../../ATTRIBUTION.md#python-uv-workflow)。
<!-- provenance:end -->
