---
name: docx
description: 创建或修改 Word 文档（.docx/.dotx）。Use when the user wants to create, edit, or extract a Word document. Do not use for PDF, Excel/spreadsheets, or PowerPoint/.pptx files.
license: Apache-2.0; see LICENSE.txt
---

# docx（Word）

## 本仓说明

本目录按仓库惯例补充了中文入口、Windows 与依赖边界，以及共用 schema 路径；创建、编辑和校验规则仍以上游正文为准。

### 何时用

用户要创建、编辑、抽取或批注 Word 文档（`.docx` / `.dotx`）时使用。PDF 用 [pdf-toolkit](../pdf-toolkit/SKILL.md)，Excel 用 [xlsx](../xlsx/SKILL.md)，真实 PowerPoint 用 [pptx](../pptx/SKILL.md)。不要把「报告/备忘录」在未指定 Word 时默认做成 .docx。

### 依赖（不要假设已预装）

先按 toolkit-map 查本机 Python、Node 与系统工具的绝对路径。缺失时如实报告，获得用户许可后再在项目环境中安装，不要全局安装，也不要假定上游环境「已预装」。

- 创建新文档：Node 包 `docx`
- 阅读现有文档：`pandoc`（例如 `pandoc -t markdown file.docx`）
- 转 PDF / 视觉抽查、遗留 `.doc` 转换：LibreOffice（`soffice` / Windows 上的 `soffice.exe`）
- 可选页图：Poppler `pdftoppm`
- 校验脚本：Python 包 `lxml`、`defusedxml`

编辑已有文档时用 `scripts/office/zipio.py` 解包 XML 再打包（Windows 与 Unix 都可用，不要用 Expand-Archive）；docx-js 打不开已有文件。

### 共用 schema 与脚本

OOXML XSD 与 Python 实现已抽到仓库 [`shared/office/`](../../shared/office/README.md)；本技能的 `scripts/office/` 只留启动器。`install.ps1` 在全量安装，或 `-Only` 包含 `xlsx`、`docx`、`pptx`、`token-efficient-workflow` 任一，时会把 `shared/` 联接到 `~/tools/shared/`（Windows 上为 `%USERPROFILE%\tools\shared`）；只安装其他技能时不会联接。用绝对路径调用 `scripts/office/validate.py`、`scripts/office/zipio.py`、`scripts/merge_runs.py`、`scripts/accept_changes.py` 和 `scripts/comment.py`。

# DOCX creation, editing, and analysis

A `.docx` is a ZIP archive of XML files. Choose your approach by task:

| Task | Approach |
|---|---|
| **Create** a new document | Write a `docx` (npm) script — see gotchas below |
| **Edit** an existing document | `zipio.py unpack` → edit `word/document.xml` → `zipio.py pack` (docx-js cannot open existing files) |
| **Read** content | `pandoc -t markdown file.docx` |

> Script paths below are relative to this skill's directory.

## Creating with docx-js — gotchas

Do not assume the Node `docx` package is preinstalled. `require('docx')` only after confirming it is available; if it fails, report the missing package and run `npm install docx` only with the user's permission, in the project environment, not globally. The model knows the API; these are the footguns:

- **Page size defaults to A4.** For US Letter set `page: { size: { width: 12240, height: 15840 } }` (DXA; 1440 = 1″).
- **Landscape:** pass portrait dimensions and `orientation: PageOrientation.LANDSCAPE` — docx-js swaps width/height internally.
- **Tables need dual widths:** set `columnWidths` on the table AND `width` on every cell, both in `WidthType.DXA` (PERCENTAGE breaks in Google Docs). Column widths must sum to the table width.
- **Table shading:** use `ShadingType.CLEAR`, never `SOLID` (renders black).
- **Lists:** never insert `•` literally; use a `numbering` config with `LevelFormat.BULLET`.
- **`ImageRun` requires `type:`** (`"png"`, `"jpg"`, …).
- **`PageBreak` must be inside a `Paragraph`.**
- **Never use `\n`** — use separate `Paragraph` elements.
- **TOC:** headings must use built-in `HeadingLevel.*`; custom heading styles need `outlineLevel` set or they won't appear.
- **Don't use a table as a horizontal rule** — use a paragraph bottom border instead.
- **Dot-leader / right-aligned-on-same-line:** use `PositionalTab` (`alignment: PositionalTabAlignment.RIGHT`, `leader: PositionalTabLeader.DOT`) inside a `TextRun`, not literal `.` or space padding.

## Verify the output

After writing a `.docx`, render it and look at it:

