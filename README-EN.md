# agent-skills

[中文](README.md) · [English](README-EN.md)

> A purpose-categorized skill library for AI agents: 36 active skills, 11 archived skills and 9 categories — browse the catalog, install what you need.

## What's inside

- **36 active skills** across nine categories: requirements & planning, implementation & orchestration, quality & debugging, Git delivery, design & UI, writing, knowledge graph & security research, skill authoring & efficiency, data & backend. Each lives at the stable path `skills/<name>/`.
- **11 archived skills**: historical skills and drafts under `archive/`, not installed by default, kept for reference.
- **Catalog index**: category, value and upgrade notes live in `catalog.json`; the human-readable version is [docs/catalog.md](docs/catalog.md).
- **Traceable provenance**: every skill records its source (third-party / original / improved from upstream / unverified) and license in [ATTRIBUTION.md](ATTRIBUTION.md) and [skill-provenance.json](docs/sources/skill-provenance.json).
- **Removable installs**: `install.ps1` links skills into agent directories with junctions; the repo keeps the content, uninstall removes only the links.

## Install

From the repo root in Windows PowerShell, dry-run first:

```powershell
.\install.ps1 -DryRun
.\install.ps1 -Only deepseek-subagent-orchestration -Target codex -DryRun
.\install.ps1 -Only deepseek-subagent-orchestration -Target codex
```

Full install, uninstall and external-source setup: [installation guide](docs/guides/installation.md). The [DeepSeek API helper](skills/deepseek-subagent-orchestration/SKILL.md) keeps the current GPT lead agent and hands independent work blocks to your own `deepseek-flash` API; credentials are configured separately.

## Layout

```text
skills/    active skills, stable path per name
archive/   historical skills, rules and drafts; not installed
shared/    shared resources
docs/      catalog, install/maintenance guides and provenance
scripts/   repository checks and generators
tests/     offline regression tests
```

`catalog.json` holds human judgments, `manifest.json` defines install targets, `external.json` registers the independently maintained [toolkit-map](https://github.com/haxsd/toolkit-map).

## Maintenance

Before adding or retiring a skill, check the [catalog](docs/catalog.md), update the index and run the repo checks per the [maintenance guide](docs/guides/maintenance.md). Third-party skills must be pinned to an upstream version and keep their license; original improvements keep upstream authorship and licensing.

## Docs

- [Catalog](docs/catalog.md)
- [Installation guide](docs/guides/installation.md)
- [Maintenance guide](docs/guides/maintenance.md)
- [Documentation index](docs/README.md)

## License

Repository content is [MIT](LICENSE); third-party material bundled with individual skills stays under its own license, see [NOTICE](NOTICE).
