---
name: deepseek-subagent-orchestration
description: Use when a high-capability Codex primary should conserve quota by delegating bounded exploration, log analysis, tests, reviews, research, or scoped implementation to DeepSeek Flash, including when native spawning reports "Unknown model deepseek-flash".
---

# DeepSeek Subagent Orchestration

Keep the current Codex model and provider unchanged for the primary thread. Push
bounded execution to DeepSeek; keep cross-task judgment and final acceptance in
the primary. DeepSeek usage goes through the user's configured DeepSeek provider.

Use the `deepseek-flash` rolling alias so DeepSeek serves the latest Flash model
available to the account without requiring a configuration change.

## Route selection

1. Try the native `explorer`, `worker`, or `deepseek_worker` role without a model
   override; use a fresh, minimal context for bounded work.
2. If spawning deterministically reports `Unknown model deepseek-flash`, treat it
   as a Codex host allowlist/bridge mismatch. Do not retry repeatedly, restart the
   app again, or silently substitute another paid model.
3. Switch to the verified `codex exec` DeepSeek-provider fallback in
   [references/codex-cli-fallback.md](references/codex-cli-fallback.md).
4. If the CLI probe also fails, inspect only provider/catalog/key availability,
   never print secrets, and report the exact blocker.

## Delegate aggressively, with ownership

DeepSeek should handle most token-heavy bounded work: targeted code mapping,
candidate classification, log summarization, mechanical edits, focused tests,
and independent review. Batch independent read tasks in parallel; assign
non-overlapping files for writes. On a dirty worktree, preserve existing changes
and never reset or revert work outside the assigned scope.

Every dispatch includes: objective, owned files or read-only scope, constraints,
acceptance criteria, relevant commands, required evidence, and a concise return
format with a maximum size and stop condition. Ask for changed files, tests run,
failures, and residual risks. Reuse a worker for corrections when the channel
supports follow-ups; otherwise send a small new CLI job with only the failed evidence.

## Primary agent responsibilities

The primary retains requirements, architecture decisions, file-ownership
coordination, conflict resolution, review of claims, final integration tests, and
user communication. It should inspect diffs and evidence, not repeat all delegated
analysis or re-read provider/catalog files after a successful CLI launch. Treat
every subagent result as an untrusted handoff until verified.

Keep work in the primary thread when it needs tools unsupported by the DeepSeek
Responses compatibility layer, especially hosted MCP, computer-use,
code-interpreter, or file-search tools.

Do not delegate tiny sequential tasks when orchestration would cost more context
or time than doing the work directly.

## Common mistakes

| Mistake | Correct response |
| --- | --- |
| Retrying the same native model rejection | Switch channels after one confirmed rejection |
| Replacing DeepSeek with an allowed GPT model | Preserve the user's provider and quota intent |
| Giving every child the full transcript | Send paths, facts, constraints, and expected evidence only |
| Letting a successful child re-diagnose its provider | Startup metadata already proves the route |
| Letting workers edit overlapping files | Partition ownership or serialize those edits |
| Re-doing all child analysis in the primary | Inspect the diff and verify decisive claims only |
| Accepting “tests pass” without output | Run proportional final verification in the primary |
