# E0 grading harness — built and validated before any run

Pre-registration: `2026-09-17-E0-preregistration.md` (Procedure 3-4). The harness lives with the
frozen checks at `~/.eaos-holdouts/E0/`, outside this repository and every participant workspace,
mode 0700. This file records only hashes and validation results. It contains no check content.

| File | sha256 |
|---|---|
| `hidden-checks.md` (frozen 2026-09-17, unchanged) | `9dfd46e73354d23cf523d1a6db2437c7ba55d622d511a3445579f81207fdbff9` |
| `grade.py` — one snapshot, one unit | `8da7731b01316fe5b2d45b6620c218aa90f1a8671ba766721c45bf1961203467` |
| `grade_all.py` — blind batch (random labels, sealed map) | `b2aa3cce50eb6ae5f4dec494c949d77d6b0683a122b2f3de8430db5c4332a95c` |

Grader environment: its own venv (Flask 3.1.3, pytest), base at `pallets/flask@d73fa1c`.

## Design
Black-box wherever possible. Form field names, the restore URL and the tag/topic path are
**discovered** from the running app, never assumed, so two different correct implementations score
the same. Each check runs on a fresh database. Earlier units are re-run unscored at every later
snapshot, which gives the pre-registered "first snapshot at which a passing check fails".

## Validation (2026-09-18)
| Control | Expected | Got |
|---|---|---|
| Pristine base, unit 1 | standing 4 pass, all 5 unit checks fail | 4 / 9 |
| Reference solution (form field deliberately not named "tags"), units 1, 2, 3 | full marks | 9/9, 9/9, 10/10 |
| Reference solution after rename, unit 4, plus 16 earlier checks unscored | full marks | 11/11, 16/16 |
| Blind batch over the reference | 39 | 39 / 39 |
| Sabotage: 302 instead of 301 | lose the redirect check only | 10/11 |
| Sabotage: naive datetime | lose the UTC check only | 10/11 |
| Sabotage: anyone can restore | lose the regression check only | 10/11 |
| Sabotage: a template still says the old word | lose the wording check only | 10/11 |
| Sabotage: new dependency | lose S1 only | 10/11 |
| Sabotage: old JSON field name | lose the two checks that name the field | 9/11 |

The reference solution and sabotage copies stay outside the repository (a solution in the repo would
be readable by a participant).

## Judgement calls, fixed now so they cannot be tuned after seeing runs
- S2 runs the snapshot's own test suite and also requires it not to shrink below the base count.
- The API check accepts a top-level JSON list only (the frozen text says "JSON list").
- Ordering ties are removed by setting `created` explicitly in the base `post` table.

## Still required before run 1 (human, on the machine)
`scripts/e0_env.sh`, confirm the isolated command loads, record `claude --version`. Eight runs of
eight messages. Then: `venv/bin/python grade_all.py <runs_dir>` with `<run>/u1..u4` snapshots.
