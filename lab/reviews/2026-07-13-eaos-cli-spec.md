# `eaos` runtime CLI — build spec (ROADMAP backlog #1)

Goal: move the kernel's deterministic bookkeeping from prompt-enforcement to a small script.
Rules become computational: a ceiling is an exit code, not a sentence the model may skip.

## Constraints
- ONE file: `scripts/eaos` (python3, stdlib only — json/argparse/os/re/datetime; NO pyyaml).
  Executable (`#!/usr/bin/env python3`, chmod +x). ~400 lines target. No new deps ever.
- All state under `./.eaos/` in the cwd (the target project), same layout the kernel already
  defines. Two files per task: `warroom.md` (human-readable log, append-only) and
  `state.json` (machine state: counters, gates, criteria, spawns).
- Every command prints a one-line machine-readable result. Exit 0 = allowed/ok,
  exit 1 = ceiling hit / gate unmet / invalid, exit 2 = usage error, exit 3 = CONDITIONAL
  (`verify --require` only), exit 4 = infrastructure (lock contention — nothing mutated,
  retry; never a verdict, hooks fail open on it). Codes 3/4 were added by the §11
  consistency layer and review round 4 respectively.
- Timestamps: ISO-8601 local. Message ids: msg-001, msg-002… per task, assigned by the CLI.

## Commands

### `eaos init`
Create `.eaos/memory/{decisions,patterns,lessons,codebase}/`. Seed `.eaos/memory/index.md`
from `~/.claude/eaos/memory-seed/index.md` if present and index absent. Write
`.eaos/config.json` if absent with defaults:
`{"max_same_issue_loops": 3, "max_total_loopbacks": 8, "max_agent_spawns_per_task": 12,
"reserved_verifier_spawns": 1}` (the reserve: top slot(s) only a verifier may take — added
after the 2026-09-09 real run showed the orchestrator re-grading its own fix at 12/12)
(these mirror routing.yaml > loop_guard/budget; the CLI reads ONLY config.json — the
orchestrator may override values at init via flags: `--max-spawns N` etc.). Idempotent.

### `eaos task new "<title>"`
Allocate next T-NNN (scan `.eaos/T-*`, race-safe via os.makedirs exclusive). Create
`.eaos/T-NNN/artifacts/`, `warroom.md` with header (task title, date, status: active),
`state.json` (phase: INTAKE, counters zeroed). Print the id.

### `eaos append <id> --from X --to Y --type T --body "..." [--ref path] [--priority p]`
Sole-writer mechanized: appends a numbered protocol message (schema from
orchestrator/protocol.md) to warroom.md and mirrors it in state.json's message index.
Valid types: PROPOSE QUESTION CHALLENGE REVIEW RISK DECISION HANDOFF STATUS VERDICT.
Invalid type → exit 2.

### `eaos phase <id> <PHASE>`
Record phase transition (in state.json + a STATUS line in warroom.md). Any phase string
accepted (playbooks differ); keeps a history list.

### `eaos spawn <id> --agent <name>`
Increment spawn tally, log to warroom. If tally would EXCEED max_agent_spawns_per_task →
exit 1 with `BUDGET EXCEEDED: <n>/<cap> spawns — downgrade or drop an agent, or raise the
cap consciously at init`. The orchestrator calls this BEFORE each Task spawn.

### `eaos loopback <id> --edge "REVIEW->IMPLEMENT" --issue "<stable-key>" --attempt "approach -> outcome"`
The anti-spin core. Increments per-issue counter and total-loopback counter; appends the
attempt line to the ledger (state.json + warroom). Then:
- same-issue counter > max_same_issue_loops → exit 1: `DEADLOCK: issue '<key>' looped N times
  — escalate to the human with the attempt ledger` (print the ledger).
- total > max_total_loopbacks → exit 1: `CEILING: N total loop-backs — halt, hand the human
  the attempt ledger + best current state` (print the ledger).
- else exit 0 and print remaining allowance.

### `eaos gate <id> <phase> --check "<name>" --pass|--fail [--note "..."]`
Record a named gate check result. `eaos gate <id> <phase> --require` → exit 1 listing any
failed/unrecorded checks for that phase (orchestrator runs this before advancing).

### `eaos verify <id> --criterion "AC-1" --verdict pass|fail --evidence "file:line / test output"`
Build the DoD table. `--verdict` without `--evidence` → exit 2 (evidence is mandatory —
an unevidenced pass is the exact fantasy this tool exists to kill).
`eaos verify <id> --require` → exit 1 if any recorded criterion failed OR zero criteria
recorded (empty table ≠ verified). Prints the table.

### `eaos status <id>`
Resume aid: phase history, spawn tally vs cap, loop counters vs ceilings, gate results,
criteria table, last 5 war-room messages. This is what a fresh session reads to continue.

### `eaos report <id>`
Assemble a skeleton `final-report.md` in artifacts/ from state: criteria table, phase
history, decisions (DECISION messages), attempt ledger if nonempty, artifact file list.
The orchestrator fills in the plain-language prose around it (templates/final-report.md).
Refuses (exit 1) if `verify --require` would fail — a final report on an unverified task
is the "mad" scenario.

## Tests
`scripts/test_eaos.py` (stdlib unittest, run in a tempdir): id allocation (incl. two
concurrent `task new`), append numbering, spawn cap exit code, loopback ceilings (both),
gate require, verify evidence-mandatory + require-on-empty, report refusal, init idempotence.
Wire into Makefile `test` target: `@python3 scripts/test_eaos.py`.

