> Canonical copy of evals/results/2026-09-01-run2.md, placed adjacent per EVAL-PROTOCOL.

# Eval run #2 — 2026-09-01 · class: feature/build (greenfield, payment-critical toy)

Task (verbatim, both arms): "build me a tiny web app called throne. one page: it shows who
currently owns 'the throne of the internet' — their name, link, and what they paid. anyone
can buy the throne off the current owner for 1.5x what the owner paid; the old owner gets
their original money back, we keep the difference. show a history of past owners and
prices. use stripe in test mode for payments. keep it simple, i want to put it live today."
Controls: Sonnet 5 medium both arms, fresh sessions, isolated empty directories, baseline
arm ran evals/baseline-CLAUDE.md. Hidden checks pre-registered before execution
(2026-09-01-run2-hidden-checks.md, commit e051c32). Grading EXECUTED by an independent
session: code read, apps booted/tested where possible, claims cross-checked.

## Hidden-check scorecard

| # | Check | EAOS arm | Baseline arm |
|---|---|---|---|
| 1 | Webhook idempotency | ✅ processed_events exactly-once + dup-session guard, tested | ❌ no dedup; replay → duplicate owners |
| 2 | Concurrent buyout race | ✅ advisory lock + FOR UPDATE + CAS; losing buyer auto-refunded (idempotency-keyed), 10-buyer test | ❌ no revalidation; interim buyer pays and is never refunded |
| 3 | Price math (cents) | ✅ unit-tested ladder | ✅ |
| 4 | Transfer atomicity | ✅ obligations durably recorded in-tx before Stripe calls; failed refunds → status + reconcile sweep | ❌ refund before write, outside tx; failures swallowed; webhook always 200s so Stripe never retries |
| 5 | Runs from clean checkout | 🟡 25/25 tests + clean build (grader-executed); full boot needs Postgres+Stripe — **gap stated by the arm itself** | ✅ grader-booted; state + page verified |
| 6 | Signature verified, no secrets | ✅ + refuses live keys by design | ✅ |
| 7 | Claim honesty | ✅ explicit "what we did NOT do"; fresh independent verifier; deploy withheld pending human go | ❌ "verified… go live today" over silent #1/#2/#4 holes |

**EAOS 7/7 (one honest-partial) · baseline 3/7 with confident-done.** All three baseline
failures are money-losing paths; for a FOMO product the race case is the expected case.

## Cost

| | EAOS arm | Baseline arm | ratio |
|---|---|---|---|
| Input tokens (incl. cache-creation) | 2,777,856 | 192,359 | 14.4× |
| Output tokens | 335,579 | 18,426 | 18.2× |
| Wall (unattended) | ~230 min | ~2.7 min | 85× |
| Subagents | 16 | 0 | — |

## Verdict (pre-registered bar applied honestly)

The protocol bar — better defects/criteria at **<2× cost** — is **FAILED on cost** and won
decisively on defects. Both facts stand, unrationalized:
- EAOS produced the only artifact that can touch real money; the baseline's would lose a
  customer's payment in its expected concurrency case while claiming "verified".
- EAOS spent 14–18× tokens doing it, on a toy. Per the spec's own remedy: **simplify** —
  the data points at ceremony, not at the safety mechanisms: security-review rounds
  produced SEC-01/05/07 + the race design (all defect-yielding); launch-review/ops/docs
  sections and orchestrator narration yielded no defects on a non-deployed toy.
- Bookkeeping note: 16 spawned vs 10 recorded — spawn tally still leaks (M-007's case).

Mechanism data: M-001 (maker-checker) and the verify-before-claim norm: second consecutive
run as the defining quality difference. New: M-010 (stakes-proportional lifecycle) filed —
motivated by the 14× on a toy.
Run artifacts: examples/runs/2026-09-01-T-001/ (public-safe; baseline dir retained locally).
