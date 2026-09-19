# v4.0.0 first real runs — synergina-app, 2026-09-18 (private repo; runtime records only)

Seven runs on EAOS v4.0.0 (commit 575869c), Claude Fable 5.1 medium, hooks installed.
Numbers read from each task's `.eaos/<task>/state.json`; summaries from the human.

| Run | Task | Kind / stakes | Units | Checks (bound) | Scenarios graded | Checker | Spawns | Episode |
|---|---|---|---|---|---|---|---|---|
| 1 hygiene fix | none | toy | — | — | — | — | 0 | **no task created**; lead skipped the runtime entirely |
| 2 dead code | T-030 | chore / internal | 0 | 3 | 0 | spawned; lead recorded its verdicts | 1 | verified |
| 3 env inventory | T-031 | question / internal | 3 read | 1 | 0 | yes | 4 | verified |
| 4 plan resolver | T-032 | refactor / internal | 1 build | 7 | 5/5 | yes | 2 | verified |
| 5 token revocation | T-033 | feature / production | 1 build | 4 | 6/6 | yes — caught unhandled throw | 3 | conditional-manual (4 items to human) |
| 6 CI gate | T-034 | deploy-shaped / production | 1 build | 11 | 3/3 | yes — caught missing typecheck script + vitest exclude | 2 | verified; PR #133 opened, no push to main |
| 7 merge stack | T-035 | integration / production | **0** | 1 | 0 | **none** | 0 | **never closed**; rebased a shared branch without a human gate |

Spawns across tasks 2-6: 12 total (v3 used 12 per task). Token counts not captured (transcripts
not exported). Every recorded check was snapshot-stable. Session binding: 1 of 6 sessions bound
(cause unknown until a transcript is inspected).

## Findings -> changes
1. Run 7: production stakes with no checker and a history rewrite on a shared branch. Fix: front
   door names branch-history rewrites as a human gate; checker unconditional above toy stakes for
   every task shape (merges, docs, integration included).
2. Runs 4, 5: turns wasted advancing INTAKE->BUILD to satisfy the audit's v3 phase check. Fix:
   audit check (b) phase_intake_consistency removed (phases are optional in v4).
3. Run 5: 19 criteria for 4 ACs — lead and checker invented different ids. Fix: ids fixed at intake
   (AC-n, S-n, R-B-n); the checker grades exactly those.
4. Run 1: toy stakes read as "skip EAOS". Fix: task new + verify + episode close are unconditional;
   toy skips units and the checker only.
5. Hooks bound 1/6 sessions: RESOLVED (see runs 8-9 below) — measurement artifact plus one real gap.

## Also found by the runs
- Live `CHAT_ENCRYPTION_KEY` committed in `training-ai-service/.env.example:86` (run 3) — rotate.
- Triage inbox T-028 was wrong on 2 of 4 "zero-importer" files (run 2 refused to delete them).
- 86 pre-existing lint errors on main; typecheck script missing on main (run 6).

## Runs 8-9 (EAOS cb1ed35, same day)

| Run | Task | Result |
|---|---|---|
| 8 resume T-035 | chore / production, fresh context | packet read first; AC-1..4, S-001..4, R-B-001 (fixed ids held); checker spawned for a merge-shaped task and APPROVEd with executed evidence; no rebase/push; `verify --require` 0; episode closed verified; audit clean. **spawns recorded = 0** although a checker ran. |
| 9 typo, toy | nothing to fix | one grep, no `task new`. Defensible (no work existed) but the front door says always; left as is — a task for a no-op is cost without value. |

Fixes 1, 3 and the history-rewrite gate from cb1ed35 all held in run 8.

### Finding 5 resolved: "hooks bound 1 of 6 sessions"
Replayed the real run-3 PostToolUse payload through the hook: bind succeeds. Spawn logs for
T-030..T-034 (1, 4, 2, 3, 2) were hook-recorded. `episode close` removes the session mapping by
design, so counting `.eaos/sessions/` after the fact showed only the one unclosed task. **The
1-of-6 figure was a measurement artifact.** Two real defects were behind it:
- **Resume path never binds.** A fresh context runs `status --packet`, never `task new`, so the
  session had no task and PreToolUse failed open: run 8's checker spawn was uncounted. Fix: the
  binder also fires on command-position `eaos status --packet T-nnn` and calls
  `session bind --resume`, accepted only for an active task no other session claims.
- **Legacy task dirs printed `no state.json for task: T-nnn`** on every scan (16 lines per
  command in synergina). Fix: scans skip dirs without state.json silently.

## Run 10 (EAOS cd5ea4d) — toy one-line edit, T-036
Fix 4 held: `task new` ran at toy stakes, no units, no checker; legacy-dir noise gone. Edit correct.
**Failure:** the lead guessed `verify --status` (flag is `--verdict`; the front door never showed the
syntax), got exit 2, and because `verify`, `verify --require`, `report`, `episode close` were one
chained command, the task closed `unverified` with **zero criteria** and the lead moved on.
Fixes: front door shows the verify line verbatim and says one command at a time; `--status` accepted
as an alias; `episode close` refuses a task with zero criteria unless `--abandon --reason` (tasks
with any recorded verdict still close honestly). T-036 stays closed-unverified as the record of it.

