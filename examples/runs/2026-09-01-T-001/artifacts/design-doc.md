# Design — T-001: Throne — single-page "king of the internet" flip app

**Approach (1 paragraph):** One Next.js App Router project, TypeScript, no ORM, no queue, no cron,
no admin UI. Postgres holds a single append-mostly `ownerships` ledger where the current king is the
one row with `is_current = true` (enforced by a partial unique index, AC21), plus a `processed_events`
table keyed by Stripe event id (AC19). All state changes happen in exactly one place: the
`checkout.session.completed` webhook. That handler takes a transaction-scoped Postgres advisory lock
(serializes takeovers *including* the genesis case where there is no row to `FOR UPDATE`), does a
compare-and-set on the `expectedOwnerId` carried in Checkout metadata, and either (a) ends the prior
reign, inserts the new one, and marks the prior row `refund_status='pending'`, or (b) declares the
buyer a loser and refunds them in full with no ownership row. Stripe network calls happen *after*
commit with deterministic `Idempotency-Key`s derived from durable ids, so retries, duplicate
deliveries, and crash-in-the-middle all converge to at-most-one refund per obligation. A
`npm run reconcile` sweep (also run opportunistically at the top of every webhook) re-attempts any
`pending`/`failed` refund using the same idempotency key — that is the AC16 retry path without a job
system. Price is integer-only: `nextPrice(c) = floor((3c + 1) / 2)` = `ceil(1.5c)` with zero floats.

---

## Components & interfaces

| Component | Path | Responsibility | In → Out |
|---|---|---|---|
| Env gate | `lib/env.ts` | Parse + validate env at module load. Throws if `STRIPE_SECRET_KEY` lacks `sk_test_` prefix (AC22). `import 'server-only'`. | `process.env` → typed `env` |
| DB pool | `lib/db.ts` | Module-level `pg.Pool` (max 3, ssl), `query()`, `withTx(fn)` | SQL → rows |
| Price | `lib/price.ts` | `nextPrice(cents: number): number`, `formatUsd(cents): string` | int → int |
| Validation | `lib/validate.ts` | `parseBuyInput({displayName,url})` → `{ok,value}`/`{ok:false,fieldErrors}`; `safeHref(url): string \| null` | untrusted → normalized |
| Stripe client | `lib/stripe.ts` | Configured `Stripe` instance (apiVersion pinned), `assertTestMode()` | — |
| Throne repo | `lib/throne.ts` | `getCurrentOwner()`, `getHistory()`, `getBuyPrice()`, `commitTakeover(...)` (the tx + CAS) | — |
| Refunds | `lib/refunds.ts` | `refundPriorOwner(row)`, `refundLoser(session)`, `reconcilePendingRefunds()` | — |
| Page | `app/page.tsx` | Server component, `force-dynamic` (AC4). Renders king, price, history, TEST banner | DB → HTML |
| Buy form | `app/components/BuyForm.tsx` | `'use client'`. Collects name+url, POSTs `/api/checkout`, `window.location = url` | — |
| Checkout API | `app/api/checkout/route.ts` | Validate → recompute price from DB → create Session (AC6/7/8) | JSON → `{url}` |
| Webhook API | `app/api/stripe/webhook/route.ts` | Verify sig on raw body → idempotency → CAS transfer → post-commit refunds (AC10-16,19,20) | raw → 200 |
| Migration | `db/migrations/001_init.sql` + `scripts/migrate.ts` | Schema + seed. `npm run migrate` | — |

**Public HTTP surface (only three routes):** `GET /`, `POST /api/checkout`, `POST /api/stripe/webhook`.

---

## 1. Schema (concrete)

`db/migrations/001_init.sql`:

