# War Room — T-001: Throne
task: build "throne" — one-page app, current owner of the throne, buy at 1.5x, prior owner refunded, house keeps difference, history, Stripe test mode
date: 2026-09-01
status: done
playbook: feature-delivery (greenfield / new-service)
signals: [payments, new-service, ui, public-api]
complexity: standard (provisional)

## Roster + why
- requirements — spec + acceptance criteria
- architect — money flow + data model (new-service)
- developer — build
- qa-engineer — test plan from spec (payments)
- code-reviewer — final diff
- security-reviewer — payments/webhook (can veto)
- devops-engineer — deploy guide
- tech-writer — README
- verifier — independent grading
OMITTED (budget/value): platform-engineer, sre-observability — single-page app, no scaling or SLO surface. Noted per budget rule.

## Log

### INTAKE (requirements)
PROPOSE artifacts/task-spec.md — 26 ACs. kind=feature, greenfield=true, complexity=standard. 15 assumptions, 0 blocking questions.
RISK HIGH AC20 — concurrent takeover race; needs compare-and-set on current owner + partial unique index + auto-refund of losing buyer.
RISK HIGH AC15 — webhook retry double-refund; needs processed_events table + stable Idempotency-Key from prior ownership row id.
RISK MED AC16 — refund failure leaves prior owner unpaid; policy = commit transfer, mark refund_status=failed, 2xx, manual recovery.
RISK MED AC18 — XSS / javascript: URL from user-supplied name+link; allowlist http(s), escape, rel=noopener noreferrer nofollow.
RISK FYI AC22 — "live today" vs TEST mode; live-key flip is a separate human gate, not in T-001.

[2026-09-01T11:34:24] STATUS phase: INTAKE -> PLAN

### PLAN (architect)
PROPOSE design-doc.md — 2 tables (ownerships, processed_events), 3 routes (GET /, POST /api/checkout, POST /api/stripe/webhook), ~20 files.
DECISION adr-001 — current owner = partial unique index on is_current; race safety = pg_advisory_xact_lock(7301) + CAS on metadata expectedOwnerId.
DECISION adr-002 — refunds post-COMMIT, idempotency keys throne:refund:ownership:<priorId> / throne:refund:loser:<sessionId>; failure -> refund_status=failed + 2xx; `npm run reconcile` + bounded sweep per webhook.
DECISION adr-003 — no price_history table; ownerships.paid_cents is the series; nextPrice(c)=floor((c*3+1)/2), integer only.
DECISION adr-004 — losing buyer: no ownership change, full auto-refund, event outcome='lost'.
DECISION adr-005 — raw pg + numbered .sql migrations, no ORM, parameterized only.
DECISION adr-006 — reject-at-write (http/https only, name 1-40) + escape-at-render + safeHref() + rel=noopener noreferrer nofollow + security headers.
RISK med — failed refund can sit until next purchase (mitigated: flag + log + reconcile script); serverless conn exhaustion (Pool max 3, pooled URL); no moderation (accepted).
RISK fyi — AC20 "three refunds" count is off by the setup flip; QA to assert ADR-004 invariant instead.
HANDOFF architect -> developer.
Gate PLAN: buildability folded into IMPLEMENT (greenfield, no legacy constraints); no open high-sev risk.
[2026-09-01T11:39:58] GATE phase=PLAN check=design-buildable result=pass note=
[2026-09-01T11:39:58] GATE phase=PLAN check=no-open-high-risk result=pass note=

[2026-09-01T11:39:58] STATUS phase: PLAN -> IMPLEMENT
[2026-09-01T11:40:27] SPAWN agent=requirements tally=1/12
[2026-09-01T11:40:28] SPAWN agent=architect tally=2/12
[2026-09-01T11:40:28] SPAWN agent=developer tally=3/12
[2026-09-01T11:40:28] SPAWN agent=qa-engineer tally=4/12

### TEST (qa-engineer, parallel w/ IMPLEMENT)
PROPOSE artifacts/test-plan.md — 47 cases (TC1-47), all 26 ACs, ADR-004 refund invariant, XSS/tamper/sk_live_ negatives, idempotent-redelivery + race recipes. 40 automatable.
RISK — flag AC20 literal "three refunds" vs ADR-004 formula; TC31 tests the formula not the literal count.
QUESTION fyi — no risk-register heading in design-doc.md; substituted ADR consequences + spec open-questions. Answered: acceptable, risk register was in architect's PLAN protocol messages not a doc section.

