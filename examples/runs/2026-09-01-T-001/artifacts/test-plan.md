# Test Plan — T-001 "Throne"

Source: task-spec.md (26 ACs), adr-004-losing-buyer-auto-refund.md. Derived from spec only; no
implementation code was read.

## Global test fixtures
- **Stripe TEST mode** account, `STRIPE_SECRET_KEY=sk_test_...`, `STRIPE_WEBHOOK_SECRET` from
  `stripe listen`.
- Local: `stripe listen --forward-to localhost:3000/api/stripe/webhook` running throughout.
- DB: fresh Postgres schema per test run (migration + seed), or truncate `ownerships` /
  `processed_events` between cases.
- Test card: `4242 4242 4242 4242`, any future exp, any CVC.
- Helper `stripe trigger checkout.session.completed --add checkout_session:metadata.displayName=...`
  is NOT sufficient alone for money-accurate cases (it doesn't let us control amount/prior owner
  linkage) — for AC11–AC21 drive events by actually completing real TEST-mode Checkout Sessions via
  Stripe's hosted page (Playwright or manual), then capture the real webhook. Use `stripe trigger`
  only for generic delivery/signature/idempotency-plumbing cases (AC10, AC12 unknown-event path).

## Case table

| # | AC | Category | Preconditions | Action | Expected | How to observe | Type | Auto? | Pri |
|---|---|---|---|---|---|---|---|---|---|
| TC1 | AC1 | happy | Current owner exists (name "Ada", url `https://ada.dev`, paid 150) | `GET /` | Page shows "Ada", link `href="https://ada.dev"` with `rel="noopener noreferrer nofollow"` `target="_blank"`, "$1.50" | curl + HTML assert / Playwright DOM query | integration | yes | P0 |
| TC2 | AC1 | boundary | owner paid 1 cent | `GET /` | displays "$0.01" not "$0.010" or "$.01" | curl+assert | integration | yes | P1 |
| TC3 | AC2 | happy | current_owner_paid_cents=150 | `GET /` | buy price shown = ceil(150*1.5)=225 ("$2.25") and Checkout session amount = 225 | curl page + inspect created Checkout Session `amount_total`/`unit_amount` via Stripe API | integration | yes | P0 |
| TC4 | AC2 | boundary | current_owner_paid_cents=101 (odd, forces rounding) | compute expected via ceil(101*1.5)=152 | page price == Checkout amount == 152 | same as above | integration | yes | P0 |
| TC5 | AC3 | happy | empty DB (genesis, no ownerships rows) | `GET /` | "vacant/unowned" state rendered; buy price == `SEED_PRICE_CENTS` (default 100) | curl+assert | integration | yes | P0 |
| TC6 | AC3 | boundary | `SEED_PRICE_CENTS=500` env override, empty DB | `GET /` | buy price == 500 | curl+assert | integration | yes | P1 |
| TC7 | AC4 | happy | owner change occurs between two loads | `GET /` twice, with a completed takeover in between | second response shows new owner; no caching headers serve stale data (`Cache-Control` absent/no-store, or Next `revalidate=0`) | two sequential curls, diff bodies + check response headers | integration | yes | P0 |
| TC8 | AC5 | happy/boundary | none | unit-call `nextPrice(100)`, `nextPrice(150)`, `nextPrice(225)` | returns 150, 225, 338 respectively; function returns integer type | `node:test` assertEqual | unit | yes | P0 |
| TC9 | AC5 | negative | none | inspect stored/transmitted price representations | no `number` with decimals or float currency anywhere (grep DB column type is integer, API payload has integer cents) | schema check + response body type assert | unit/integration | yes | P1 |
| TC10 | AC6 | negative | current price computed server-side = 225 | `POST /api/checkout` with tampered `amount`/`priceCents` field in body claiming 1 | server ignores client amount; created Checkout Session amount == 225 (server truth), or request rejected 400 | inspect Stripe Session via API + response code | integration | yes | P0 |
| TC11 | AC7 | negative | none | `POST /api/checkout` with `displayName=""` (or 41+ chars, see TC24/25) | 400 with field-level error `{field:"displayName", ...}`; assert no Stripe session created (list sessions, none new) | curl + Stripe API session list diff | integration | yes | P0 |
| TC12 | AC7 | negative | none | `POST /api/checkout` with `url="not a url"` | 400 field error; no session created | curl + Stripe session list | integration | yes | P0 |
| TC13 | AC7 | negative | none | `POST /api/checkout` with `url="ftp://x.com"` | 400 (scheme must be http/https) | curl | integration | yes | P1 |
| TC14 | AC7 | boundary | none | `displayName` exactly 40 chars (after trim) | 200 accepted | curl | integration | yes | P1 |
| TC15 | AC8 | happy | valid body | `POST /api/checkout` | 200 with a Stripe Checkout Session URL in TEST mode; session metadata contains `displayName`, `url`, `expectedPriceCents`, `expectedOwnerId` matching server state | curl response + `stripe.checkout.sessions.retrieve` and inspect `.metadata` | integration | yes | P0 |
| TC16 | AC9 | negative | webhook forwarding disabled (`stripe listen` NOT running / endpoint returns non-2xx deliberately) | complete Checkout with test card, land on success URL | `GET /` still shows OLD owner (no state change from redirect alone) | manual: complete real Checkout in browser with webhook forwarder stopped, then curl `/` | integration | manual | P0 |
| TC17 | AC10 | negative | webhook listener up | POST to `/api/stripe/webhook` with valid JSON body but no `Stripe-Signature` header | 400; DB unchanged (row counts before/after equal) | curl raw POST + SQL count `ownerships`/`processed_events` before/after | integration | yes | P0 |
| TC18 | AC10 | negative | webhook listener up | POST with `Stripe-Signature` header present but signature computed against a *different* body (tampered payload after signing) | 400; DB unchanged | curl with forged signature + SQL count diff | integration | yes | P0 |
| TC19 | AC10 | happy | `stripe listen` running, forwards to real endpoint | `stripe trigger checkout.session.completed` (or real completed checkout) | signature verifies, 2xx | `stripe listen` terminal log shows delivery + 200 | integration | yes | P1 |
| TC20 | AC11 | happy | prior owner exists (paid 150, is_current=true) | complete real Checkout for new buyer at server price 225, webhook delivered once | single TX: new `ownerships` row inserted `is_current=true, paid_cents=` actual `amount_total`; prior row `is_current=false, ended_at` set; history entry present | SQL: `SELECT * FROM ownerships ORDER BY started_at DESC` — assert row shapes and timestamps; `GET /` reflects new owner | integration | yes | P0 |
| TC21 | AC12 | happy | webhook up | `stripe trigger payment_intent.created` (an event type app doesn't handle) | webhook returns 2xx; no DB mutation | curl/stripe log + SQL diff | integration | yes | P1 |
| TC22 | AC12 | negative(dup) | an already-processed `checkout.session.completed` event id exists in `processed_events` | redeliver identical event (Stripe CLI resend or `stripe events resend <id>`) — see TC30 | 2xx returned, never 5xx, no additional mutation | curl / stripe log status code + SQL diff | integration | yes | P0 |
| TC23 | AC13 | happy | prior owner exists, `payment_intent_id=pi_X`, `paid_cents=150` | new buyer completes checkout, webhook processes | Stripe refund created for exactly `pi_X` amount 150; house margin = newPrice-150 | `stripe refunds list --payment-intent pi_X` (or Stripe API/dashboard) — exactly one refund, amount 150 | integration | yes | P0 |
| TC24 | AC14 | happy | genesis (no prior owner) | first-ever buyer completes checkout | no refund attempted; no error thrown/logged; webhook 2xx; `refund_status` field on new row is null/n-a | `stripe refunds list` — zero refunds; check response 2xx; check app logs for errors | integration | yes | P0 |
| TC25 | AC15 | negative(idempotency) | takeover already processed once, refund already issued | **redeliver same webhook event** (Stripe CLI: capture event id from `stripe listen` log, then `stripe events resend <evt_id>`, or replay same signed payload via curl) | at most one refund exists for that prior-owner's `payment_intent_id`; second delivery does not create a second refund; response 2xx | `stripe refunds list --payment-intent pi_X` → count==1 after redelivery | integration | yes | P0 |
| TC26 | AC16 | negative(failure-mode) | prior owner's `payment_intent_id` is deliberately invalid/uncapturable (e.g. use a PI from a different currency, or a canceled/refunded-already PI to force API error) so `stripe.refunds.create` throws | webhook delivered | ownership transfer STILL commits (new owner is current, history row exists); prior owner row `refund_status='failed'` with error text recorded; webhook still returns 2xx | SQL check `ownerships.refund_status='failed'` + error column populated; curl webhook response code == 2xx; confirm no Stripe retry storm (single delivery in `stripe listen` log) | integration | yes | P0 |
| TC27 | AC17 | happy | N=3 successful sequential takeovers performed | `GET /` | history section lists exactly 3 entries, reverse-chronological, each with name/link/price/start+end (current entry has no end, visually marked) | Playwright DOM query counting list items + order assertion | integration | yes | P0 |
| TC28 | AC18 | negative(xss) | none | `POST /api/checkout` with `displayName="<script>alert(1)</script>"` | rejected 400, OR accepted but rendered as literal escaped text (`&lt;script&gt;`) — never executed | curl body + if accepted, Playwright: load page, assert no `alert` dialog fires, assert DOM textContent (not innerHTML) shows escaped string | integration | yes | P0 |
| TC29 | AC18 | negative(xss) | none | `POST /api/checkout` with `url="javascript:alert(1)"` | rejected 400 (fails AC7 URL scheme check) OR if somehow stored, rendered `href` is never `javascript:` (stripped/neutralized) | curl + if rendered, assert `<a href>` does not start with `javascript:` | integration | yes | P0 |
| TC30 | AC19 | negative(idempotency) | none processed yet | deliver identical `checkout.session.completed` event **twice** in sequence (same event id) via `stripe listen` + manual resend, or two curls with identical signed body/timestamp | exactly one ownership change, one history row, one refund total (not two) | SQL count `ownerships` rows + `processed_events` unique constraint + `stripe refunds list` count | integration | yes | P0 |
| TC31 | AC20/ADR-004 | concurrency/race | one current owner (incumbent) at price P; two buyers B1,B2 each independently create Checkout Sessions at price P against same `expectedOwnerId`, both pay | exactly one of {B1,B2} becomes current owner with a new `ownerships` row + history entry; the loser gets NO `ownerships` row and is fully refunded their own charge; incumbent refunded exactly once; **no double-refund of incumbent** | fire both completed-checkout webhooks concurrently (see below); then assert the ADR-004 invariant (not literal "3 refunds" — see Note A) | integration | yes | P0 |
| TC32 | AC21 | concurrency | none | fire 10 parallel purchase webhooks (10 distinct buyers, sequential prices each computed against the DB price at request time, OR same race pattern repeated) against the running app | at most one row has `is_current=true` at all times (DB partial unique index enforced) — no window where 0 or 2+ | run a concurrent polling SQL query during the burst: `SELECT count(*) FROM ownerships WHERE is_current=true` must never exceed 1; also assert final state count==1 | integration | yes | P0 |
| TC33 | AC22 | negative | `STRIPE_SECRET_KEY=sk_live_xxx` (or malformed) set in env | boot app / call `POST /api/checkout` | app refuses to boot, OR endpoint returns 500 with clear message referencing test-mode requirement | process exit code / log grep, or curl 500 + body text assert | integration | yes | P0 |
| TC34 | AC23 | happy | any state | `GET /` | visible "TEST MODE — no real money" banner present in DOM; README documents card `4242 4242 4242 4242` | Playwright DOM text assert + grep README.md | integration+manual | partial | P1 |
| TC35 | AC24 | negative | none | build client bundle (`npm run build`), grep output `.next/static` for secret patterns | no `sk_test_`/`sk_live_`/`whsec_` substrings found in any client-shipped JS; `.env.example` has exactly the 5 documented keys with placeholder (non-real) values | `grep -r "sk_" .next/static` returns empty; `cat .env.example` inspection | build/static | yes | P0 |
| TC36 | AC24 | negative | git repo present | scan repo files (not `.env`) for secret-looking strings | no committed real secret values | `git grep -nE "sk_(test|live)_[A-Za-z0-9]{10,}"` on tracked files → empty | static | yes | P1 |
| TC37 | AC25 | happy(e2e) | clean clone, empty DB | follow README runbook exactly: install, env, migrate/seed, `npm run dev`, `stripe listen`, complete genesis purchase, complete one takeover with refund | every documented step succeeds as written; end state = 1 owner, 1 refund issued, page reflects it | manual full run-through, tick off each README step | manual e2e | manual | P0 |
| TC38 | AC26 | happy | none | `npm run build`; `npm test` (or configured test runner) | build exits 0, no type errors; automated suite (price math + webhook handler + concurrency) passes | CI/local command exit codes | build/CI | yes | P0 |

## Additional negative/edge cases (spec-driven, not 1:1 with a single AC — mapped to nearest)

| # | AC | Category | Preconditions | Action | Expected | How to observe | Type | Auto? | Pri |
|---|---|---|---|---|---|---|---|---|---|
| TC39 | AC7 | boundary | none | `displayName` = 41 chars (one over limit, after trim) | 400 field error | curl | integration | yes | P0 |
| TC40 | AC7 | boundary | none | `displayName` = " Ada " (leading/trailing spaces, trims to 3 chars) | trimmed length used for 1–40 check; accepted, stored trimmed | curl + SQL check stored value has no leading/trailing space | integration | yes | P2 |
| TC41 | AC7/AC18 | negative | none | `displayName` containing control characters (e.g. `\x00`, `\x1b[31m`, `\n`) | rejected 400, or stripped/sanitized before storage/render — never passed through raw to DB/HTML | curl + if accepted, SQL + rendered HTML byte inspection | integration | yes | P1 |
| TC42 | AC10 | negative | none | POST webhook with `Stripe-Signature` header containing a well-formed but wrong-secret signature (signed with a different webhook secret) | 400, no mutation | curl + SQL diff | integration | yes | P0 |
| TC43 | AC10 | negative | none | POST webhook with body byte-for-byte tampered after Stripe's original signature (classic "tampered webhook body" case: take a real captured signed request, flip one char in the JSON, keep old signature header) | 400 (signature mismatch since raw body no longer matches), no mutation | capture real webhook via `stripe listen --print-json`, mutate body, replay with curl using original header + SQL diff | integration | yes | P0 |
| TC44 | AC16 | negative(failure-mode) | Stripe refund API deliberately made to fail (see TC26) — repeat with retry path | after TC26's failed state, run the reconcile/retry mechanism (manual re-invoke or job) | refund succeeds on retry without creating a duplicate if it had partially succeeded (idempotency key reused); `refund_status` transitions to succeeded | SQL check `refund_status` before/after retry + `stripe refunds list` count stays 1 | integration | yes | P1 |
| TC45 | AC6 | negative | none | `POST /api/checkout` with negative or zero `amount`/extra unexpected fields injected in body | server ignores client-sent price entirely regardless of value/shape; computed price unaffected | curl + inspect created session amount | integration | yes | P2 |
| TC46 | ADR-004 | negative | race loser scenario (TC31) | after the race, attempt to find the loser in `/` history list | loser NEVER appears in `GET /` history (no `ownerships` row for them at all) | Playwright DOM query — loser's display name absent from history list | integration | yes | P0 |
| TC47 | AC22 | boundary | `STRIPE_SECRET_KEY` unset entirely | boot / call checkout | same as AC22: refuse to boot or 500 with clear message (empty string does not start with `sk_test_`) | same as TC33 | integration | yes | P1 |

## Stripe CLI recipes

**Listen (run for entire session):**
```
stripe listen --forward-to localhost:3000/api/stripe/webhook --print-json
```
Capture the `whsec_...` it prints into `STRIPE_WEBHOOK_SECRET`.

**Genesis + takeover happy path (manual, backs TC20/TC23/TC37):**
```
# 1. POST /api/checkout with valid body -> get Checkout URL
# 2. Open URL, pay with 4242 4242 4242 4242
# 3. stripe listen delivers checkout.session.completed automatically
```

**Redelivery for idempotency (TC22, TC25, TC30):**
```
# From the stripe listen log, note the delivered event id evt_XXXX
stripe events resend evt_XXXX
# or, replay the exact signed request Stripe sent (capture raw body + Stripe-Signature
# header via --print-json / a local proxy) and curl it again unmodified
```

**Untyped/irrelevant event for AC12 (TC21):**
```
stripe trigger payment_intent.created
```

**Concurrency race (TC31, TC32):** cannot rely on `stripe trigger` (no control over metadata/two
sessions vs one owner). Drive it programmatically:
```js
// pseudo, node:test — create two real TEST checkout sessions against the SAME expectedOwnerId,
// simulate both completing, then fire both signed webhook POSTs concurrently with Promise.all
const [r1, r2] = await Promise.all([
  fetch('/api/stripe/webhook', { method: 'POST', headers: sigHeaders(bodyA), body: bodyA }),
  fetch('/api/stripe/webhook', { method: 'POST', headers: sigHeaders(bodyB), body: bodyB }),
]);
```
Sign both bodies locally with `stripe.webhooks.generateTestHeaderString` (or CLI equivalent) using
the real `STRIPE_WEBHOOK_SECRET` and realistic `checkout.session.completed` payloads referencing two
distinct real (or synthetically valid) PaymentIntents, so refund calls are real Stripe TEST API
calls against real objects — this is required to actually validate AC13/AC15/ADR-004 refund counts.

**Tampered body (TC43):**
```
# capture real delivery, then curl with body mutated but old signature header kept
curl -X POST localhost:3000/api/stripe/webhook \
  -H "Stripe-Signature: t=...,v1=..." \
  --data-binary @tampered-body.json
```

## Note A — AC20's "three total refunds" vs the ADR-004 invariant

AC20 literally says: "assert one owner, three total refunds accounted for, and consistent DB state."
That literal count is scenario-specific (it presumes some particular refund history baseline) and is
**not** the general invariant to test against, per ADR-004's explicit correction:

> "Refund accounting invariant (asserted by the concurrency test): exactly one refund per ended
> `ownerships` row, plus exactly one refund per `outcome='lost'` event, and no others."

TC31 therefore asserts the ADR-004 formula, not the literal "3":
```sql
-- refund_count_expected = (# ended ownerships rows) + (# processed_events WHERE outcome='lost')
SELECT
  (SELECT count(*) FROM ownerships WHERE ended_at IS NOT NULL) +
  (SELECT count(*) FROM processed_events WHERE outcome = 'lost') AS expected_refunds;
```
Cross-check this number against the actual Stripe refunds issued (`stripe refunds list`, filtered to
PaymentIntents involved in the test) — counts must match exactly, and no PaymentIntent should have
more than one refund. This is flagged as a spec/ADR discrepancy — see RISK below.

## Automatable (node:test / integration harness) vs Manual

**Automatable:** TC1–TC15, TC17–TC33, TC35–TC36, TC38–TC47 (unit price math, HTTP/webhook
integration tests against a real TEST-mode Stripe account + ephemeral Postgres, DOM assertions via
Playwright/JSDOM for XSS/banner/history rendering).

**Manual / not practically automatable:**
- TC16 (visually confirming redirect-only behavior with webhook forwarder deliberately down — can be
  scripted but is commonly run manually once as a sanity check).
- TC34 (banner + README doc check) — partially automatable (DOM banner text yes; README prose
  review is manual).
- TC37 (full README runbook walkthrough) — inherently manual, it's validating documentation/DX, not
  code behavior.

## Coverage
- [x] Every acceptance criterion (AC1–AC26) has ≥1 test case above.
- [x] Untestable criteria: none — all 26 ACs are testable as written.
- [x] ADR-004 refund invariant covered (TC31, TC46, Note A) in addition to AC20/AC21 literal text.
- [x] Risk register: design-doc.md not present in artifacts directory at plan time — see QUESTION
  below; risks captured here are drawn from spec's "Open questions" and ADR-004's Consequences
  (loser invisibility, refund settlement window) as TC31/TC46 and general failure-mode coverage
  (TC26, TC44).
