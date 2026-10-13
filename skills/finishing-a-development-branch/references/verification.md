# Verification Reference

Shared evidence contract for completion claims. Used by finishing-a-development-branch and plan execution.

## The Rule

Evidence before claims. A claim is valid only when it is bound to a verification command that was run against the current code state, and its actual output confirms the claim.

## What Proves What

| Claim | Requires | Not sufficient |
|-------|----------|----------------|
| Tests pass | Test command output: 0 failures | Previous run, "should pass" |
| Linter clean | Linter output: 0 errors | Partial check, extrapolation |
| Build succeeds | Build command: exit 0 | Linter passing |
| Bug fixed | Test of the original symptom passes | Code changed, assumed fixed |
| Regression test works | Red-green cycle verified | Test passes once |
| Requirements met | Line-by-line checklist | Tests passing |
| Delegated agent finished | VCS diff shows the changes | Agent's success report |

## Binding Evidence to Code State

- Record the code state (commit hash or working-tree state), the verification command, and the result.
- Evidence is invalidated when the code it covers changes; re-run only what the change touches.
- Do not re-run unchanged checks just to restate them in a new message.

## Red Flags

- "Should work", "probably", "seems to" before running anything.
- Satisfaction language ("Done!", "Perfect!") before the check output was read.
- One green check extrapolated into "everything passes" (lint ≠ build ≠ requirements).
- Trusting a subagent's success report without checking the diff.
- Partial verification (ran one test file, claimed the suite).
