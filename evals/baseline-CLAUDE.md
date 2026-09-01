# Fixed baseline CLAUDE.md — the "plain Claude Code" arm of the EAOS evaluation
#
# Purpose: docs/EVAL-PROTOCOL.md requires a FIXED, fair baseline. Copy this file verbatim
# into the target repo as CLAUDE.md for baseline runs. Do not tune it per task — a moving
# baseline invalidates the comparison. It represents good solo practice, deliberately
# WITHOUT EAOS mechanisms (no personas, no war room, no phase gates, no verifier spawn).

## Working rules

- Understand before editing: locate the relevant files, their callers, and the tests that
  cover current behavior. Cite file:line for claims about the code.
- State acceptance criteria for the task before implementing; keep them visible.
- Prefer the smallest change that satisfies the criteria; follow the repo's conventions.
- Run the project's own test/build/lint before declaring anything done; paste the real
  output, never summarize a run you didn't execute.
- Review your final diff against the criteria and for leftovers (debug logs, TODOs,
  secrets) before finishing.
- If a criterion cannot be verified locally, say so explicitly instead of claiming success.