```sql
CREATE TABLE IF NOT EXISTS ownerships (
  id                  BIGSERIAL PRIMARY KEY,
  display_name        TEXT        NOT NULL,
  url                 TEXT        NOT NULL,
  paid_cents          INTEGER     NOT NULL CHECK (paid_cents > 0),
  payment_intent_id   TEXT        NOT NULL,
  checkout_session_id TEXT        NOT NULL,
  stripe_event_id     TEXT        NOT NULL,
  prev_ownership_id   BIGINT      REFERENCES ownerships(id),
  started_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  ended_at            TIMESTAMPTZ,
  is_current          BOOLEAN     NOT NULL DEFAULT TRUE,
  refund_status       TEXT        NOT NULL DEFAULT 'none'
                      CHECK (refund_status IN ('none','pending','succeeded','failed')),
  refund_id           TEXT,
  refund_error        TEXT,
  refunded_at         TIMESTAMPTZ,
  CONSTRAINT current_has_no_end CHECK (NOT (is_current AND ended_at IS NOT NULL)),
  CONSTRAINT ended_has_end      CHECK (is_current OR ended_at IS NOT NULL)
);

-- AC21: at most one row may have is_current = true. Partial unique index over a
-- column that is constant within the filtered set => at most one qualifying row.
CREATE UNIQUE INDEX IF NOT EXISTS ownerships_single_current
  ON ownerships (is_current) WHERE is_current;

-- AC19 cross-event guard: two different Stripe events for the same Checkout Session
-- (e.g. checkout.session.completed + checkout.session.async_payment_succeeded)
-- can never produce two reigns.
CREATE UNIQUE INDEX IF NOT EXISTS ownerships_session_uniq
  ON ownerships (checkout_session_id);

CREATE INDEX IF NOT EXISTS ownerships_started_at_desc ON ownerships (started_at DESC);
CREATE INDEX IF NOT EXISTS ownerships_refund_open
  ON ownerships (id) WHERE refund_status IN ('pending','failed');

CREATE TABLE IF NOT EXISTS processed_events (
  event_id      TEXT        PRIMARY KEY,        -- Stripe evt_...
  event_type    TEXT        NOT NULL,
  outcome       TEXT        NOT NULL DEFAULT 'received'
                CHECK (outcome IN ('received','ignored','transferred','lost','duplicate_session')),
  ownership_id  BIGINT      REFERENCES ownerships(id),
  session_id    TEXT,
  -- loser bookkeeping (a loser has no ownerships row by design — see ADR-004)
  loser_refund_status TEXT  NOT NULL DEFAULT 'none'
                CHECK (loser_refund_status IN ('none','pending','succeeded','failed')),
  loser_refund_id     TEXT,
  loser_amount_cents  INTEGER,
  loser_payment_intent_id TEXT,
  error         TEXT,
  received_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS processed_events_loser_open
  ON processed_events (event_id) WHERE loser_refund_status IN ('pending','failed');
```

**No `price_history` table.** `ownerships` *is* the price history: the price series is
`SELECT paid_cents FROM ownerships ORDER BY started_at`, and the live buy price is a pure function
of the current row. A second table would be a denormalized duplicate that can disagree with the
ledger. See **ADR-003**.

**Current owner read (AC1/2/3):**

```sql
SELECT * FROM ownerships WHERE is_current LIMIT 1;   -- 0 rows = genesis/vacant
```
```ts
buyPriceCents = current ? nextPrice(current.paid_cents) : env.SEED_PRICE_CENTS; // default 100
```

**History (AC17):** `SELECT * FROM ownerships ORDER BY started_at DESC, id DESC;` — current reign is
first and is styled distinctly (`is_current`), losers never appear (ADR-004).

---

## 2. Money flow, end to end

```
Browser                Next server                 Postgres                 Stripe
   │  POST /api/checkout {displayName,url}
   ├──────────────────────▶ validate (AC7)
   │                        SELECT current owner ───▶
   │                        price = current ? ceil(1.5*paid) : SEED   (AC2/AC6 — client amount ignored)
   │                        sessions.create(unit_amount = price,
   │                          metadata{displayName,url,expectedPriceCents,expectedOwnerId}) ───▶
   │  ◀── {url} ────────────                                                     ◀── session
   ├── redirect to Checkout ─────────────────────────────────────────────────────▶
   │  ◀── success_url /?purchase=pending  (renders "awaiting confirmation", NO state change — AC9)
                                                            Stripe ──▶ POST /api/stripe/webhook
```

**Price math (`lib/price.ts`), integer-only (AC5):**

```ts
export function nextPrice(cents: number): number {
  if (!Number.isSafeInteger(cents) || cents <= 0) throw new RangeError('cents must be a positive integer');
  return Math.floor((cents * 3 + 1) / 2);   // === ceil(1.5 * cents), no float arithmetic
}
// nextPrice(100)=150  nextPrice(150)=225  nextPrice(225)=338
```

**Checkout session creation (`app/api/checkout/route.ts`):**

