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