### IMPLEMENT (developer)
HANDOFF — built per design-doc + 6 ADRs. Gates green: tsc 0 errors, lint 0/0, npm test 15/15, npm run build succeeds w/ zero env vars (no-DB-at-build-time confirmed).
RISK low — no DB-backed integration tests for webhook/concurrency (AC10-16,19-21) in this sandbox (no live Postgres/Stripe creds); logic implemented per design's SQL/crash-matrix but only unit-tested indirectly. Recommend manual verify via README runbook + `stripe listen` before shipping, or a follow-up TEST_DATABASE_URL-gated suite.
Deviations (disclosed, accepted): node:test instead of vitest (per orchestrator instruction); lib/env.ts made lazy so build doesn't require env vars (necessary for AC — Next imports route modules during build static analysis); Stripe apiVersion pinned to installed SDK's default.
Files: package.json, db/migrations/001_init.sql, lib/{env,db,stripe,price,validate,types,throne,refunds}.ts, app/{layout,page,globals.css}, app/components/{TestModeBanner,OwnerCard,HistoryList,BuyForm}.tsx, app/api/checkout/route.ts, app/api/stripe/webhook/route.ts, scripts/{migrate,reconcile-refunds}.ts, tests/{price,validate}.test.ts, README.md, .env.example.
[2026-09-01T11:47:55] GATE phase=IMPLEMENT check=builds result=pass note=
[2026-09-01T11:47:55] GATE phase=IMPLEMENT check=self-tests result=pass note=

[2026-09-01T11:47:55] STATUS phase: IMPLEMENT -> REVIEW

### REVIEW (code-reviewer)
REVIEW verdict=approve. Matches design/ADRs exactly, no scope creep, no secrets, parameterized SQL, integer-cents verified, ADR-001/002/006 implemented as designed.
Nits (non-blocking): webhook route returns 500 (not 200+log) on missing payment_intent/amount_total edge case — retry-storm risk if it ever fires; loose type cast in reconcilePendingRefunds.

### REVIEW (security-reviewer)
REVIEW verdict=block (high, mitigable — no human gate, mitigation is concrete).
BLOCK SEC-04 high — AC19/20/21 (idempotency/race/single-current) have zero executable tests; ADR-006's claimed dangerouslySetInnerHTML grep test doesn't exist (AC26 unmet).
RISK SEC-01 med — checkout.session.async_payment_succeeded ignored, unpaid completed sessions dropped w/ no refund; payment_method_types not pinned to card so delayed methods reachable.
RISK SEC-02 med — lib/db.ts ssl:{rejectUnauthorized:false} on all non-localhost conns (prod!), MITM+cred capture; includes("localhost") spoofable.
CHALLENGE SEC-03 med — ADR-002 "can never double-refund" overstated: Stripe idempotency keys expire 24h; crash between refunds.create success and status UPDATE + late reconcile => real double refund.
RISK low batch — SEC-05 no amount_total vs expectedPriceCents check; SEC-06 reconcile missing AND NOT is_current guard; SEC-07 500 on malformed event causes retry storm (should be 200+log); SEC-08 String(err) leaks env var names to client; SEC-09 no rate limit on /api/checkout; SEC-10 postcss CVE transitive via next, build-time only, track don't force upgrade; SEC-11 no CSP (accepted, documented).
DECISION fyi — confirmed clean: webhook sig verify, TEST-mode gate real, zero SQLi surface, XSS defense real, no secrets in repo/bundle, no SSRF.
Convergence: security owns hard veto on high-sev; mitigations are concrete -> loop to developer, not human. Attempt 1.
[2026-09-01T11:54:44] LOOPBACK edge=REVIEW->IMPLEMENT issue=security-block-tests-and-money-safety attempt=initial build -> security block: missing invariant tests + payment/TLS/refund-idempotency gaps (same-issue 1/3, total 1/8)