```ts
export const runtime = 'nodejs';
export async function POST(req: Request) {
  assertTestMode();                                  // AC22 -> 500 w/ clear message
  const parsed = parseBuyInput(await req.json());
  if (!parsed.ok) return Response.json({ fieldErrors: parsed.fieldErrors }, { status: 400 }); // AC7
  const current = await getCurrentOwner();
  const price   = current ? nextPrice(current.paid_cents) : env.SEED_PRICE_CENTS;   // AC6
  const session = await stripe.checkout.sessions.create({
    mode: 'payment',
    line_items: [{ quantity: 1, price_data: {
      currency: 'usd', unit_amount: price,
      product_data: { name: 'The Throne', description: 'Ownership of the throne (TEST MODE)' } } }],
    success_url: `${env.NEXT_PUBLIC_BASE_URL}/?purchase=pending`,
    cancel_url:  `${env.NEXT_PUBLIC_BASE_URL}/?purchase=cancelled`,
    metadata: {                                                                      // AC8
      displayName: parsed.value.displayName,
      url: parsed.value.url,
      expectedPriceCents: String(price),
      expectedOwnerId: current ? String(current.id) : 'genesis',
    },
  });
  return Response.json({ url: session.url });
}
```

**Webhook (`app/api/stripe/webhook/route.ts`) — the only mutator:**

```ts
export const runtime = 'nodejs';          // needs raw body + pg
export const dynamic = 'force-dynamic';

export async function POST(req: Request) {
  const raw = await req.text();                                   // AC10: raw body, unparsed
  const sig = req.headers.get('stripe-signature');
  let event: Stripe.Event;
  try { event = stripe.webhooks.constructEvent(raw, sig ?? '', env.STRIPE_WEBHOOK_SECRET); }
  catch (e) { return new Response('invalid signature', { status: 400 }); }  // mutates nothing

  if (event.type !== 'checkout.session.completed') {
    await recordIgnored(event); return new Response('ok', { status: 200 });  // AC12
  }
  const session = event.data.object as Stripe.Checkout.Session;
  if (session.payment_status !== 'paid') { await recordIgnored(event); return ok(); }

  let result: TakeoverResult;
  try { result = await commitTakeover(event, session); }
  catch (e) { logError(e); return new Response('error', { status: 500 }); }  // genuine DB outage -> let Stripe retry

  // --- post-commit Stripe calls, all idempotency-keyed (never inside the tx) ---
  try {
    if (result.kind === 'transferred' && result.priorOwnership) await refundPriorOwner(result.priorOwnership);
    if (result.kind === 'lost')                                  await refundLoser(event.id, session);
  } catch (e) { logError('refund failed', e); }                    // AC16: still 2xx
  await reconcilePendingRefunds({ limit: 5 });                     // opportunistic sweep, best-effort
  return new Response('ok', { status: 200 });                      // AC12/AC16
}
```

---

## 3. The transaction: idempotency + race safety (`commitTakeover`)

```sql
BEGIN;

-- (a) AC19 exactly-once on event id. Wins the race atomically; loser of the INSERT
--     race gets 0 rows and returns early with 200.
INSERT INTO processed_events (event_id, event_type, session_id, outcome)
VALUES ($eventId, $eventType, $sessionId, 'received')
ON CONFLICT (event_id) DO NOTHING
RETURNING event_id;
--> 0 rows  => already processed: COMMIT; return {kind:'duplicate'}   (AC12, AC19)

-- (b) Serialize ALL takeovers, including genesis where there is no row to lock.
--     Transaction-scoped: auto-released on COMMIT/ROLLBACK, pgbouncer-txn-mode safe.
SELECT pg_advisory_xact_lock(7301);

-- (c) Read + lock the incumbent (0 or 1 row).
SELECT id, paid_cents, payment_intent_id, refund_status
  FROM ownerships WHERE is_current FOR UPDATE;

-- (d) COMPARE-AND-SET on expected owner (AC20).
--     expectedOwnerId from metadata: 'genesis' | '<id>'
--     match = (expected === 'genesis' && current === null) || (current && String(current.id) === expected)
--> no match => loser path (see §4)

-- (e) Cross-event dupe guard: same session already seated?
SELECT 1 FROM ownerships WHERE checkout_session_id = $sessionId;
--> exists => outcome='duplicate_session'; COMMIT; return 200

-- (f) End the prior reign FIRST (the partial unique index is checked per-statement,
--     so we must vacate the throne before seating the new king).
UPDATE ownerships
   SET is_current = FALSE, ended_at = now(),
       refund_status = CASE WHEN refund_status = 'none' THEN 'pending' ELSE refund_status END
 WHERE id = $currentId;

-- (g) Seat the new king. paid_cents = amount ACTUALLY charged (assumption 8).
INSERT INTO ownerships (display_name, url, paid_cents, payment_intent_id,
                        checkout_session_id, stripe_event_id, prev_ownership_id, is_current)
VALUES ($name, $url, $amountTotal, $paymentIntentId, $sessionId, $eventId, $currentId, TRUE)
RETURNING id;

UPDATE processed_events SET outcome = 'transferred', ownership_id = $newId WHERE event_id = $eventId;
COMMIT;   -- AC11: insert + end-prior + history are one atomic unit
```

