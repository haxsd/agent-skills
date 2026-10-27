# PDF Toolkit Dependencies

Install only the packages needed for the requested operation. Do not install
system packages or packages globally without the user's permission.

## Required by capability

| Capability | Python package | License | Notes |
|------------|----------------|---------|-------|
| Inspect, merge, split, rotate, encrypt, decrypt, forms | `pypdf` | BSD-3-Clause | Core operations; use 6.x for AES-256 |
| Layout-aware text and table extraction | `pdfplumber` | MIT | Pulls PDF parsing dependencies |
| Create PDFs and text watermarks | `reportlab` | BSD-3-Clause | Optional TrueType font support |
| Render page images | Poppler `pdftoppm` | GPL-2.0-or-later | External executable, not bundled |

## Install

```powershell
python -m pip install -r requirements.txt
```

Use the project's verified Python environment. If the project uses a virtual
environment, install there instead of the global interpreter.

## Failure behavior

- Missing Python packages: the command stops and names the package.
- Missing `pdftoppm`: rendering stops; install Poppler or provide the verified
  executable path with `--pdftoppm`.
- Wrong or missing password: the command stops without printing the password.
- Unsupported font: creating a PDF stops; pass `--font-file` for CJK or a
  custom typeface instead of assuming Helvetica covers every glyph.
