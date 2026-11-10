# 共用 Office 资源

xlsx、docx、pptx 三个技能共用这里的 OOXML XSD 和 Python 实现，避免各拷贝一份。

- `schemas/`：OOXML XSD（约 1MiB）。
- `python/office/`：校验、LibreOffice 封装、安全解包/打包等脚本的唯一实现。各技能的 `scripts/office/` 只保留薄启动器，导入时解析到这一份代码。

`install.ps1` 在全量安装，或 `-Only` 包含 `xlsx`、`docx`、`pptx`、`token-efficient-workflow` 任一，时会把仓库 `shared/` 联接到 `~/tools/shared/`（Windows 上为 `%USERPROFILE%\tools\shared`）。只安装其他技能时不会建立这个联接。

路径解析同时覆盖：仓库树内开发（从技能目录向上找到 `shared/`），以及安装后的 `~/tools/shared` 联接。也可设置：

- `AGENT_SKILLS_OFFICE_SCHEMAS` 或 `OFFICE_SCHEMAS_DIR`：XSD 目录
- `AGENT_SKILLS_OFFICE_PYTHON`：`shared/office/python` 或其中的 `office` 包目录

校验脚本按以下顺序查找 schema：上述环境变量，技能内遗留的 `scripts/office/schemas/`，与实现文件相邻的 `shared/office/schemas/`，仓库 `shared/office/schemas/`，以及 `~/tools/shared/office/schemas/`。

许可见 LICENSE.txt 与 NOTICE.txt。