**Why three layers of concurrency control, not one:**

| Layer | Handles |
|---|---|
| `processed_events` PK + `ON CONFLICT DO NOTHING` | duplicate delivery of the *same* event (AC19) |
| `ownerships.checkout_session_id` unique | two *different* events for the same session |
| `pg_advisory_xact_lock` + CAS on `expectedOwnerId` | two different buyers racing (AC20); works at genesis where `FOR UPDATE` has nothing to lock |
| partial unique index `ownerships_single_current` | last-resort DB invariant, provable in the AC21 test |

**Stripe idempotency keys (deterministic, derived from durable ids — AC15):**

| Call | Key |
|---|---|
| Prior-owner refund | `throne:refund:ownership:<prior_ownership_id>` |
| Loser refund | `throne:refund:loser:<checkout_session_id>` |

Both are stable across process restarts, webhook retries, and reconcile sweeps, so replaying an event
issues **at most one refund** — Stripe returns the original refund object for a repeated key.

**Exactly-once transfer under retries — crash matrix:**

| Crash point | Effect | Recovery |
|---|---|---|
| before `BEGIN` | nothing | Stripe retries → normal path |
| after (a), before COMMIT | tx rolls back incl. the `processed_events` row | Stripe retries → normal path |
| after COMMIT, before refund | transfer done, prior row `refund_status='pending'` | Stripe retry short-circuits at (a) → 200; the **reconcile sweep** issues the refund under the same key |
| after refund, before status UPDATE | refund exists, row says `pending` | reconcile re-calls with same key → Stripe returns the *same* refund → row marked `succeeded`, no double refund |

---

## 4. Losing-buyer path (AC20)

CAS mismatch at step (d) = someone else took the throne between session creation and webhook.

```sql
UPDATE processed_events
   SET outcome = 'lost', loser_refund_status = 'pending',
       loser_amount_cents = $amountTotal, loser_payment_intent_id = $paymentIntentId
 WHERE event_id = $eventId;
COMMIT;
```
Then, post-commit:
```ts
const refund = await stripe.refunds.create(
  { payment_intent: pi, amount: amountTotal, reason: 'requested_by_customer',
    metadata: { throne_reason: 'lost_race', session: sessionId } },
  { idempotencyKey: `throne:refund:loser:${sessionId}` });
await q(`UPDATE processed_events SET loser_refund_status='succeeded', loser_refund_id=$1 WHERE event_id=$2`,
        [refund.id, eventId]);
```
Guarantees: **no** `ownerships` row → no history entry (AC17 count stays exact), no `is_current`
change, no touch of the incumbent's `refund_status` → **no double-refund of the original owner**.
Return 200. Refund accounting invariant asserted by the concurrency test:

> exactly one refund per ended `ownerships` row, plus exactly one refund per `outcome='lost'` event,
> and no other refunds exist in the Stripe test account for this run.

---

## 5. Refund-failure policy (AC16)

Refunds are issued **after** commit, never inside the transaction (Stripe latency must not hold a
Postgres tx or the advisory lock).

