---
name: design
description: "Visual asset production for logos, corporate identity programs, banners, SVG icons, and social images. Use for creating brand and campaign artifacts, not for brand governance, design tokens, UI implementation, or slide decks; route those to brand, design-system, or ui-styling."
argument-hint: "[design-type] [context]"
license: MIT
metadata:
  author: claudekit
  version: "2.2.0"
---

# Design

Visual asset production for logos, CIP deliverables, banners, icons, and social
images. Adjacent disciplines have dedicated owners; load this skill only when
the requested deliverable is one of those visual assets.

## When to Use

- Logo design and AI generation
- Corporate identity program (CIP) deliverables
- Banner design for social media, ads, web, print
- SVG icon design and icon sets
- Social photos for Instagram, Facebook, LinkedIn, Twitter, Pinterest, TikTok

## Operating Boundary

- Commands below assume the current directory is this skill's installed root.
  Resolve `scripts/...` against that root, not against the user's project.
- Use the current host's image generation, browser, and screenshot tools when
  available. Do not assume that a named external skill or CLI exists. If the
  required capability is unavailable, say which artifact could not be produced.
- Respect explicit requirements for background, transparency, dimensions,
  copy, and quantity. Do not replace them with style defaults.
- Posters and artwork belong to `canvas-design`; brand voice and governance to
  `brand`; tokens to `design-system`; shadcn/Tailwind implementation to
  `ui-styling`; design research to `ui-ux-pro-max`.

## Sub-skill Routing

| Task | Sub-skill | Details |
|------|-----------|---------|
| Brand identity, voice, governance | `brand` | Dedicated skill |
| Tokens, specs, CSS vars | `design-system` | Dedicated skill |
| shadcn/ui, Tailwind, code | `ui-styling` | Dedicated skill |
| Presentations, pitch decks | `design-system` | Slide system and references |
| Design research and checklists | `ui-ux-pro-max` | Local searchable intelligence |
| Logo creation, AI generation | Logo (built-in) | `references/logo-design.md` |
| CIP mockups, deliverables | CIP (built-in) | `references/cip-design.md` |
| Banners, covers, headers | Banner (built-in) | `references/banner-sizes-and-styles.md` |
| Social media images/photos | Social Photos (built-in) | `references/social-photos-design.md` |
| SVG icons, icon sets | Icon (built-in) | `references/icon-design.md` |

## Logo Design (Built-in)

55+ styles, 55 color palettes, 55 industry guides. Gemini Nano Banana models.

> 计数口径：调色板与行业指南来自 `data/logo/colors.csv`、`data/logo/industries.csv`（各 55 条数据行）；改动数据文件时同步改这一行。

### Logo: Generate Design Brief

```bash
python scripts/logo/search.py "tech startup modern" --design-brief -p "BrandName"
```

### Logo: Search Styles/Colors/Industries

```bash
python scripts/logo/search.py "minimalist clean" --domain style
python scripts/logo/search.py "tech professional" --domain color
python scripts/logo/search.py "healthcare medical" --domain industry
```

### Logo: Generate with AI

Preserve the requested background. If the user asks for transparency, use an
output format and generator that support it; otherwise state the limitation
instead of silently adding a white background.

```bash
python scripts/logo/generate.py --brand "TechFlow" --style minimalist --industry tech
python scripts/logo/generate.py --prompt "coffee shop vintage badge" --style vintage
```

Diagnose missing dependencies or API configuration before changing code. Do
not modify unrelated project files to make a generator run.

If a preview would help, offer it with the host's confirmation UI or in plain
text. Load `ui-ux-pro-max` only when a design review is actually needed.

## CIP Design (Built-in)

50+ deliverables, 20 styles, 20 industries. Gemini Nano Banana (Flash/Pro).

### CIP: Generate Brief

```bash
python scripts/cip/search.py "tech startup" --cip-brief -b "BrandName"
```

### CIP: Search Domains

```bash
python scripts/cip/search.py "business card letterhead" --domain deliverable
python scripts/cip/search.py "luxury premium elegant" --domain style
python scripts/cip/search.py "hospitality hotel" --domain industry
python scripts/cip/search.py "office reception" --domain mockup
```

### CIP: Generate Mockups

