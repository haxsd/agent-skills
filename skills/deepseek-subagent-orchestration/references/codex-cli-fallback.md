# DeepSeek CLI fallback

Use this only when native spawning rejects `deepseek-flash` before the child
starts. That error is distinct from a DeepSeek API authentication or rate-limit
failure.

## Read-only probe and job

Run from the target project directory. On this machine, keep the `rtk` prefix:

```powershell
rtk codex exec --ephemeral --skip-git-repo-check `
  -s read-only `
  -c 'model_provider="deepseek"' `
  -c 'model_catalog_json="C:/Users/Administrator/.codex/deepseek-models.json"' `
  -c 'model_reasoning_effort="high"' `
  -m deepseek-flash `
  'Read only. Inspect only the named project files; successful startup already proves the provider route, so do not inspect provider configuration. Answer the bounded question with at most 12 bullets, cite decisive file paths and commands, then stop.'
```

If `rtk` is unavailable, use the same command beginning with `codex exec`.

For an authorized implementation task, select the least-capable sandbox that
allows the assigned edits. Use `danger-full-access` only when the parent task
already permits it and narrower filesystem access cannot complete the job.

## Dispatch contract

A useful CLI prompt contains, in order:

1. one concrete objective;
2. exact read-only scope or owned files;
3. repository constraints, including dirty-worktree preservation;
4. acceptance criteria and focused verification commands;
5. the required compact result, maximum size, and stop condition.

Keep `--ephemeral` so delegated jobs do not create user-visible task history.
Never include `DEEPSEEK_API_KEY` or other secrets in prompts, arguments, or logs;
the provider must obtain credentials from the environment.

## Failure classification

Use this section only after the CLI launch itself fails. A running
`model: deepseek-flash` / `provider: deepseek` session needs no catalog diagnosis.

| Result | Meaning | Action |
| --- | --- | --- |
| Native `Unknown model` before start | Host bridge/allowlist mismatch | Use this CLI route |
| CLI says model/catalog missing | Local DeepSeek catalog configuration | Check the catalog path and alias |
| CLI returns 401/403 | Credential/account problem | Check environment configuration without printing the key |
| CLI returns 429 | Provider quota/rate limit | Back off or report the provider limit |
| Task starts but a hosted tool is absent | Compatibility limitation | Keep that tool-dependent portion in the primary |