```ts
export async function refundPriorOwner(prior: Ownership) {
  try {
    const r = await stripe.refunds.create(
      { payment_intent: prior.payment_intent_id, amount: prior.paid_cents },   // AC13: exact original amount
      { idempotencyKey: `throne:refund:ownership:${prior.id}` });              // AC15
    await q(`UPDATE ownerships SET refund_status='succeeded', refund_id=$1, refunded_at=now(),
             refund_error=NULL WHERE id=$2`, [r.id, prior.id]);
  } catch (err) {
    await q(`UPDATE ownerships SET refund_status='failed', refund_error=$1 WHERE id=$2`,
            [String(err).slice(0, 1000), prior.id]);                            // flagged row
    console.error('[throne] refund_failed', { ownershipId: prior.id, err });     // structured log
    // swallow: transfer stays committed, webhook returns 2xx -> no Stripe retry storm
  }
}
```
- Genesis (`prior === null`) → no refund call at all (AC14).
- Retry path without double-refund (AC16): `reconcilePendingRefunds()` selects
  `WHERE refund_status IN ('pending','failed')` (and the loser equivalent) and re-invokes the *same*
  idempotency key. Exposed two ways: `npm run reconcile` (script) and a bounded best-effort sweep at
  the tail of every webhook. No cron, no queue.

---

## 6. XSS / URL hardening (AC18)

**Validate on write (`lib/validate.ts`):**
```ts
const name = String(input.displayName ?? '').trim();
if (name.length < 1 || name.length > 40)        fieldErrors.displayName = 'must be 1–40 characters';
if (/[ -]/.test(name))         fieldErrors.displayName = 'contains control characters';

let u: URL; try { u = new URL(String(input.url ?? '')); } catch { fieldErrors.url = 'must be a valid URL'; }
if (u.protocol !== 'http:' && u.protocol !== 'https:') fieldErrors.url = 'must start with http:// or https://';
if (!u.hostname || u.username || u.password)           fieldErrors.url = 'invalid URL';
if (u.href.length > 500)                               fieldErrors.url = 'too long (max 500)';
// stored value is the normalized u.href — protocol-relative, javascript:, data:, vbscript: all rejected
```
`javascript:alert(1)` → `new URL()` parses it but `protocol === 'javascript:'` → **400, no Stripe
session created**.

**Escape on read:** React server components auto-escape all text nodes; `<script>alert(1)</script>`
as a display name is stored verbatim and rendered as inert text. **No** `dangerouslySetInnerHTML`
anywhere in the repo (grep-assertable in the test suite).

**Defense in depth at render:** hrefs never come straight from the DB —
```tsx
const href = safeHref(o.url);                        // returns null unless http:/https:
{href ? <a href={href} target="_blank" rel="noopener noreferrer nofollow">{o.display_name}</a>
      : <span>{o.display_name}</span>}
```
(AC1 rel/target satisfied here.) Plus response headers in `next.config.ts`:
`X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`,
`X-Frame-Options: DENY`, `Permissions-Policy: geolocation=(), camera=(), microphone=()`.

---

## 7. File layout (exact paths the developer creates)

```
~/Downloads/project-2/
├─ package.json                      # scripts: dev build start migrate reconcile test typecheck
├─ tsconfig.json                     # strict: true
├─ next.config.ts                    # security headers
├─ vitest.config.ts
├─ .gitignore                        # .env*, !.env.example, node_modules, .next
├─ .env.example                      # AC24: placeholders only
├─ README.md                         # AC23/25: runbook, 4242 4242 4242 4242, stripe listen, Vercel
├─ db/migrations/001_init.sql
├─ scripts/migrate.ts
├─ scripts/reconcile-refunds.ts
├─ lib/env.ts
├─ lib/db.ts
├─ lib/stripe.ts
├─ lib/price.ts
├─ lib/validate.ts
├─ lib/throne.ts
├─ lib/refunds.ts
├─ lib/types.ts
├─ app/layout.tsx
├─ app/globals.css
├─ app/page.tsx                      # export const dynamic = 'force-dynamic'; export const revalidate = 0
├─ app/components/TestModeBanner.tsx
├─ app/components/BuyForm.tsx        # 'use client'
├─ app/components/OwnerCard.tsx
├─ app/components/HistoryList.tsx
├─ app/api/checkout/route.ts
├─ app/api/stripe/webhook/route.ts
└─ tests/
   ├─ price.test.ts                  # AC5
   ├─ validate.test.ts               # AC7, AC18
   ├─ webhook.test.ts                # AC10,11,12,13,14,15,16,19 (Stripe SDK mocked)
   └─ concurrency.test.ts            # AC20, AC21 (real Postgres via TEST_DATABASE_URL)
```