### IMPLEMENT retry (developer, attempt 2 — after rate-limit interruption)
HANDOFF — all security fix-list items done, gate-verified. SEC-04 tests existed from interrupted attempt but had real bugs (pg-mem fake Pool sharing caused self-deadlock on concurrent tx; pg-mem's ON CONFLICT DO NOTHING RETURNING bug broke dedup) — fixed both, plus removed debug leftovers/stray scratch file from the interrupted run.
SEC-01/02/03/05/06/07/08 verified correct. SEC-09 rate limiter added (lib/rate-limit.ts, 10 req/60s IP-keyed). SEC-10 no action (accepted).
Gates: tsc 0 err, lint 0/0, npm test 19/19 (5x repeat, no flake), build green w/ zero env vars.
[2026-09-01T14:54:06] SPAWN agent=developer tally=5/12

### REVIEW retry (security-reviewer, mutation-tested)
REVIEW verdict=request-changes (med, not blocking). SEC-04 CLEARED via mutation testing (killed dedup->test1 fails, killed advisory lock->tests2/3 fail, injected dangerouslySetInnerHTML->grep test fails). Harness containment clean (pg-mem devDep only, zero refs from app/lib/scripts, no stray files). SEC-01/03/05/06/07/08/09 confirmed in code.
NOT CLEARED: SEC-02 only fixed in lib/db.ts — scripts/migrate.ts:14 still has `ssl: databaseUrl.includes("localhost") ? false : { rejectUnauthorized: false }` (spoofable host check + disabled cert verify on the prod-credentialed DDL runner). One-line fix: mirror lib/db.ts hostname-equality + rejectUnauthorized:true.
RISK fyi SEC-09 residual — clientIp() trusts first XFF header, spoofable; accepted for single-instance test-mode app.
RISK fyi SEC-10 unchanged — postcss transitive CVE via next, build-time only; accept, don't force next@16.
[2026-09-01T14:56:39] LOOPBACK edge=REVIEW->IMPLEMENT issue=security-block-tests-and-money-safety attempt=fix pass 2 -> SEC-04 cleared, SEC-02 residual in scripts/migrate.ts (same TLS issue, different file) (same-issue 2/3, total 2/8)
[2026-09-01T14:56:39] SPAWN agent=developer tally=6/12

### IMPLEMENT fix (orchestrator, mechanical one-liner)
Fixed scripts/migrate.ts SEC-02 residual — mirrored lib/db.ts: hostname-equality local check + rejectUnauthorized:true. Not delegated (trivial, no design judgment, mirrors already-security-approved pattern). Gates re-run: tsc 0 err, lint 0/0, npm test 19/19.
[2026-09-01T14:56:55] GATE phase=REVIEW check=approve result=pass note=
[2026-09-01T14:56:55] GATE phase=REVIEW check=no-blocking-security result=pass note=

[2026-09-01T14:56:56] STATUS phase: REVIEW -> TEST

### TEST (qa-engineer)
STATUS — automated regression full green: typecheck, lint, 19/19 tests, build w/ zero env vars, no-secrets-in-bundle scan. AC5,7,13,14,18(partial),19,20,21 covered by suite (cross-checked against test-plan.md).
RISK med — AC16 (refund-failure path) and AC22 (sk_test_ gate) implementation-inspected only, zero test execution; fake-stripe.ts has no forced-failure mode.
RISK low — AC18/TC28 automated coverage is static-grep proxy not rendered-DOM assertion; acceptable given no dangerous sink + React auto-escape.
STATUS blocking(to human, not agent) — 18/26 ACs need live Postgres+Stripe TEST account to verify (checkout amount, webhook sig, real refund, full runbook) — cannot run in this sandbox. Becomes the go-live manual-verification step.

### TEST follow-up (developer)
HANDOFF — test-only. Added AC16 (forced refund failure -> transfer commits, refund_status=failed, logged, 200, reconcile heals exactly once no double-refund) and AC22 (getEnv/assertTestMode throw pre-network on sk_live_/empty/unset key) coverage. 20->25 tests, 25/25 pass 3x, tsc/lint/build clean.
[2026-09-01T15:01:49] GATE phase=TEST check=acceptance-criteria result=pass note=
[2026-09-01T15:01:49] GATE phase=TEST check=regression-suite result=pass note=

[2026-09-01T15:01:49] STATUS phase: TEST -> DEPLOY
[2026-09-01T15:01:49] SPAWN agent=devops-engineer tally=7/12

### DEPLOY (devops-engineer)
HANDOFF — deploy-guide.md written, all steps human-executed (destructive_action gate). Covers git init, Vercel path (CLI or GitHub import), Postgres provisioning + migrate, 5 env vars, Stripe webhook registration, 4-step go-live verification runbook (covers the 18 sandbox-untestable ACs), rollback (Vercel instant promote-previous; confirmed 001_init.sql additive-only, no DB rollback needed), monitoring.
RISK low — npm run reconcile has no scheduler; stuck-refund window until manually run. Not launch-blocking; fast-follow candidate (Vercel Cron).
Nothing deployed/provisioned yet — pending human execution.
[2026-09-01T15:03:32] GATE phase=DEPLOY check=deploy-guide-exists result=pass note=
[2026-09-01T15:03:32] SPAWN agent=sre-observability tally=8/12

### Launch Review (security-reviewer + sre-observability, gate_owners_auto_roster)
Security/Privacy section: GO, no blocking. Regression spot-check clean (TLS fix confirmed in both lib/db.ts + scripts/migrate.ts, no dangerous sinks, secrets clean, all SQL parameterized, npm audit unchanged, 25/25). New SEC-12 low fyi — no PII retention/takedown path; runbook redaction UPDATE suggested, not blocking. PCI scope SAQ-A (Stripe-hosted Checkout, no cardholder data touches this app).
Ops section: GO, no blocking. Rollback confirmed-on-paper (Vercel instant promote, migrations additive-only verified). Heavyweight items correctly N/A at this scale (solo operator, test-mode). Sev-low follow-up: reconcile scheduler gap, not blocking.
VERDICT: GO. Prerequisite for any future live-key flip (separate gate): privacy notice, CSP, durable rate limiter, erasure path.
[2026-09-01T15:05:46] GATE phase=DEPLOY check=launch-review-go result=pass note=

[2026-09-01T15:05:46] STATUS phase: DEPLOY -> DOCUMENT
[2026-09-01T15:05:46] SPAWN agent=tech-writer tally=9/12

### DOCUMENT (tech-writer)
STATUS — README verified against artifacts. Fixed one drift: webhook events list only had checkout.session.completed, missing checkout.session.async_payment_succeeded (deploy-guide requires both). All other sections (mechanics, env vars, dev setup, limitations) confirmed accurate.
[2026-09-01T15:07:39] GATE phase=DOCUMENT check=docs-trace-to-artifacts result=pass note=

[2026-09-01T15:07:39] STATUS phase: DOCUMENT -> STABILIZE
[2026-09-01T15:07:39] SPAWN agent=verifier tally=10/12
[2026-09-01T15:10:41] VERIFY criterion=AC1 verdict=pass evidence=OwnerCard.tsx:11-30
[2026-09-01T15:10:41] VERIFY criterion=AC2 verdict=pass evidence=page.tsx:15, checkout/route.ts:41,55
[2026-09-01T15:10:41] VERIFY criterion=AC5 verdict=pass evidence=price.ts:9, price.test.ts:6-8
[2026-09-01T15:10:41] VERIFY criterion=AC10 verdict=pass evidence=webhook/route.ts:15-22
[2026-09-01T15:10:41] VERIFY criterion=AC16 verdict=pass evidence=refunds.ts:31-37, money-safety.test.ts test4
[2026-09-01T15:10:41] VERIFY criterion=AC19-21 verdict=pass evidence=throne.ts CAS+advisory lock, 001_init.sql partial unique index, money-safety.test.ts tests1-3
[2026-09-01T15:10:41] VERIFY criterion=AC22-26 verdict=pass evidence=env.ts, TestModeBanner, .next/static secret scan clean, 25/25 tests, build green zero-env
[2026-09-01T15:10:41] VERIFY criterion=AC8-9,13,15,25(live-verify) verdict=pass evidence=implemented per code inspection; requires stripe listen live run before shipping, environment constraint not defect

### STABILIZE (verifier)
REVIEW verdict=APPROVE (fresh, no war-room context). 21/26 ACs directly evidence-verified; 5 (AC8,9,13,15,25) implemented-per-inspection, need live Stripe/Postgres — environment constraint not defect, does not block approval per grading instruction. Anti-gaming checks clean (no eslint-disable/ts-ignore/as-any, strict tsconfig, tests exercise real route handler + real migration SQL through pg-mem, not reimplementations).
RISK non-blocking: SEED_PRICE_CENTS unvalidated (NaN if malformed); scripts/** unlinted (still typechecked); refunds.list() takes data[0] without amount/status match (fragile if a partial refund ever exists, not reachable today).
Live-fire gap: 5 ACs need `stripe listen` walkthrough before real launch — this is exactly deploy-guide.md step 6's manual verification runbook.

status: done
[2026-09-01T15:24:17] EPISODE closed verdict=verified close_revision=1
