# API worker setup and job contract

The stdlib-only helper calls `https://api.deepseek.com/chat/completions` directly.
It does not launch another Codex session or modify `config.toml`. This avoids
native subagent model allowlists and keeps the primary on its current GPT model.

## Credentials and configuration

Configuration defaults to `$CODEX_HOME/deepseek-worker.json`, or
`~/.codex/deepseek-worker.json` when `CODEX_HOME` is unset. No secrets are stored
in that JSON. `DEEPSEEK_API_KEY` takes precedence; on Windows the fallback is
`deepseek-worker.key.dpapi` beside the config, encrypted with Windows DPAPI for
the current user. Another account/machine needs its own setup. Environment keys
also work on Linux/macOS. Do not copy credentials into this skill or Git.

With the resolved absolute Python/helper paths, configure Windows interactively:

```powershell
& $python $helper configure
& $python $helper doctor --probe
```

`configure` prompts without echoing the key. For already-authorized automated
setup, `--key-stdin` accepts a key via stdin. Avoid literal keys in shell commands
or transcripts. `doctor` checks `/models`; `--probe` also performs one tiny billed
chat request. Run the probe once, rather than before every task. An environment
key requires no `configure` step. `--config <absolute-path>` selects another
nonsecret JSON config. The default official HTTPS endpoint is deliberate; a user
may explicitly configure a trusted compatible HTTPS provider through `base_url`.

Config keys: `base_url`, `model` (must be `deepseek-flash`), `api_key_env`, and
`encrypted_key_file`. Relative encrypted file paths resolve beside the config.

## Job file

```json
{
  "jobs": [
    {
      "id": "review-parser",
      "task": "Find incorrect handling of an empty input in this parser. Propose a minimal fix.",
      "acceptance": "Cite source lines and give a reproducible example; report uncertainty.",
      "context": "Do not redesign the module. Return at most three findings.",
      "files": [{"path": "src/parser.py", "start_line": 1, "end_line": 100}]
    },
    {
      "id": "classify",
      "task": "Group these skill names by their actual purpose.",
      "acceptance": "Every provided name appears exactly once; explain ambiguous assignments.",
      "context": "Names and descriptions supplied here by the primary.",
      "files": []
    }
  ]
}
```

Paths are relative to `--root`, exact files only; no glob/directory scan. Use
line ranges for large files. Symlinks/junctions escaping root, common credential
files, key material, invalid ranges, duplicate IDs, and oversized input fail
before any API request. This is a defense against accidental disclosure, not a
complete secret scanner: the primary must choose appropriate context.

```powershell
& $python $helper run --jobs $jobs --root $project --out-dir $freshOutput
```

Optional flags: `--concurrency 1..4`, `--max-tokens 64..4096`,
`--timeout 1..120`, `--max-input-chars 1..48000`, and
`--max-batch-chars 1..192000`. Context is measured in characters, not tokens.
The completion limit includes any provider reasoning tokens. Defaults suit
small tasks; real latency and cost depend on the job and provider.

## Results

`summary.json` gives per-job status, returned model, token usage, elapsed seconds,
and artifact name. Each `<id>.json` contains the full handoff with `summary`,
`evidence`, `suggestions`, and `unknowns` fields. Suggested changes are proposals;
no files are modified by workers. Logs print only batch counts and output path.
Exit 0 means all jobs returned well-formed, untruncated handoffs; exit 1 means
at least one incomplete/error result; exit 2 means local preflight/setup failure.
HTTP errors retain numeric status but omit response bodies to avoid echoed secrets.
After a 401/403, unscheduled jobs are marked `skipped`; already in-flight calls
may finish (at most the selected concurrency). Only `deepseek-flash` and the
verified `deepseek-v4.1-flash` response name are accepted.

The output directory must not already exist. Put dispatch/results outside tracked
files (for example a system temporary directory). A follow-up should include only
the failed acceptance criterion and the source needed to correct it.

## Verified sources

- [DeepSeek V4.1 release mapping](https://api-docs.deepseek.com/updates/), checked 2026-09-30.
- [JSON output](https://api-docs.deepseek.com/guides/json_mode): request JSON and include a concrete format in the prompt.
- [Thinking mode](https://api-docs.deepseek.com/guides/thinking_mode): small jobs explicitly disable thinking.
- [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents): native orchestration is host-specific; this helper uses an external API route.
