# Launch Review — T-001 "Throne"

Pre-ship gate. Every item gets a check and an owner. N/A is a valid answer — written down, not assumed.

Reviewed at: 2026-09-01 · Scope: initial launch, Stripe TEST mode, no accounts.
Basis: deep security pass logged in `warroom.md` (`### REVIEW (security-reviewer)`,
`### REVIEW retry (security-reviewer, mutation-tested)`) + regression spot-check at gate time.

## Security

| # | Check | Verdict | Owner |
|---|---|---|---|
| S1 | [x] Authn/authz verified for every new surface (endpoint, queue, job, admin path) | **PASS (partial N/A)** — no accounts, no login, no admin path by design; nothing to authenticate. Both write surfaces are authorized by other means: `POST /api/stripe/webhook` is authenticated by Stripe HMAC signature verification (`constructEvent`, 400 on failure, verified before any DB/refund work); `POST /api/checkout` is intentionally public (it only creates a server-priced Stripe Checkout session — price is computed server-side from `nextPrice(current.paid_cents)`, never client-supplied) and is throttled by `lib/rate-limit.ts` (10 req/60s, IP-keyed). Scripts (`migrate`, `reconcile`) are operator-run CLI, not network-exposed. | security-reviewer |
| S2 | [x] Input validation on all new external inputs (params, payloads, headers, files) | **PASS** — `lib/validate.ts::parseBuyInput` is the single entry gate: name 1–40 chars + control-char reject; URL parsed via `new URL`, `http:`/`https:` allowlist, embedded-credential reject, 500-char cap, normalized `href` stored. Malformed JSON → 400. Webhook events are validated structurally (missing `payment_intent`/`amount_total` → 200 + log, not 500) and financially (`amount_total` must equal `metadata.expectedPriceCents`, else full idempotent refund + drop). `safeHref()` re-validates at render — DB is not treated as a trust boundary. Zero SQL injection surface: every statement parameterized (`$1`-style), no string interpolation into SQL, no ORM. No file uploads. | security-reviewer |
| S3 | [x] No secrets in code, config, or logs — scanned, not eyeballed | **PASS** — scanned for `sk_test_`/`sk_live_`/`whsec_`/credentialed Postgres URLs across `app/ lib/ scripts/ db/ README.md`: only placeholders in `.env.example`. No `.env` file present in tree; `.gitignore` covers `.env`, `.env.local`, `*.log` with `!.env.example`. All 16 `console.*` call sites reviewed — they log event/session/ownership IDs and error objects only, never secrets, never the Stripe key, never raw request bodies. SEC-08 fix holds: `/api/checkout` returns a static `GENERIC_ERROR` and logs server-side, so env var names no longer reach the client. Prior bundle scan for secrets was clean. | security-reviewer |
| S4 | [x] Dependency CVEs checked for new/updated packages | **PASS with accepted low (SEC-10)** — `npm audit` (prod and full) shows exactly 2 advisories, both the same transitive `postcss <=8.5.22` chain pulled in by `next`. npm labels it high, but reachability is nil for this app: postcss runs at build time over our own `app/globals.css`; there is no attacker-controlled CSS, no untrusted `sourceMappingURL`, and postcss ships no runtime code to the client. Fix requires `next@16` (breaking). **Accepted, not remediated** — see Accepted Risks. No other CVEs. | security-reviewer |
| S5 | [x] Threat notes written for any new attack surface | **PASS** — threat model captured across `adr-006-xss-url-hardening.md` (XSS / `javascript:` URL), `adr-001` (takeover race), `adr-002` (webhook-retry double-refund), `adr-004` (losing-buyer refund), and the SEC-01..SEC-11 finding set in `warroom.md`. Money-path threats specifically covered: signature forgery, event replay (`processed_events` PK + `ownerships_session_uniq`), concurrent takeover (`pg_advisory_xact_lock` + CAS on `expectedOwnerId` + partial unique index on `is_current`), price tampering (SEC-05 amount check), refund double-spend (stable idempotency keys + `refund_status` state machine + reconcile sweep). Live-key flip is explicitly out of scope and gated by `assertTestMode()` — a non-`sk_test_` key throws before any network call. | security-reviewer |

### Regression spot-check at gate time
All previously-closed findings re-verified, no drift:
- SEC-02 (TLS): both `lib/db.ts:11,20` and `scripts/migrate.ts:13,16` use hostname-equality local detection with `rejectUnauthorized: true` on remote. The spoofable `includes("localhost")` pattern is gone from the tree.
- SEC-01: `payment_method_types: ["card"]` pinned; `checkout.session.async_payment_succeeded` handled in the same `SETTLEMENT_EVENTS` path.
- SEC-05/06/07/08/09: all present in code as reviewed.
- XSS: zero `dangerouslySetInnerHTML` / `innerHTML` / `eval(` anywhere in `app/ lib/ scripts/`; `tests/no-dangerous-html.test.ts` enforces it (mutation-tested — injecting the sink fails the test).
- Suite green: 25/25 tests pass.

## Privacy / Data