`.env.example` (AC24): `DATABASE_URL`, `STRIPE_SECRET_KEY=sk_test_...`, `STRIPE_WEBHOOK_SECRET=whsec_...`,
`NEXT_PUBLIC_BASE_URL=http://localhost:3000`, `SEED_PRICE_CENTS=100`.
Only `NEXT_PUBLIC_BASE_URL` is `NEXT_PUBLIC_`-prefixed; every secret is read exclusively from
`lib/env.ts`, which starts with `import 'server-only'` so any accidental client import is a build error.

---

## Trade-offs considered

| Option | Pros | Cons | Chosen? |
|---|---|---|---|
| `throne_state` singleton row pointing at current owner | one obvious row to lock | second source of truth; can drift from ledger; still needs a lock at genesis | No |
| `ownerships.is_current` + partial unique index | single ledger, DB-enforced invariant, AC21 verbatim | must vacate before seating (statement-level index check) | **Yes** (ADR-001) |
| `SELECT … FOR UPDATE` alone | idiomatic | locks nothing when 0 rows → two genesis buyers both win | No |
| `pg_advisory_xact_lock` + CAS + partial index | correct at genesis and steady state; cheap | one global lock = serialized takeovers (fine at this throughput) | **Yes** (ADR-001) |
| Refund inside the DB transaction | "atomic" feel | holds tx + global lock across a Stripe round-trip; a Stripe timeout rolls back a real charge's transfer | No |
| Refund after commit + deterministic key + reconcile sweep | tx stays short; crash-safe; AC15/16 both fall out | brief window where prior owner is `pending` | **Yes** (ADR-002) |
| Separate `price_history` table | "explicit" | duplicate of ledger, can disagree, extra writes in the hot tx | No (ADR-003) |
| Loser gets an `ownerships` row w/ `is_current=false` | uniform records | pollutes history (breaks AC17 count), invites double-refund logic | No (ADR-004) |
| Prisma / Drizzle | typed queries | install + generate + migration engine on the critical path; ~12 queries total | No (ADR-005) |
| `ceil(cents * 1.5)` with floats | obvious | float in the money path violates AC5's spirit | No — use `floor((3c+1)/2)` |

---

## Risk register

| Risk | Severity | Mitigation | Owner |
|---|---|---|---|
| Serverless cold starts exhaust Postgres connections | med | `Pool({max: 3})`, module-level reuse, require a pooled `DATABASE_URL` (Neon/Supabase pooler); documented in README | developer |
| Refund left `pending`/`failed` (Stripe outage) — prior king out of pocket | med | flagged row + structured log + `npm run reconcile` with same idempotency key; README documents it | developer |
| Global advisory lock serializes all purchases | low | throughput is ~1 purchase/minute at best; lock held for ms | architect |
| Stripe metadata (`expectedOwnerId`) is the CAS token; a hand-crafted event could forge it | low | signature verification (AC10) precedes all metadata reads | security |
| Duplicate Stripe *account* refunds if `TEST_DATABASE_URL` points at the dev DB | low | tests use a separate DB + mocked Stripe except the documented manual runbook | QA |
| No moderation: offensive name / hostile link on the throne | med | escaping + `nofollow` + `noopener`; accepted per spec assumption 13; requires a DB `UPDATE` to remove | human |
| Strict CSP not shipped (Next inline bootstrap needs nonce plumbing) | low | no `dangerouslySetInnerHTML` + no user HTML anywhere; nosniff/frame-deny headers ship | security |
| AC20 says "three total refunds"; the two-racer scenario mechanically yields **two** (prior owner + loser) unless the setup flip's refund is counted | low | test asserts the precise invariant (1 refund per ended reign + 1 per lost event) and documents the count derivation | QA |
| Price exceeds card limits after ~15 flips | low | out of scope per spec; noted in README | human |

---

## Decisions
- **ADR-001** — Current owner = `is_current` partial unique index; race safety via `pg_advisory_xact_lock` + compare-and-set on `expectedOwnerId`
- **ADR-002** — Refunds issued post-commit with deterministic idempotency keys + reconcile sweep (no queue/cron)
- **ADR-003** — No separate `price_history` table; `ownerships` is the price ledger
- **ADR-004** — Losing buyer gets a full auto-refund and no `ownerships` row
- **ADR-005** — Raw `pg` + plain SQL migrations, no ORM
- **ADR-006** — XSS/URL hardening: protocol allowlist on write + `safeHref()` on render + security headers

## Buildability sign-off
- [ ] Developer confirms this is implementable.