## Wiring (docs — SECOND worker does this, not the CLI worker)
- commands/agentic-os.md: at Step 0, `command -v` check for `scripts/eaos` in the EAOS
  checkout or `~/.claude/eaos/bin/eaos`; if present, Steps 0/loop-backs/spawns/gates/verify
  MUST go through it and its exit codes are BINDING (a nonzero loopback = stop and escalate,
  not a suggestion). Prose remains the no-CLI fallback.
- setup.sh: install to `~/.claude/eaos/bin/eaos` (chmod +x); doctor checks it.
- orchestrator/loop.md + routing.yaml loop_guard comment: note ceilings are now
  CLI-enforced when installed; config.json mirrors these values at init.
- ROADMAP: move backlog #1 to Done with a line on what stayed prompt-enforced (routing
  choice, convergence rule, review quality — judgment, not bookkeeping).
- adapters/solo-mode.md: solo users may use `eaos verify/report` too (works in any tool —
  it's just python).

## Non-goals (do NOT build)
No token counting, no LLM calls, no yaml parsing, no daemon, no network, no colors beyond
pass/fail markers, no Windows-specific code (POSIX paths fine), no subcommands beyond the
list above.

## v4 additions (2026-09-18; docs/specs/2026-09-17-eaos-v4-architecture.md)
New verbs, same exit-code contract (0 ok · 1 refused · 2 usage · 3 conditional · 4 lock busy):
- `snapshot` — identity of the product inputs (HEAD + tracked modifications + untracked
  non-ignored files; `.eaos/` and cache noise excluded).
- `check <id> --category test|lint|type|build|rehearsal|other --cmd "<shell>"` — runs the
  command, records exit + output log + snapshot before/after; `--unavailable --reason` for an
  explicit not-applicable. Exit 1 when the check fails or the command changed product files.
- `unit start|handoff` — a unit of work with scope and start revisions; `--ready` is refused
  without valid evidence for the current snapshot, with unreconciled in-scope board changes,
  or while stale; `--blocked --reason` is always available and never a success claim.
- `board post|resolve|view|diff|reconcile` — typed entries (≤400-char summary, `--ref`),
  runtime metadata, `--invalidates` marks a unit stale, budgeted views that never silently
  omit a blocking entry (exit 3 when incomplete), `--for checker` excludes maker claims.
- `writer claim|release|show` — one writer per workspace (advisory on hosts without a gate).
- `ctx <id> --tokens N` — records the lead's context size; exit 3 over the ceiling (advisory).
- `status --packet` — the bounded continuation packet for a fresh context.
- `scenario add|list|grade` — evaluator scenarios (K-2/K-3): written at intake from
  disclosed requirements, stored outside the workspace, listed to the checker only, graded by
  execution; `verify --require` refuses while any is ungraded; a failure marks it revealed.

## v4.3.0 additions (2026-09-19)

- `finish <task>`: `verify --require`, `report`, `episode close` in order; stops at the first refusal and
  closes nothing. Exit 0, or 3 when conditional. Replaces three chained commands (run 10).
- `unit start ... --criterion AC-n[,AC-m]`: the criteria a unit serves. `require_status` refuses a unit
  serving a criterion with no verdict, and a criterion declared at `task new --criteria` with no verdict.
- `goal intent|lock|amend|item|check|next|status <goal>`: a goal is a task of `--kind goal`. Intent
  contract with `R-n` and `A-n` lines, locked by sha256, changed only by `amend --reason`. Items are
  ordinary tasks linked by a `goal` field (not `parent`, which would pool the spawn budget). `check`
  refuses an unserved requirement, an item serving nothing (investigations excepted), an unknown
  requirement id, a cycle, a contract changed after lock. Completion is read from the items' own episode
  records; acceptance lines are criteria on the goal; all of it flows through `require_status`, so
  `verify --require`, `report`, `episode close` and `finish` agree.
- Hook mode `guard` (PreToolUse): scenario store unreachable by tools; Edit/Write refused while a
  different active task holds the workspace pen.

## v4.4.0 additions (2026-09-19)

- `checker run <task|goal> [--host auto|claude|cursor|codex] [--timeout-min 30]`: starts the independent
  checker as a separate headless process, counts it as a spawn, waits, then prints APPROVE / CONDITIONAL /
  REJECT **computed by `require_status` from the verdicts that process recorded**. A process that records
  nothing is a failed run (exit 1), never a pass. Exit 0 / 3 / 1.
- `drain <goal> --max-items 3 --max-minutes 90 [--host] [--permission-mode] [--allowed-tools]`: one headless
  process per ready item, dependency order. Stops: item budget, time budget, all closed (0); item did not
  finish with a pass, or an item closed without a pass, or nothing ready (3). Refuses an unlocked intent or a
  plan that does not cover it (1). Never locks intent, never grades acceptance.
- `$EAOS_HOST_CMD` replaces the host command (`<cmd...> <role> <prompt>`); used by the tests' fake host.
- claude invocation puts the prompt before `--allowedTools` (variadic; found by the first real run).

## v4.5.0 (2026-09-19)

`checker run`, `drain` and `$EAOS_HOST_CMD` are removed. They assumed hosts without subagents; Cursor has them and loads `~/.claude/agents/`. Design: `lab/specs/2026-09-19-hosts-own-their-subagents-design.md`.
