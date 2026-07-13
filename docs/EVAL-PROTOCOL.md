# A/B Evaluation Protocol — does EAOS earn its overhead?

EAOS adds real ceremony (personas, war room, gates, loops) on top of plain Claude Code. That
overhead is only justified if it produces measurably better outcomes. This is the protocol for
checking that honestly, instead of assuming it. Nothing in this repo has run this protocol yet
— it's the pre-registered design, so results can't be cherry-picked after the fact.

## Design

Take **10 real engineering tasks**, spanning at least: a small bug fix, a standard feature, one
with an auth/payments/PII signal, one refactor, and one investigation/question. Run each task
twice, from the same starting repo state:

- **(a) Baseline** — plain Claude Code with a good, hand-written `CLAUDE.md` for that repo, no
  EAOS personas/playbooks/gates. One session, no orchestration ceremony.
- **(b) EAOS** — the same task through `/agentic-os` (or the matching dedicated command), full
  routing, roster, and gates as configured.

Same task text, same starting commit, same model tier for the primary agent in both arms. Do
not let the same session see both arms (no contamination — a fresh session per arm, per task).

## Metrics (recorded for every run, both arms)

| Metric | How to measure |
|---|---|
| Defects found post-hoc | A human (or independent reviewer) reviews the final diff for bugs/regressions the run's own checks missed. Count them. |
| Acceptance-criteria hit rate | % of the task's stated acceptance criteria actually satisfied by the final diff. |
| Tokens | Total tokens consumed across the run (all subagents combined, for EAOS). |
| Wall-clock | Start to final diff, human time not included. |
| Human interruptions | Count of times the run stopped and asked the human something (clarifications, gate approvals, blockers). |

## Pre-registered success bar

**EAOS must beat plain Claude Code on defects found post-hoc AND acceptance-criteria hit rate,
at under 2x the token cost of the baseline.** This bar is fixed before running any tasks — it is
not adjusted after seeing results.

- If EAOS wins on quality but costs ≥2x tokens: EAOS is too expensive for what it buys — cut
  agents/phases until it's under the line, then re-run.
- If EAOS does not beat the baseline on quality: the ceremony isn't paying for itself — simplify
  before adding anything else to the pipeline.
- If EAOS wins on quality within budget: the overhead is justified; note which task types showed
  the biggest gap (that tells you where the ceremony matters most).

## Reporting

Record every run's raw numbers in a results table (one row per task per arm) plus the verdict
against the bar above. Do not average away outliers without also showing them — a single
catastrophic miss in one arm is signal, not noise.

## Out of scope for this protocol

- Statistical significance testing — 10 tasks is a directional read, not a proof. Treat results
  as "worth investigating further" or "worth acting on now," not as a p-value claim.
- Live-testing this across IDEs other than the one it's run in (see `adapters/solo-mode.md` for
  the honest cross-IDE story).
