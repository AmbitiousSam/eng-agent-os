# Routing eval — how to run it

A **classify-only dry run** of `evals/routing-golden.yaml` against the real `/agentic-os` front
door. This checks the routing *decision* (kind, playbook, roster), not full execution — no code
gets written, nothing gets built. `make eval` only schema-validates the fixture file itself
(`scripts/eval_check.py`); running the eval below is a separate, manual/LLM-judged step.

## Why classify-only

Running all 16 fixtures through a full build would be slow and expensive, and isn't what this
eval is checking. What matters here is: given this one-line task description, does the
orchestrator pick the right `kind`, the right `playbook`, and route in at least the right
minimum roster? That's a cheap, fast, repeatable check you can re-run every time
`orchestrator/routing.yaml` changes.

## How to run it

For each `cases[]` entry in `evals/routing-golden.yaml`:

1. Paste the `task` text to `/agentic-os`, prefixed with an explicit dry-run instruction:

   ```
   Classify only, do not execute. Given this task, tell me: the task kind, which playbook you'd
   select, the complexity level, which signals apply, and the full roster you'd activate
   (always + conditional agents), with a one-line reason for each conditional agent.

   Task: <paste the case's `task` text here>
   ```

2. Record the model's answer in the results table (below) alongside the fixture's `expected`
   block.
3. Mark each row **PASS** if: `kind` matches, `playbook` matches, and every agent in
   `expected.roster` appears in the model's roster (extra agents beyond the minimum are fine —
   the fixture is a floor, not a ceiling). Otherwise **FAIL**, with a one-line note on what
   diverged.
4. A human (or a second, fresh LLM judge with no context from the run being graded) reviews any
   FAIL and decides: fixture is wrong (routing.yaml changed and the golden file is stale — fix
   the fixture) vs. routing.yaml is wrong (the rule itself needs to change).

This can be run by a human pasting into a live session, or scripted by an agent that reads the
fixture, drives `/agentic-os` in dry-run mode per case, and fills in the table — either is fine;
the point is an eye (human or independent judge) confirms the verdicts, not a passing exit code.

## Results table template

Copy this into a dated results file (e.g. `evals/results/2026-07-13.md`) per run.

> **Canon is the fixture.** This table is a convenience mirror of `evals/routing-golden.yaml`
> — if you add/change a case there, regenerate the rows from the fixture (one row per
> `cases[]` entry); when the two disagree, the fixture wins.

| # | Task (short) | Expected kind/playbook | Got kind/playbook | Roster match? | Verdict | Notes |
|---|---|---|---|---|---|---|
| 1 | Fix a typo in README | chore / feature-delivery | | | | |
| 2 | Timezone default bug | bug / bug-fix | | | | |
| 3 | CSV export button | feature / feature-delivery | | | | |
| 4 | New notifications microservice | feature / feature-delivery | | | | |
| 5 | Checkout null-pointer w/ repro | bug / bug-fix | | | | |
| 6 | Payments API 5xx spike | incident / incident-response | | | | |
| 7 | Rate limiter question | question / investigation | | | | |
| 8 | New loyalty product (in-repo) | product / product-framing | | | | |
| 9 | Welder marketplace venture | venture / venture | | | | |
| 10 | Canary rollout of checkout | release / release | | | | |
| 11 | OAuth SSO login (auth signal) | feature / feature-delivery | | | | |
| 12 | Usage-based pricing tier | venture / venture | | | | |
| 13 | Retry-backoff refactor | refactor / feature-delivery | | | | |
| 14 | Greenfield expense-splitting app | product / product-framing | | | | |
| 15 | Search p99 latency redesign | feature / feature-delivery | | | | |
| 16 | Users table data migration | chore / feature-delivery | | | | |

**Summary:** `<N>/16 passed`. Any systematic miss (e.g. every pricing-shaped task gets routed to
feature-delivery) is a `routing.yaml` bug, not a one-off — file it and re-run this eval after
the fix.
