---
name: deepseek-subagent-orchestration
description: Delegate independent work blocks to the user's DeepSeek Flash API while the current Codex GPT model leads. Use for multi-step implementation, test writing, diagnosis, documentation, batch analysis, solution comparison, and independent review; supports scoped file tools and named checks.
---

# GPT primary with DeepSeek workers

Keep the current conversation's GPT model, provider, and reasoning settings.
Use this skill's `scripts/deepseek_worker.py` and the user's `deepseek-flash` API.
Workers are external API agents, not native Codex subagent threads.

## Default routing

For a nontrivial task, first identify independent work blocks with a concrete
deliverable and acceptance criteria. **Delegate a useful block by default when
one exists**; do not restrict delegation to tiny or repetitive tasks. Briefly
state the division of work. If none is suitable, give the concrete reason once
(for example, a single tightly dependent edit), then work directly. Do not force
an API call for every reply or split a trivial task to satisfy a quota.

Good worker assignments include implementing a bounded module, adding tests,
investigating a failure, exploring selected sources, producing documentation,
comparing architecture options, and reviewing a patch. Complexity alone is not
a reason to exclude a task. Workers may propose architectural decisions; the
primary resolves requirement conflicts and chooses the final design.

The primary supplies only necessary context, defines owned paths and authorized
checks, verifies deliverables, integrates changes, and communicates the result.
Keep credentials, unrelated private data, production operations, publishing,
and final merge decisions with the primary. Delegation inherits the user's
existing authorization; it never creates permission for additional actions.

## Choose a mode and dispatch

Read [references/api-workers.md](references/api-workers.md) for setup, schemas,
limits, and examples. Resolve Python and any check executables through the local
tool map/runtime. Locate the helper relative to this skill, not the project.

- `execute`: default for independent implementation, exploration, tests, or
  diagnosis. Copies selected exact files into a separate workspace per job.
  DeepSeek can list/read/search those files, write explicitly owned paths, and
  run primary-authorized named checks through a bounded tool-call loop.
- `run`: lightweight analysis of supplied text/file excerpts with no tools.
  Use it when a compact read-only answer is sufficient.

1. Confirm the API route with `doctor` once per session/config change, or reuse
   a recent successful call. Do not change the primary model to enable it.
2. Write objective and acceptance criteria. For `execute`, select source files,
   exact writable paths, and fixed check argv. Include applicable project rules
   in context; do not copy the entire repository or conversation. Assign different
   owned paths to parallel implementation jobs. Default concurrency is 2.
3. Dispatch with a fresh output directory outside tracked project files. Work on
   independent primary tasks while calls run. Dependent jobs wait for verified
   prerequisites.
4. Read `summary.json` and relevant job artifacts. Review the modified files and
   actual check logs; a worker's `completed` status only means a valid handoff.
   Apply approved changes to the primary workspace and run decisive integration
   checks. Avoid redoing the worker's whole analysis when evidence is adequate.

File tools enforce the copied workspace and exact write ownership. Named checks
use fixed argv without a shell and receive a minimal environment without the API
key. **Check processes are not an OS sandbox**: authorize only appropriate local
test/build commands and trusted projects. A test can execute code from writable
files; use an actual OS/container sandbox when hostile code is involved. Workers
have no browser, MCP, arbitrary shell, Git publishing, or primary-workspace tools.

## Budgets and incomplete work

Execution defaults: 12 model rounds, 4,096 completion tokens per call, 48,000
reported total tokens per job, 96,000 conversation characters, 60-second HTTP
timeout, and at most 6 check runs per job. Select larger limits or thinking mode
for a justified complex block; small jobs can keep thinking disabled. Round/token
caps bound the loop, rather than forbidding substantial work. Usage is recorded;
the total budget uses a conservative input estimate and is not a billing cap.

Inspect status, model, finish reason, tool logs, and usage. Truncated, malformed,
failed, or contradicted results are incomplete. At most one focused correction
job for a failed acceptance criterion, then complete that part in the primary.
Do not repeatedly run a failed check without a relevant fix.

On 401/403 stop new batch dispatches and report the account failure. On
429/5xx/timeout report failure and continue locally when practical. No automatic
HTTP retry or silent provider/model substitution. Credentials remain in
`DEEPSEEK_API_KEY` or the Windows current-user DPAPI file outside the repository.
Never copy them to tasks, check environments, outputs, or commits.

`deepseek-flash` is a rolling alias. The 2026-09-30 verified mapping is V4.1
Flash; recheck [release notes](https://api-docs.deepseek.com/updates/) when needed.

<!-- provenance:start -->
> 创作归属：本仓原创。来源、署名与许可见 [来源说明](../../ATTRIBUTION.md#deepseek-subagent-orchestration)。
<!-- provenance:end -->