```bash
# With logo (RECOMMENDED)
python scripts/cip/generate.py --brand "TopGroup" --logo /path/to/logo.png --deliverable "business card" --industry "consulting"

# Full CIP set
python scripts/cip/generate.py --brand "TopGroup" --logo /path/to/logo.png --industry "consulting" --set

# Pro model (4K text)
python scripts/cip/generate.py --brand "TopGroup" --logo logo.png --deliverable "business card" --model pro

# Without logo
python scripts/cip/generate.py --brand "TechFlow" --deliverable "business card" --no-logo-prompt
```

Models: `flash` (default, `gemini-2.5-flash-image`), `pro` (`gemini-3-pro-image-preview`)

### CIP: Render HTML Presentation

```bash
python scripts/cip/render-html.py --brand "TopGroup" --industry "consulting" --images /path/to/cip-output
```

**Tip:** If no logo exists, use Logo Design section above first.

## Banner Design (Built-in)

22 art direction styles across social, ads, web, and print. Use the current
host's HTML/CSS, image generation, and screenshot capabilities.

Load `references/banner-sizes-and-styles.md` for complete sizes and styles reference.

### Banner: Workflow

1. **Gather requirements** — purpose, platform, content, brand, style, quantity
2. **Research** — Use `ui-ux-pro-max` or user-provided references when available
3. **Design** — Create HTML/CSS and generate or source visuals with available tools
4. **Export** — Screenshot to PNG at exact dimensions with an available browser
5. **Present** — Show all options side-by-side, iterate on feedback

### Banner: Quick Size Reference

| Platform | Type | Size (px) |
|----------|------|-----------|
| Facebook | Cover | 820 x 312 |
| Twitter/X | Header | 1500 x 500 |
| LinkedIn | Personal | 1584 x 396 |
| YouTube | Channel art | 2560 x 1440 |
| Instagram | Story | 1080 x 1920 |
| Instagram | Post | 1080 x 1080 |
| Google Ads | Med Rectangle | 300 x 250 |
| Google Ads | Leaderboard | 728 x 90 |

**导出到 PNG 的命名约定**（按平台尺寸精确截图，用当前宿主可用的截图能力即可）：`assets/banners/{campaign}/{style}-{width}x{height}.png`，kebab-case；对时间敏感的投放加日期前缀 `{YYMMDD}-{style}-{size}.png`，方便按批次找回。截图后检查实际像素尺寸是否等于目标尺寸，不要只看文件名。
| Website | Hero | 1920 x 600-1080 |

### Banner: Top Art Styles

| Style | Best For |
|-------|----------|
| Minimalist | SaaS, tech |
| Bold Typography | Announcements |
| Gradient | Modern brands |
| Photo-Based | Lifestyle, e-com |
| Geometric | Tech, fintech |
| Glassmorphism | SaaS, apps |
| Neon/Cyberpunk | Gaming, events |

### Banner: Design Rules

- Safe zones: critical content in central 70-80%
- One CTA per banner, bottom-right, min 44px height
- Max 2 fonts, min 16px body, ≥32px headline
- Text under 20% for ads (Meta penalizes)
- Print: 300 DPI, CMYK, 3-5mm bleed

## Icon Design (Built-in)

15 styles, 12 categories. Gemini 3.1 Pro Preview generates SVG text output.

### Icon: Generate Single Icon

```bash
python scripts/icon/generate.py --prompt "settings gear" --style outlined
python scripts/icon/generate.py --prompt "shopping cart" --style filled --color "#6366F1"
python scripts/icon/generate.py --name "dashboard" --category navigation --style duotone
```

### Icon: Generate Batch Variations

```bash
python scripts/icon/generate.py --prompt "cloud upload" --batch 4 --output-dir ./icons
```

### Icon: Multi-size Export

```bash
python scripts/icon/generate.py --prompt "user profile" --sizes "16,24,32,48" --output-dir ./icons
```

### Icon: Top Styles

| Style | Best For |
|-------|----------|
| outlined | UI interfaces, web apps |
| filled | Mobile apps, nav bars |
| duotone | Marketing, landing pages |
| rounded | Friendly apps, health |
| sharp | Tech, fintech, enterprise |
| flat | Material design, Google-style |
| gradient | Modern brands, SaaS |