## Run 11 (54bfdb6) — T-037, premise false
Lead checked before building: typecheck script and blocking CI step already existed (run 6). One
snapshot-bound type check, no edits, no spawns, closed with `--abandon --reason` (first use; reason
logged with file lines). Correct behaviour; the use case was the reviewer's mistake.

## Run 12 (54bfdb6) — T17-10 idempotent fulfilment, production, in the integration worktree
First full feature since the fix rounds. Runtime record (worktree `.eaos/T-001`): 5 scenarios written
before any unit; 2 build units; checks type/test/lint/other + checker's own test run, all at the
handoff snapshot; checker (16 commands, clean context) mutation-tested the maker's tests, posted 3
findings, APPROVE; 18 criteria verified using the spec's own ids (AC0..AC11); closed verified; audit
clean; nothing pushed. Commit 73a661e, 8 files, +1000. Found a live coupon double-redeem bug and a
same-month free-to-paid grant bug beyond the spec. ~9 minutes wall clock, 38 lead tool calls.
Findings:
1. **spawns = 0 again, different cause.** Session cwd was the main checkout; every eaos command was
   `cd <worktree>; ...`. The hook looked at the main checkout's `.eaos`. Fix: binder follows the
   command's `cd` target, records a session->workspace pointer, pretool/stop honour it.
2. **All five scenarios graded with one shared evidence sentence.** Fix: `scenario grade` refuses
   evidence identical to another scenario's; verdict checklist asks for per-scenario evidence and
   names the mutation when leaning on the maker's tests.
3. Spec ids (AC0, AC0a..) used instead of AC-n: sensible. Front door now says spec ids win.

## Token cost of the runs (from transcripts, response level, de-duplicated by message id)
ctx0 = context at first response; fresh = uncached input + cache-creation tokens; subs = subagents.

| Run | responses | ctx0 | ctx max | lead out | lead fresh | subs | sub fresh |
|---|---|---|---|---|---|---|---|
| v3-era T-029 design overhaul (9916a675) | 196 | 107k | 289k | 77.6k | 374k | 12 | 626k |
| 2 dead code | 36 | 85k | 115k | 13.3k | 60k | 1 | 23k |
| 3 env inventory | 26 | 85k | 123k | 15.4k | 68k | 4 | 121k |
| 4 plan resolver | 94 | 85k | 175k | 32.4k | 128k | 2 | 123k |
| 5 token revocation | 48 | 85k | 138k | 20.9k | 91k | 3 | 145k |
| 8 resume T-035 | 30 | 85k | 129k | 12.6k | 82k | 1 | 36k |
| 9 / 10 / 11 toy + no-op | 2-6 | 73-85k | 76-88k | 0.2-1.3k | 30-37k | 0 | 0 |
| 12 T17-10 feature (+1000 lines) | 40 | 73k | 173k | 40.0k | 131k | 1 | 45k |

Reading: (1) one command expansion per session in every v4 run (v3: one per message). (2) No v4 run
reached 180k; none compacted. (3) **73-85k of context exists before EAOS does anything** — the front
door is ~1.6k of it; the rest is the host (system prompt, tool schemas, MCP servers, plugin skill
lists, CLAUDE.md). A two-response typo run costs 85k context for that reason alone. EAOS cannot
reduce it; the user's host configuration can. (4) The v3-era row is not a controlled comparison
(different task) but the shape is the point: 12 subagents and 626k subagent tokens vs 1 and 45k.

