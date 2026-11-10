# 共用 Office OOXML schema

xlsx、docx、pptx 三个技能共用这里的 XSD，避免各拷贝一份（约 1MiB）。
安装器会把仓库 `shared/` 联接到 `~/tools/shared/`。
校验脚本按以下顺序查找：`AGENT_SKILLS_OFFICE_SCHEMAS` 或 `OFFICE_SCHEMAS_DIR`，技能内遗留的 `scripts/office/schemas/`，仓库 `shared/office/schemas/`，以及 `~/tools/shared/office/schemas/`。

许可见 LICENSE.txt 与 NOTICE.txt。