| # | Check | Verdict | Owner |
|---|---|---|---|
| P1 | [x] PII inventory: what new personal data is collected, where it lands | **PASS** — Inventory is complete and small. Collected: (a) buyer-supplied `display_name` (1–40 chars) and (b) buyer-supplied `url` — both submitted for the express purpose of public display on the leaderboard, so they are public-by-intent, not sensitive PII. Landing: `ownerships.display_name`, `ownerships.url` in Postgres, plus a copy in Stripe Checkout Session `metadata`. Also stored: Stripe pseudonymous identifiers (`payment_intent_id`, `checkout_session_id`, `stripe_event_id`, `refund_id`) and integer cent amounts. **Not collected, not stored, never transits this app:** email, postal address, phone, card number, PAN, CVC, or any cardholder data — the payment form is Stripe-hosted Checkout, so card data goes buyer→Stripe directly. Stripe is the data controller for payment data. Caveat noted: `display_name` is free text, so a buyer *could* type their own real name — that is user-elected public disclosure, and it is why P2 matters. | security-reviewer |
| P2 | [~] Retention/deletion story exists for that data | **GAP — low severity, non-blocking (SEC-12)** — retention is currently "indefinite by design": the reign history is the product, and there is no delete endpoint, no admin UI, and no documented operator takedown procedure. For public-by-intent display names this is defensible, but there is no answer for "a buyer typed their real name / posted an abusive name / asks for removal." **Mitigation (fast-follow, not launch-blocking):** add a runbook line to `deploy-guide.md` giving the operator the exact statement — `UPDATE ownerships SET display_name='[removed]', url='https://example.invalid' WHERE id=$1;` (redact in place; do **not** `DELETE`, which would break the `prev_ownership_id` chain and the refund audit trail). Ships as a documented manual path; automate only if volume warrants. | security-reviewer |
| P3 | [x] Logging redacts PII and secrets on the new paths | **PASS** — audited all 16 `console.*` sites. Logs carry `eventId`, `sessionId`, `ownershipId`, `amountTotal`, `expectedPriceCents` and error objects. `display_name` and `url` are **never** logged on any path. No secrets, no raw request/webhook bodies, no stack traces returned to clients. One residual noted and accepted: `ownerships.refund_error` / `processed_events.error` persist raw Stripe error strings, which can embed Stripe object IDs — pseudonymous, no cardholder data, acceptable. | security-reviewer |
| P4 | [x] Compliance flags raised if applicable (GDPR/HIPAA/SOC2/contractual) | **PASS (largely N/A)** — HIPAA N/A (no health data). SOC2 N/A (no such commitment on this app). PCI-DSS: scope minimized to **SAQ A** territory — Stripe-hosted Checkout means no cardholder data touches this app's servers, code, or database; there is nothing here to descope further. GDPR: minimal but non-zero exposure — `display_name`/`url` can be personal data if a buyer elects to make them so. There is no privacy policy, no cookie banner, and no erasure mechanism (see P2); acceptable for a TEST-mode launch with no real charges and no marketing, and it is the correct place to start if this ever flips to live keys. **Compliance flag raised for the live-key gate, not for this launch:** before any `sk_live_` flip, a privacy notice + the P2 erasure path should exist. | security-reviewer |

## Operational Readiness

*Not my section — owned by devops/SRE. Left unfilled deliberately.*

| Check | Owner |
|---|---|
| [ ] Rollback tested — not just written down | |
| [ ] Alerts + dashboards cover the new failure modes | |
| [ ] Runbook entry: what breaks, how it looks, what to do | |
| [ ] SLO impact assessed (latency, error budget, capacity) | |
| [ ] Feature flag / kill switch in place for risky paths | |
| [ ] On-call informed of the change and its blast radius | |

## Accepted Risks (security + privacy, all low severity, none blocking)

| ID | Risk | Why accepted | Follow-up |
|---|---|---|---|
| SEC-09 | `clientIp()` trusts the first `X-Forwarded-For` value; spoofable, so the rate limiter is evadable. Limiter is also in-memory, so it does not survive cold starts or span instances. | Threat model is a single-instance, TEST-mode app with no real money at stake; the limiter is a speed bump, not a control. Cost of a real limiter exceeds the risk today. | If traffic or live keys arrive: move to Upstash/Redis keyed on the platform-verified client IP. |
| SEC-10 | `postcss` transitive CVE chain via `next` (npm severity high). | Build-time only, operates on first-party CSS, no attacker-controlled input, no client runtime component. Fix is a breaking `next@16` major. | Track; adopt `next@16` on the normal upgrade cycle, not as a hotfix. |
| SEC-11 | No Content-Security-Policy header. | Other headers are set (`nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy`); no dangerous sink exists (zero `dangerouslySetInnerHTML`, React auto-escaping, URL allowlist), so CSP would be defence-in-depth on an already-closed vector. Documented and accepted at design time. | Add a CSP before live-key flip. |
| SEC-12 | No data retention limit and no deletion/takedown path (P2). | Public-by-intent data, TEST mode, no real buyers yet. | Add the redaction runbook line to `deploy-guide.md` — fast-follow, human-approved. |

## Verdict — Security + Privacy sections only

| Verdict | Blocking items | Sign-off |
|---|---|---|
| **GO** | none — S1–S5 pass, P1/P3/P4 pass, P2 is a low-severity documented gap (SEC-12) shipping with an explicit follow-up | security-reviewer, 2026-09-01 |

No high-severity findings remain open; the security veto is **not** exercised.
All four accepted risks are low severity, explicitly documented, and carry named follow-ups.

**Two conditions attached (neither blocks this launch):**
1. SEC-12 redaction runbook line lands in `deploy-guide.md` as a fast-follow.
2. The `sk_live_` flip is a **separate security gate**, not covered by this sign-off. Before it: privacy notice, CSP (SEC-11), durable rate limiter (SEC-09), and the erasure path (SEC-12) must all be in place. `assertTestMode()` enforces this today by throwing on any non-`sk_test_` key.

Overall launch verdict is not mine to give — it depends on Operational Readiness, still unfilled.
