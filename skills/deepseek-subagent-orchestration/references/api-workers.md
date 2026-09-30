# API worker configuration and contracts

The stdlib helper calls the user's DeepSeek API; it does not launch a Codex
session or change config.toml. GPT remains the primary. The two commands are
`run` for one-shot analysis and `execute` for agents with scoped file tools.

## Setup

Configuration defaults to $CODEX_HOME/deepseek-worker.json, or
~/.codex/deepseek-worker.json. Fields: base_url (default https://api.deepseek.com),
model (deepseek-flash), api_key_env (DEEPSEEK_API_KEY), encrypted_key_file.
No plaintext credential fields are accepted. Environment credentials take
precedence. On Windows the fallback is a current-user DPAPI encrypted file
beside the config; Linux/macOS can use an environment key.

Resolve absolute Python/helper paths through the local tool map/runtime:

```powershell
& $python $helper configure
& $python $helper doctor --probe
```

configure prompts without echoing. For already-authorized automated setup,
--key-stdin reads the key from stdin. Never embed keys in command text. Existing
config/credential files are not overwritten. doctor checks /models; --probe
also makes a tiny billed call. A successful recent call can replace the probe.
Global --config selects another nonsecret JSON config. HTTPS without URL
credentials/query/fragment is required; redirects are refused.

## Execution job

```json
{
  "jobs": [{
    "id": "fix-parser",
    "task": "Fix the empty-input bug and add boundary tests.",
    "acceptance": "Existing tests unchanged and passing; new tests cover the bug.",
    "context": "Relevant project rules and a bounded design requirement.",
    "files": ["src/parser.py", "tests/test_parser.py"],
    "writable": ["src/parser.py", "tests/test_parser_boundaries.py"],
    "checks": [{
      "name": "parser-tests",
      "argv": ["/verified/absolute/python", "-m", "unittest", "discover", "-s", "tests"],
      "timeout": 30
    }]
  }]
}
```

Replace the executable with the actual verified tool-map path, including a
Windows absolute path where appropriate. The example path is a placeholder.
argv is fixed by the primary; the worker chooses only the check name. No shell,
additional argv, or worker-selected executable is supported. Nested tool needs
must be resolved before dispatch; commands receive no inherited PATH or API/cloud
credentials. Use trusted project test/build code. These subprocesses are **not
an OS sandbox** and can access host resources through their code, create child
processes, or perform network I/O. Environment filtering and file-tool confinement
do not prevent that. Use a real external sandbox for hostile code; this helper
makes no such isolation claim. Timeouts terminate the direct check process;
checks must not spawn background processes.

```powershell
& $python $helper execute --jobs $jobs --root $project --out-dir $freshOutput
```

files and writable contain exact root-relative paths using forward slashes.
Only selected regular UTF-8 files are copied. Source links/junctions, path escapes,
credential/configuration paths, case aliases, Windows device names, and potential
key material fail preflight. New owned files are allowed. Copied files can be
read by the worker, but writes require an exact writable match. Include relevant
project conventions in context; .git, .codex and .agents are excluded.

Every job gets workspaces/<id> below the fresh output directory. The primary
workspace stays unchanged by file tools. Tools:

- list_files: copied/current files, owned paths, available check names.
- read_file: numbered lines, at most 300 and a bounded response; next_line allows pagination.
- search: case-insensitive literal search, at most 40 short matches.
- write_file: complete UTF-8 content, at most 100 KB, exact owned paths only.
- run_check: fixed named argv, no shell, at most 6 executions; exit/timeout/output recorded.
- finish: summary string and evidence/suggestions/unknowns arrays of strings.

Defaults: at most 8 jobs, 2 concurrent, 80 copied files and 40 owned files per job,
1 MB/source file, 4 MB/copied batch, 8 named checks/job, 12 model rounds,
4096 completion tokens/call, 48000 reported total tokens/job, 96000 conversation
characters, 60-second HTTP timeout. Check timeout is 1..60 seconds, default 30.

Flags: --concurrency 1..4, --max-tokens 256..16384, --max-rounds 1..32,
--max-total-tokens 256..128000, --max-input-chars 4000..256000,
--timeout 1..120, --thinking disabled|enabled. Thinking defaults to disabled;
choose enabled for justified reasoning work and allow a sufficient output budget.
Thinking content is retained only in in-memory tool history as required by the
provider protocol, never exported as evidence. Input/token estimates are not a
hard monetary budget; actual usage and latency are recorded, not promised.

## Lightweight analysis

```json
{"jobs": [{
  "id": "review-parser",
  "task": "Find incorrect empty-input handling and propose a minimal fix.",
  "acceptance": "Cite source lines and a reproducible example.",
  "context": "Return a compact answer in the supplied JSON handoff contract.",
  "files": [{"path": "src/parser.py", "start_line": 1, "end_line": 100}]
}]}
```

```powershell
& $python $helper run --jobs $jobs --root $project --out-dir $freshOutput
```

run is the backward-compatible read-only interface: no file or command tools.
It accepts exact file excerpts (up to 24/job) and context. Defaults: 2048 completion
tokens, 24000 input characters/job, 96000/batch, thinking disabled. Optional
--max-tokens 64..4096, --max-input-chars 1..48000, --max-batch-chars 1..192000,
--concurrency 1..4, --timeout 1..120. The model must return the same finish fields
as a JSON object; malformed/truncated handoffs are not accepted.

## Verify and integrate

summary.json contains status, returned model, aggregate usage, elapsed seconds,
and artifact paths. Each <id>.json includes result and, in execution mode, rounds,
workspace, modified_files, actual tool calls and check logs. A final workspace
inventory catches unexpected file mutations by checks, including deleted copied
files and outputs outside the owned paths; such jobs are marked error. Authorize
expected generated artifacts explicitly, or use checks that avoid producing them.

completed means a valid handoff, not that the implementation or checks passed.
The primary must inspect modified files, check actual exit codes, verify important
claims, integrate approved content, and run decisive integration checks. Do not
blindly copy a workspace directory. Keep different owned paths for parallel jobs
and dispatch dependent jobs only after validating prerequisites.

Exit 0: all valid handoffs; exit 1: one or more errors/incomplete jobs; exit 2:
local preflight/configuration failure. 401/403 stops unscheduled jobs; already
in-flight jobs may finish. No HTTP retries or silent provider/model changes.
Timeouts may be billed. Numeric HTTP status is retained without response bodies.
Only deepseek-flash and the verified deepseek-v4.1-flash response alias are accepted.

Keep dispatch and output directories outside tracked files. A focused correction
job may address a failed acceptance criterion once, with only the required context.

## Provider references

- [Tool calls](https://api-docs.deepseek.com/guides/tool_calls/): multi-turn function calls; the client executes the functions.
- [Thinking mode](https://api-docs.deepseek.com/guides/thinking_mode): thinking and tool history requirements.
- [JSON output](https://api-docs.deepseek.com/guides/json_mode): JSON response mode for lightweight analysis.
- [Release mapping](https://api-docs.deepseek.com/updates/): rolling deepseek-flash alias, checked 2026-09-30.
