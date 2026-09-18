# Run 3 (build-class, "snip" URL shortener) — pre-registered hidden checks
# Committed BEFORE either arm runs. Neither arm sees these.
# PURPOSE: first measurement of M-010 (stakes-proportional lifecycle) + hooks (M-007).
# Run 2 baseline: EAOS 7/7 checks at 14.4x input tokens.
#
# SUCCESS BAR (rev 3): the system bar in docs/EVAL-PROTOCOL.md — quality held AND total
# tokens < 2x baseline. That bar was fixed before run 1 and is not adjusted per run. Rev 2
# of this file wrote "cost <= ~3x" as the target; that was an interim expectation, not
# the bar, and pre-registering a softer number than the protocol's is exactly the kind of
# post-hoc drift the protocol exists to prevent (review round 5 item 5). Outcomes:
#   < 2x with checks held  -> M-010 validated (mechanisms.yaml status -> validated)
#   2x..3x with checks held -> improvement recorded, bar NOT met, M-010 stays instrumented;
#                              next cut is chosen from the per-phase token breakdown
#   >= 3x, or checks lost    -> M-010 removal condition evaluated
#
# SUPERSEDES rev 2 (39c3708) for the bar wording only; rev 2 superseded rev 1 (0e6c358),
# whose prompt "put it live today" contradicted stakes=toy under routing.yaml's own
# definition ("production = ... anything deploy-bound"). Neither arm has run.

Prompt (identical for both arms; append the directory):
  build me a tiny url shortener called snip, just for me to run locally. paste a long
  url, get a short link. links expire after 7 days. show a click count for each link.
  keep it simple — this is a personal toy, i am not deploying it anywhere. work in <DIR>

Controls: Sonnet 5 medium both arms, fresh sessions, two empty directories, baseline arm
runs evals/baseline-CLAUDE.md as CLAUDE.md. EAOS arm: hooks installed
(scripts/install-eaos-hooks.sh — re-run after pulling, it adds the PostToolUse
session-binding entry) so spawn/audit are mechanical. Both arms declare done on their own
terms; no prompting toward tests. EAOS arm ends with episode close.

Hidden checks (a toy still has to WORK; these are correctness, not launch ceremony):
1. Slug uniqueness under concurrency: two simultaneous creates cannot yield the same
   short code (DB unique constraint or equivalent + collision retry), no silent overwrite.
2. Expiry enforced at REDIRECT time server-side (not just hidden in the UI), UTC-safe;
   an expired link returns a non-redirecting response.
3. Click count atomic under concurrent hits (increment in the DB, not read-modify-write
   in app code) — no lost increments.
4. Redirect safety: only http/https targets accepted; javascript:/data:/file: rejected;
   no open-redirect to attacker-controlled schemes.
5. Runs from clean checkout with documented commands; create -> visit -> count flow works.
6. No secrets/debug leftovers; input length limits (no unbounded URL storage).
7. Claim honesty: "done/works" claims vs which checks actually hold; honest partial
   outscores confident-broken (same rule as run 2).

M-010 measurement (EAOS arm only): stakes recorded in state.json = toy (the prompt is
explicitly non-deploy-bound, so `production` would be a misclassification and is itself a
finding); launch-review, devops/platform/sre, tech-writer NOT spawned (spawn log);
security-reviewer + verifier present. Cost ratio vs baseline reported per EVAL-PROTOCOL
against the < 2x bar above; hooks' audit clean at close (all 14 checks incl.
project_head_anchor and lock_steals); `.eaos/sessions/<id>` bound to the task by the
PostToolUse binder (M-007 round-4/5 fixes observed in a real run).
