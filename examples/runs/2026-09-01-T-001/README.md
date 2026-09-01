# Captured run: T-001 "Throne" (2026-09-01) — eval run 2, EAOS arm

Source project: greenfield toy ("throne" buyout MVP — public-safe, no business internals)
Task: build a one-page scarce-asset buyout app w/ Stripe test payments (verbatim prompt in
evals/results/2026-09-01-run2.md)
Outcome: verified (8/8 criteria pass; one stated gap — live e2e needs real Stripe+Postgres)
Notable: exactly-once webhook processing (processed_events), advisory-lock + FOR UPDATE +
compare-and-set takeover with auto-refunded losing buyers, refunds recorded as durable
obligations before any Stripe call + reconcile sweep, live-key refusal guard, 25/25 tests,
2 recorded loop-backs (security-fix rounds), independent fresh verifier, plain-language
final report with an explicit "what we did NOT do" section.
Sanitization: home paths rewritten; secrets grep reviewed by: grader session, 2026-09-01 —
all matches are documentation placeholders (sk_test_/whsec_ prefixes in deploy-guide prose).