**Model:** `gemini-3.1-pro-preview` — text-only output (SVG is XML text). No image generation API needed.

## Social Photos (Built-in)

Multi-platform social image design: HTML/CSS → screenshot export. Use `brand`
and `design-system` only when their inputs are needed.

Load `references/social-photos-design.md` for sizes, templates, best practices.

### Social Photos: Workflow

1. **Plan** — Track independent assets; use parallel workers only when their write scopes are separate
2. **Analyze** — Parse prompt: subject, platforms, style, brand context, content elements
3. **Ideate** — 3–5 concepts; show them with the host's available preview or plain text
4. **Design** — Apply brand/tokens when available; create HTML per concept and size
5. **Export** — Screenshot at exact px with an available browser (2x scale when appropriate)
6. **Verify** — Inspect the rendered result for clipping, contrast, and required copy
7. **Report** — Summarize decisions in the final response; write files only when asked
8. **Organize** — Follow the project's existing asset conventions

### Social Photos: Key Sizes

| Platform | Size (px) | Platform | Size (px) |
|----------|-----------|----------|-----------|
| IG Post | 1080×1080 | FB Post | 1200×630 |
| IG Story | 1080×1920 | X Post | 1200×675 |
| IG Carousel | 1080×1350 | LinkedIn | 1200×627 |
| YT Thumb | 1280×720 | Pinterest | 1000×1500 |

## Workflows

### Complete Brand Package

1. **Logo** → `scripts/logo/generate.py` → Generate logo variants
2. **CIP** → `scripts/cip/generate.py --logo ...` → Create deliverable mockups
3. **Presentation** → Use `design-system` → Build and validate the slide deck

### New Design System

1. **Brand** (brand skill) → Define colors, typography, voice
2. **Tokens** (design-system skill) → Create semantic token layers
3. **Implement** (ui-styling skill) → Configure Tailwind, shadcn/ui

## References

| Topic | File |
|-------|------|
| Design Routing | `references/design-routing.md` |
| Logo Design Guide | `references/logo-design.md` |
| Logo Styles | `references/logo-style-guide.md` |
| Logo Colors | `references/logo-color-psychology.md` |
| Logo Prompts | `references/logo-prompt-engineering.md` |
| CIP Design Guide | `references/cip-design.md` |
| CIP Deliverables | `references/cip-deliverable-guide.md` |
| CIP Styles | `references/cip-style-guide.md` |
| CIP Prompts | `references/cip-prompt-engineering.md` |
| Banner Sizes & Styles | `references/banner-sizes-and-styles.md` |
| Social Photos Guide | `references/social-photos-design.md` |
| Icon Design Guide | `references/icon-design.md` |

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/logo/search.py` | Search logo styles, colors, industries |
| `scripts/logo/generate.py` | Generate logos with Gemini AI |
| `scripts/logo/core.py` | BM25 search engine for logo data |
| `scripts/cip/search.py` | Search CIP deliverables, styles, industries |
| `scripts/cip/generate.py` | Generate CIP mockups with Gemini |
| `scripts/cip/render-html.py` | Render HTML presentation from CIP mockups |
| `scripts/cip/core.py` | BM25 search engine for CIP data |
| `scripts/icon/generate.py` | Generate SVG icons with Gemini 3.1 Pro |

## Prerequisites

**Python:** This skill uses Python scripts. On Windows, use `python` instead of `python3` (e.g., `python scripts/logo/search.py` instead of `python3 scripts/logo/search.py`).

Check the verified Python runtime before running scripts:
```bash
python --version
```

## Setup

```bash
Set `GEMINI_API_KEY` in the current environment when image generation is
required. Never commit it. Install `google-genai` and `pillow` only with the
user's permission in the selected project environment.
```

> **Note for Windows:** Use `python` instead of `pip` where needed (e.g., `python -m pip install ...`).

## Integration

**Adjacent skills:** brand, design-system, ui-styling, ui-ux-pro-max
**Optional host capabilities:** image generation, browser preview, screenshot export

<!-- provenance:start -->
> 创作归属：原创改进（基于上游）。来源、署名与许可见 [来源说明](../../ATTRIBUTION.md#design)。
<!-- provenance:end -->