```bash
python scripts/office/soffice.py --headless --convert-to pdf output.docx
pdftoppm -jpeg -r 100 output.pdf page
ls page-*.jpg   # then Read the images
```

`pdftoppm` zero-pads page numbers to the width of the page count (`page-01.jpg`…`page-12.jpg`).

## Editing existing documents

Legacy `.doc` files must be converted first: `python scripts/office/soffice.py --headless --convert-to docx file.doc`.

Prefer the shared Python `zipfile` helpers (Windows and Unix). Do not use `Expand-Archive`: it does not preserve OOXML entry names or compression, and is not sufficient. `zipio.py unpack` refuses symlink entries — docx from external parties is untrusted.

```bash
python scripts/office/zipio.py unpack doc.docx unpacked/
python scripts/merge_runs.py unpacked/   # coalesce fragmented runs so text is findable
# edit unpacked/word/document.xml in place — do NOT reformat or pretty-print
python scripts/office/zipio.py pack unpacked/ out.docx
python scripts/office/validate.py out.docx --original doc.docx   # XSD checks; --auto-repair fixes common issues
# redlining? add --author "<the name you redlined under>" to check every edit is tracked
```

On Unix, `unzip` / `find ... -type l -delete` / `zip -Xr` remains an optional equivalent; still delete symlink entries before editing, and do not use `Expand-Archive` as a substitute.

Word splits text across many `<w:r>` runs (revision ids, spell-check markers), so a phrase you can see in the document often doesn't exist as a contiguous string in the XML. `merge_runs.py` merges adjacent identically-formatted runs in `word/document.xml` without changing content or rendering; it also accepts a `.docx` directly (`python scripts/merge_runs.py doc.docx -o merged.docx`).

**Tracked changes:** when redlining, validate with `--author "<the name you redlined under>"` (needs `--original`) — it reports any text you changed without a `<w:ins>`/`<w:del>` around it, which is easy to do by accident and invisible in the accepted view. Wrap runs in `<w:ins>`/`<w:del>` with `w:id`, `w:author`, `w:date` attributes. Inside `<w:del>`, the text element is `<w:delText>`, not `<w:t>`. A deleted paragraph mark (`<w:pPr><w:rPr><w:del w:id=".." w:author=".." w:date=".."/></w:rPr></w:pPr>`) means "merge this paragraph into the next" — so deleting a paragraph outright is that plus a `<w:del>` around every run. The `<w:del/>` must come before the rPr's other children; their order is schema-enforced.

To produce a clean copy with all tracked changes accepted: `python scripts/accept_changes.py in.docx out.docx`.

Accepting a deleted paragraph mark should join that paragraph to the one below it, so a paragraph whose runs are *all* deleted vanishes. Word does this; `accept_changes.py` and `pandoc --track-changes=accept` don't always. Both fail the same way — they strip the deleted text but leave the emptied paragraph behind, which reads as a stray empty bullet when it was auto-numbered:

- `pandoc --track-changes=accept` never joins the paragraphs.
- `accept_changes.py` (LibreOffice) joins them correctly, except when the deleted paragraph is followed by an empty spacer paragraph.

An empty bullet in either view is an artifact of that view, not a defect in the document. Check paragraph deletions in the XML.

## Comments

Comments require six cross-linked files. Use the helper — directory mode when you'll also be editing `document.xml` (saves an unzip/rezip cycle), `.docx`-direct mode otherwise:

```bash
# Against an already-unpacked directory (preferred when also placing markers)
python scripts/comment.py unpacked/ "Fees & expenses cap is too low"
python scripts/comment.py unpacked/ "Agreed" --parent 0

# Against a .docx directly
python scripts/comment.py contract.docx "This cap is too low" -o annotated.docx
```

The script writes `comments.xml`, `commentsExtended.xml`, `commentsIds.xml`, `commentsExtensible.xml`, the relationships, and the content-type overrides. Comment IDs are auto-assigned. It then prints the `<w:commentRangeStart>`/`<w:commentRangeEnd>`/`<w:commentReference>` snippet to add to `word/document.xml` so the comment anchors to specific text — until you place those markers, the comment exists but is not visible.

## Dependencies

`docx` (npm — not preinstalled here; install only with permission if `require('docx')` fails) · `pandoc` · LibreOffice (`soffice`) · `pdftoppm` (Poppler)

<!-- provenance:start -->
> 创作归属：原创改进（基于上游）。来源、署名与许可见 [来源说明](../../ATTRIBUTION.md#docx)。
<!-- provenance:end -->
