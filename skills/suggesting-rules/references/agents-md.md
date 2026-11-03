# 写好项目指令文件（AGENTS.md / CLAUDE.md / Cursor 规则）

改编自 getsentry/skills 的 `agents-md`（固定版本 0c464f411bdfb8d4c12314b36264d06cb2f60270，Apache-2.0，Copyright 2025 Functional Software, Inc. dba Sentry；完整许可见 `../LICENSES/Apache-2.0.txt`）。本仓中文改写，加入 Windows 与多宿主落点说明。

目标：短、可执行、每条都能防止一个真实错误。根文件建议 60 行以内，最多约 100 行。

## 写之前先查

- 包管理与命令：锁文件、`pyproject.toml`、`package.json`、`Makefile`、CI workflow 里真正在跑的命令。
- 已有文档：`README`、`CONTRIBUTING`、`docs/`、`SECURITY.md`、`.github/`；引用它们，不复制。
- 约定：现有代码模式、测试布局、生成文件、不要碰的遗留目录、公开仓库禁止提交的内容。
- 已有指令文件：先读完再改，更新已有条目而不是追加重复条目。

## 范围

- 根目录一份写全仓默认；子目录只有命令或规则确实不同时才加，且比根文件更短、不重复根文件。
- 多个宿主要读同一份时，保持单一事实来源：其余文件只写“见 AGENTS.md”或按宿主支持的方式引用。Windows 上符号链接常需要开发者模式或管理员权限，不要默认依赖符号链接。
- 不维护内容分叉的 `AGENTS.md` 与 `CLAUDE.md` 副本。

## 推荐结构（只保留有非显而易见价值的节）

```markdown
# Agent Instructions

## Commands
| 任务 | 命令 |
|---|---|
| 单个测试 | `uv run pytest tests/test_x.py -q` |
| 全部检查 | `python scripts/check.py` |

## References
| 需要 | 文件 |
|---|---|
| 架构 | `docs/architecture.md` |
| 发布流程 | `docs/releasing.md` |

## Rules
- 生成文件用 `python scripts/gen.py` 更新，不手改。
- 不向公开仓库提交 `docs/internal/**`。
```

## 写法

- 标题、列表、表格；少写段落，一条一个规则。
- 用仓库相对路径和能直接运行的命令；优先单文件级的测试/检查命令，没有时才给全量命令。
- 理由只在能防止常见错误时写一句。
- 不复述 linter/格式化配置，不列已安装的技能或插件，不写“保持代码整洁”这类口号、欢迎语和结语。

## 写完核对

- 每个路径和命令都存在且能运行（实际跑一次或至少 `--help`）。
- 没有与 README/CONTRIBUTING 重复的大段内容。
- 没有密钥、内部账号、本机绝对路径或真实用量数字。
