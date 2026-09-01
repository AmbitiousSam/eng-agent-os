# Task Spec — T-001: Throne — single-page "king of the internet" flip app

**Goal:** Ship a one-page web app where a single "throne" is owned by one person at a time, and anyone can buy it from the current owner for 1.5x the owner's paid price, with the prior owner refunded their original amount and the house keeping the 0.5x spread.

**Scope:**
- One public page: current owner (display name, link, amount paid), current buy price, buy button, and a full ownership history.
- Stripe Checkout (TEST mode) for the purchase; Stripe webhook drives all state changes.
- Automatic Stripe refund of the previous owner's original PaymentIntent on successful takeover.
- Postgres persistence (`DATABASE_URL`) of throne state + owner history + payment records.
- Genesis/seed state so the first purchase has a defined price.
- Deployable to Vercel today; README with env vars + Stripe webhook setup steps.

**Out of scope:**
- User accounts, login, sessions, profiles, password reset.
- Stripe Connect, payouts, transfers, marketplace/destination charges.
- Live/production Stripe keys or real money.
- Admin UI, moderation queue, content review of names/URLs beyond basic validation.
- Email/notifications, analytics, SEO work, mobile app, i18n.
- Bidding, auctions, timers, decay, or any pricing rule other than fixed 1.5x.
- Refund-failure back-office tooling beyond logging + a flagged DB row.

## Acceptance criteria (testable)

**Display / read path**
- [ ] AC1: `GET /` renders the current owner's display name, their URL as a clickable link (`rel="noopener noreferrer nofollow"`, `target="_blank"`), and the exact amount they paid formatted as currency.
- [ ] AC2: `GET /` renders the current buy price equal to `ceil(current_owner_paid_cents * 1.5)` in cents, and this same value is what Checkout charges.
- [ ] AC3: When no one has ever owned the throne (genesis), the page shows an "unowned / vacant" state and the buy price equals the configured seed price (`SEED_PRICE_CENTS`, default 100 = $1.00).
- [ ] AC4: The page is server-rendered fresh (no stale cache): two sequential loads after an ownership change show the new owner, i.e. the route is dynamic / `revalidate = 0`.

**Price math**
- [ ] AC5: Price is computed in integer cents only; unit test asserts `nextPrice(100)=150`, `nextPrice(150)=225`, `nextPrice(225)=338` (round-half-up/ceil documented and consistent), and no floating-point currency is stored or transmitted.
- [ ] AC6: The server recomputes the price from the DB at Checkout-session creation time and never trusts a client-supplied amount; a request posting a tampered amount is charged the server-computed price (or rejected 400).

**Checkout**
- [ ] AC7: `POST /api/checkout` with `{displayName, url}` validates input (name 1–40 chars after trim; URL must parse and be `http://` or `https://`) and returns 400 with a field-level error otherwise; no Stripe session is created on invalid input.
- [ ] AC8: A valid `POST /api/checkout` creates a Stripe Checkout Session in TEST mode for the server-computed price and returns its URL; the session carries metadata `{displayName, url, expectedPriceCents, expectedOwnerId}`.
- [ ] AC9: Ownership does NOT change on redirect back to the success URL alone — with the webhook suppressed, completing checkout leaves the page showing the old owner.

**Webhook-driven transfer**
- [ ] AC10: `POST /api/stripe/webhook` verifies the Stripe signature using `STRIPE_WEBHOOK_SECRET` against the raw request body; an invalid/absent signature returns 400 and mutates nothing.
- [ ] AC11: On a verified `checkout.session.completed`, within one DB transaction: the new owner row is inserted, becomes current owner with `paid_cents` = amount actually charged, the previous owner is marked ended with an end timestamp, and a history entry is recorded.
- [ ] AC12: The webhook returns 2xx for events it does not handle and for events it has already processed, and never 5xx on duplicate delivery.

**Refund of prior owner**
- [ ] AC13: On a successful takeover with a prior owner, a Stripe refund is issued for exactly the prior owner's `paid_cents` against the prior owner's stored `payment_intent_id`; house retains `newPrice - priorPaid` (= 0.5x prior paid).
- [ ] AC14: Genesis purchase (no prior owner) issues no refund and errors nowhere.
- [ ] AC15: The refund call is idempotent (Stripe `Idempotency-Key` derived from the prior ownership row id); replaying the same webhook event issues at most one refund, verifiable via the Stripe test dashboard / API listing exactly one refund.
- [ ] AC16: If the refund API call fails, ownership transfer is still committed, the prior owner's row is marked `refund_status='failed'` with the error recorded, and the failure is logged — the webhook still returns 2xx (no infinite Stripe retry loop). A retry path (manual or job) can re-attempt without double-refunding.

**History**
- [ ] AC17: The page lists all past owners in reverse-chronological order with name, link, price paid, and reign start/end timestamps; after N successful purchases the list has N entries (including the current reign, visually distinguished).
- [ ] AC18: All user-supplied name/URL text is rendered escaped; a submission containing `<script>alert(1)</script>` or a `javascript:` URL is either rejected at validation or rendered inert (no script execution, no `javascript:` href).