## Run 13 (v4.5.0, Claude Code) — T-038, prompt deliberately bare: "Fix the 6 react/no-unescaped-entities lint errors in platform/."
Intake test: no stakes, criteria or branch given. The lead chose **toy** (right call for a 4-line JSX text
escape; the reviewer's prediction of "internal" was wrong). Work verified independently: 1 file, 4 lines,
lint 86 -> 80, rule at 0, rendered text unchanged, none of the 33 uncommitted files touched, no commit, no push.
8 responses, context flat at ~75k (74k is host baseline), first real use of `eaos finish`. Final message honest
("I only re-ran the rule count, not the full lint or a build"; report file left as the skeleton).
Findings -> fixes (v4.5.1):
1. Closed `verified` on a sentence, no check through the runtime. Fix: `task new` records `start_snapshot`;
   completion refuses when the code changed since then and no check has passed against the current code
   (every stakes level; goals exempt; a task that changed nothing needs none).
2. Edited beside 33 uncommitted files without saying so (the scope check lives in a checklist toy never
   loads). Fix: front door: `git status --short` before the first edit; say it in one line; never stage,
   commit or revert the human's files.
3. Empty report skeleton at toy stakes. Fix: at toy the closing message is the report.

## Run 14 (v4.5.2, Claude Code) — T-039, bare prompt: "Fix the 16 react-hooks/set-state-in-effect lint errors in platform/."
Lead chose **internal** unprompted, ran `git status` first, did the 12-file refactor itself (no units, no
board), 17 responses, context 74k -> 99k. Work verified independently: no suppressions, one consistent React
pattern (adjust state during render against a `prev*` value), lint 80 -> 64, rule at 0, tsc clean, vitest
302/302 (run by the reviewer; nobody in the task ran it). Checks went through the runtime after the last edit
(v4.5.1 rule held). `eaos-checker` spawned and counted. Final message honest: "it reviewed the code and did not
run the pages in a browser".
Findings -> fixes (v4.5.3):
1. The checker graded the scenario `verified` **by reading diffs** (5 calls, 36 s) while the lead's own message
   said nothing was tried in the running app: verdict and truth disagreed. Fix: `scenario grade --verdict
   verified` requires `--check <id>` naming a passing runtime check against the current code; reading alone
   grades `manual_confirmation_required`, and the task closes CONDITIONAL.
2. The single scenario was written after the build. Fix: `scenario add` marks it LATE once the code differs
   from the task's start snapshot (a regression check, not a holdout); front door says before the first edit.
3. Nobody ran the test suite. Fix: front door and checker definition: run every kind of check the project has.

## Run 15 (v4.5.3, Claude Code) — T-040, real feature, loose prompt: reorganise the user dashboard
"what to do next, how the job search is going, recent activity; mobile; every feature reachable; reuse the
visual system; do not slow the page." Lead sized it as ONE internal task, not a goal (it fit: under 4 minutes,
18 responses, context 75k -> 112k). New branch `feat/t40-user-dashboard-ia`; 46 uncommitted files untouched and
said so. 7 criteria written from the ask (incl. AC-7 "no new waterfall"), 3 scenarios recorded BEFORE the first
edit (not LATE), a pure model module with 7 unit tests, checks type/test/lint through the runtime.
`eaos-checker` spawned, re-ran test and type itself, and:
- **failed AC-3**: the lead's own spec said activity merges applications, notifications and sessions; the
  code merges two. A real catch against the maker's own words.
- graded mobile (AC-4, S-003, R-B-001) `manual_confirmation_required`: "no render possible; human check at
  375px" (the live render was blocked by login). v4.5.3's rule produced the honest verdict.
`finish` refused. The lead did **not** overwrite the failed verdict: it posted a decision (B-002: AC-3 wording
overreached; past sessions cost an extra query; human to accept or ask) and left the task ACTIVE with nothing
committed. Final message opens "The task is not finished."
No EAOS change needed. Observation only: nothing in the runtime stops a lead re-recording a checker's `failed`
as `verified` on the same code; this lead did not try.

### Run 15, resolution (four hours later, same chat)
Human accepted the narrower scope. The lead recorded it as a board decision (B-003: "Human accepted B-002 ...
AC-3 reworded, id unchanged"), then **spawned a second `eaos-checker`** rather than re-grading its own work; that
checker re-ran the tests and recorded AC-3 `verified`. `finish` closed the task **conditional-manual**: the three
mobile items stay `manual_confirmation_required` because nobody has looked at 375px. Audit clean, 2 spawns
counted, nothing committed. This also answers the open observation from the first half: given the chance to
overwrite a checker's `failed`, the lead routed the re-grade through a fresh checker.

## Run 16 (v4.5.3, Claude Code) — T-041, meant as a goal-level test: "Finish T17-25: lint to zero errors, make the CI lint step blocking"
Lead sized it as ONE internal task again and finished in 4 min 19 s: 26 responses, context 75k -> 109k, 46
files, one checker spawn, closed verified. Independently confirmed: lint 0 errors (86 warnings), tsc 0, vitest
309 pass, eslint config untouched, `continue-on-error` removed from `test.yml`, nothing pushed. Real fixes:
`useS3`/`useCloudinary` were not hooks and were renamed; fetch moved out of JSX try/catch; inner component hoisted.
Findings:
1. **The goal level has still never fired.** The model does not open a goal for work it can finish in one
   context, and it keeps being right about that. The goal level is for work larger than a context; on this
   model that is rarer than assumed. Testing it needs either a truly product-sized ask or an explicit "treat
   this as a goal".
2. **Metric gaming passed the checker.** About 40 `no-explicit-any` errors were cleared by a new helper
   `loose(x)` returning `Record<string, any>` (one suppression inside the helper, 43 call sites). Lint is quiet;
   the untyped access the rule exists to stop is unchanged. The lead disclosed it plainly; the checker counted
   "only 3 new eslint-disable lines" and approved. Fix (v4.5.4, text only): checker definition and verdict
   checklist gain a metric-criteria rule (name the cheapest way to move the number, look for it, count escape
   hatches before and after, including a helper that launders the forbidden thing); intake checklist adds a
   HOW criterion when the ask is a number.
3. One scenario only, about the CI file. Thin for a 46-file change.
