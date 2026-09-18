---
description: Run the Engineering Agentic OS on a task (v4 — the model leads; EAOS constrains actions and evidence, not reasoning).
argument-hint: <task description>
allowed-tools: Task, Agent, Read, Write, Edit, Bash, Glob, Grep
---

# EAOS

Task: **$ARGUMENTS**

EAOS gives you three things you cannot give yourself: working state that outlives a
context (the board), a check made without your reasoning (the checker), and evidence that
cannot be talked into existence (the runtime). Everything else is your judgement. This file
is loaded once; follow-up messages are plain conversation. **Do not re-run this command in
a live context.** In a fresh context on an existing task, run `eaos status --packet <task>`
first (it also binds this session to the task, so spawns are counted).

`E=~/.claude/eaos/bin/eaos` (or `scripts/eaos` in an eng-agent-os checkout). Its exit codes
are binding: 0 ok · 1 refused (budget, gate, not ready, blocked) · 2 usage · 3 conditional ·
4 lock busy, retry. No CLI installed → tell the human to run `setup.sh` and stop.

## Start (one command, then work)

`$E init && $E task new "<title>" --kind feature|bug|chore|incident|question --stakes toy|internal|production`

**Always, at every stakes level and every task shape** (a doc, a merge, a two-line fix):
`task new` first, criteria recorded with `$E verify`, and `verify --require`, `report`,
`episode close` at the end. Stakes decide only how much sits between: toy = you do the work
yourself, no units, no checker; internal = plus an independent checker; production = plus
`checklists/security.md` and an executed rehearsal for anything deploy-shaped. The checker
is never skipped above toy because the task "is just a merge" or "is just docs".
**Criterion ids are fixed at intake**: `AC-1..AC-n` for acceptance criteria, `S-n` for
scenarios, `R-B-nnn` for risks. Everyone, the checker included, grades exactly those ids and
invents no others. Two words in the ask are never assumed:
a deliverable class (*workflow, pipeline, CI/CD, deploy, release, migration, rollout*) is a
blocking question unless the codebase shows the house pattern; an identity or attribution
constraint (author, e-mail form, "only my name") becomes an acceptance criterion. Never add
`Co-Authored-By` or "Generated with" trailers unless asked. Read `checklists/intake.md`
for anything beyond a trivial change; record criteria with `$E verify` as you go. At
internal or production stakes, before any builder runs, write the **scenarios** the checker
will grade — end-to-end expectations from the disclosed requirements, held outside the
workspace: `$E scenario add <task> --title ... --given ... --when ... --then ... --requirement "<the disclosed requirement>"`.
Builders never read them; every scenario needs a checker verdict before the task can finish.

## Work in units

Trivial or small work: do it yourself. Otherwise cut the task into units of one plan item:

1. `$E unit start <task> --title "<item>" --kind build|read|check --scope <globs>` → `U-nnn`
2. Build units claim the pen: `$E writer claim <task> --unit U-nnn`. **One writer per
   workspace.** Parallel build units only on disjoint scopes in separate worktrees.
3. Post what others need on the board, never in prose to yourself:
   `$E board post <task> --type finding|decision|risk|question|claim --summary "<≤400 chars>" --ref <file> [--unit U-nnn] [--severity ...] [--invalidates U-nnn]`
   A finding that breaks another unit's assumption carries `--invalidates` that unit.
4. Before any handoff: `$E board diff <task> --unit U-nnn` and reconcile each entry
   (`$E board reconcile <task> U-nnn --entry B-nnn --disposition acted|not-applicable --note`).
5. Evidence, not claims: `$E check <task> --category test --cmd "<project test command>"`
   (also lint, type, build, rehearsal). It binds to the code snapshot; edit the code and it
   is void. Then `$E unit handoff <task> U-nnn --ready`, or `--blocked --reason` when stuck.

Spawn help through the Agent tool with these definitions and **only** these inputs:
- `eaos-builder` — a build unit. Give: the unit, criteria, `$E board view --for unit --unit U-nnn`,
  `checklists/build.md`. Nothing from your transcript.
- `eaos-reader` — research or a second opinion, read-only, any number in parallel within
  `budget.max_parallel_readers`. Give: the question, scope, `checklists/research.md`.
- `eaos-checker` — a clean-context check at internal or production stakes. Give: the task
  spec, `$E board view --for checker`, `$E scenario list <task> --for checker`, the
  snapshot id, the check commands, `checklists/verdict.md`. **Never your transcript, your
  claims, or the builder's notes.** It records verdicts itself with `$E verify` and
  `$E scenario grade`.

Readers and checkers contribute intelligence, not edits. If no checker slot remains, the
task is BLOCKED on the human (`$E loopback --class hard_blocker`), never "checked by me".

**Human gate, always, before doing any of these:** push or merge to a shared branch, deploy,
run a migration, spend money, delete data, and **rewriting history on any branch you did not
create in this task** (rebase, force-push, filter-branch, amend of a pushed commit). Prepare
it, show the exact command, and stop.

## Checklists (load on demand from `~/.claude/eaos/checklists/`)

intake · build · research · review · security · test-adequacy · verdict · deploy-rehearsal ·
operability · incident · reporting. Load one when its trigger applies; do not load all.

## Finish

Every criterion has a verdict with evidence: `verified | failed | blocked | not_reproducible |
manual_confirmation_required`. Nothing that did not execute is `verified`. Every high or
blocking risk on the board has a verdict (`--criterion R-B-nnn`), and every scenario has been
graded by the checker (`$E scenario grade`). Then
`$E verify <task> --require` (0 or 3), `$E report <task>`, `$E episode close <task>`.
Write `final-report.md` from `~/.claude/eaos/templates/final-report.md` and paste it to the
human: what was asked, built, checked with proof, decided, not done, and what needs them.

## Context

Watch `$E status --packet`: when it says OVER CEILING, finish the current unit, hand off,
and tell the human to start a fresh session with the packet. Detail belongs in files with a
`--ref`, never in the board summary or your own narration.
