# agent-skills

[中文](README.md) · [English](README-EN.md)

> A purpose-categorized skill library for AI agents: 55 active skills, 11 archived skills and 10 categories — browse the catalog, install what you need.

## What's inside

- **55 active skills** across ten categories: requirements & planning; implementation & orchestration; quality, debugging & review; Git isolation & delivery; brand, design & UI; writing & content; documents & office; knowledge graphs, research & security research; skill authoring & runtime efficiency; data & backend. Each lives at the stable path `skills/<name>/`.
- **11 archived skills**: historical skills and drafts under `archive/`, not installed by default, kept for reference.
- **Catalog index**: category, value and upgrade notes live in `catalog.json`; the human-readable version is [docs/catalog.md](docs/catalog.md).
- **Traceable provenance**: every skill records its source (third-party / original / improved from upstream / unverified) and license in [ATTRIBUTION.md](ATTRIBUTION.md) and [skill-provenance.json](docs/sources/skill-provenance.json).
- **Removable installs**: `install.ps1` links skills into agent directories with junctions; the repo keeps the content, uninstall removes only the links.

## Install

This repo is a collection, not an install-everything bundle. The recommended setup keeps only the core preset and lets `skill-discovery` retrieve the rest on demand:

```powershell
.\install.ps1 -Preset core -DryRun
.\install.ps1 -Preset core
```

The core preset (`manifest.json` → `presets.core`) contains the always-on workflow skills — requirements, debugging, testing, planning, review and delivery — plus `skill-discovery`. When a task needs a capability outside those, it searches the catalog and loads only the matching `SKILL.md`; it does not copy or install anything. Add a single skill when needed:

```powershell
.\install.ps1 -Only pdf-toolkit -DryRun
.\install.ps1 -Only pdf-toolkit
```

Full install, uninstall and external-source setup: [installation guide](docs/guides/installation.md). The [DeepSeek API helper](skills/deepseek-subagent-orchestration/SKILL.md) keeps the current GPT lead and, when the user explicitly requests DeepSeek delegation, hands bounded work to your own `deepseek-flash` API. Use `deepseek-subagents` only when full Codex CLI worker processes and local toolchains are required; the two routes are mutually exclusive.

## Layout

```text
skills/    active skills, stable path per name
archive/   historical skills, rules and drafts; not installed
shared/    shared resources
docs/      catalog, install/maintenance guides and provenance
scripts/   repository checks and generators
tests/     offline regression tests
```

`catalog.json` holds human judgments, `manifest.json` defines install targets, `external.json` registers the independently maintained [toolkit-map](https://github.com/haxsd/toolkit-map) and [reverse-skills](https://github.com/haxsd/reverse-skills).

## Maintenance

Before adding or retiring a skill, check the [catalog](docs/catalog.md), update the index and run the repo checks per the [maintenance guide](docs/guides/maintenance.md). Third-party skills must be pinned to an upstream version and keep their license; original improvements keep upstream authorship and licensing.

## Docs

- [Catalog](docs/catalog.md)
- [Installation guide](docs/guides/installation.md)
- [Maintenance guide](docs/guides/maintenance.md)
- [Documentation index](docs/README.md)

## License

Repository content is [MIT](LICENSE); third-party material bundled with individual skills stays under its own license, see [NOTICE](NOTICE).