**Idempotency / concurrency**
- [ ] AC19: Processed Stripe event ids are persisted uniquely; delivering the same `checkout.session.completed` event twice results in exactly one ownership change, one history row, and one refund.
- [ ] AC20: Two concurrent webhooks for two sessions both created at price P against the same owner: exactly one succeeds in taking the throne; the loser is detected via a compare-and-set on the expected current-owner id (or `SELECT … FOR UPDATE`) and is fully refunded its own charge, with no history row and no double-refund of the original owner. Test: fire both webhooks in parallel and assert one owner, three total refunds accounted for, and consistent DB state.
- [ ] AC21: A concurrency test asserts the invariant "at most one row has `is_current = true`" holds after 10 parallel purchase webhooks (DB-level partial unique index enforces it).

**Test-mode safety**
- [ ] AC22: App refuses to boot (or the checkout endpoint returns 500 with a clear message) if `STRIPE_SECRET_KEY` does not start with `sk_test_`.
- [ ] AC23: The UI displays a visible "TEST MODE — no real money" banner, and the README documents the Stripe test card `4242 4242 4242 4242`.
- [ ] AC24: No secret keys or webhook secrets appear in client bundles or in the repo; `.env.example` lists `DATABASE_URL`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `NEXT_PUBLIC_BASE_URL`, `SEED_PRICE_CENTS` with placeholder values only.

**Ship-ability**
- [ ] AC25: From a clean clone: `npm install`, set `.env`, run migration/seed, `npm run dev`, and complete a full genesis purchase + one takeover with refund using `stripe listen` — documented in the README as a step-by-step runbook.
- [ ] AC26: `npm run build` succeeds with no type errors, and the automated test suite (unit price math + webhook handler + concurrency) passes.

## Assumptions
1. **Refund mechanism** (orchestrator-decided): prior owner is made whole via a Stripe *refund* of their original PaymentIntent. No Stripe Connect, no payouts, no KYC. House keeps the 0.5x spread as ordinary revenue.
2. **Stack** (orchestrator-decided): Next.js App Router (TypeScript), Postgres via `DATABASE_URL`, Stripe Checkout + webhook, deploy target Vercel.
3. **Stripe TEST mode only.** Going live is a separate, human-gated task.
4. **Genesis:** throne starts unowned; first buy price = `SEED_PRICE_CENTS`, default 100 ($1.00 USD).
5. **Buyer identity:** display name + URL, collected before redirect to Checkout, carried in session metadata. No accounts, no login, no email capture beyond what Stripe collects.
6. **Currency:** USD, integer cents throughout.
7. **Rounding:** `nextPrice = ceil(paid * 1.5)` — deterministic, always strictly increasing, never under-charges.
8. **Money truth lives in Stripe; the DB is the ownership ledger.** Amount recorded is `amount_total` from the completed session, not the requested price.
9. **Concurrency loser policy:** if two people pay simultaneously, first webhook committed wins; the loser is auto-refunded in full and never appears in history. Chosen over "highest price wins" because both sessions are created at the same price, so first-commit is the only fair, race-free rule.
10. **Refund failure policy:** transfer commits, refund marked failed and logged. Rationale: the throne must not be left in a half-transferred state; an un-refunded prior owner is a recoverable bookkeeping issue.
11. **Working directory:** the human wrote `~/Downloads/project2/`; the actual empty directory provided is `~/Downloads/project-2`. Building in `~/Downloads/project-2` (hyphenated). Trivially movable.
12. **Directory is empty / greenfield** — no existing conventions to honor; conventions are set by this task.
13. **No content moderation.** Names and URLs are shown as submitted (escaped). Acceptable at this scale; noted as a risk.
14. **No refunds/disputes UI, no chargeback handling.** Out of scope for day one.
15. **Data model sketch (non-binding, architect owns final):** `throne_state` (singleton) or derive current from `ownerships(is_current)`; `ownerships(id, display_name, url, paid_cents, payment_intent_id, checkout_session_id, stripe_event_id, started_at, ended_at, is_current, refund_status, refund_id)`; `processed_events(event_id PK)`.

## Classification
- kind: feature (greenfield app)
- greenfield: true
- complexity: standard — small surface area (one page, two endpoints) but real-money-shaped correctness: webhook idempotency, refunds, and a genuine race condition make this more than a CRUD app.
- signals: [payments, stripe, webhooks, money-handling, idempotency, concurrency, public-api, external-input, xss-surface, db-migration, deploy, greenfield, time-pressure]

## Open questions
- [fyi] Directory name mismatch (`project2` in the ask vs `project-2` provided). Proceeding in `~/Downloads/project-2`.
- [fyi] Currency assumed USD and seed price assumed $1.00. Both are single-constant changes.
- [fyi] "Put it live today" — this spec delivers a Vercel-deployable app in Stripe TEST mode. Switching to live keys requires a separate human-gated decision (real money, refund liability, no moderation).
- [fyi] No moderation on the displayed name/link means the throne can be claimed with offensive content or a hostile link. Mitigated only by escaping + `nofollow`. Flag if unacceptable.
- [fyi] Price grows 1.5x per flip; after ~15 flips from $1 it exceeds $400 and Stripe/card limits eventually bite. No cap implemented.
