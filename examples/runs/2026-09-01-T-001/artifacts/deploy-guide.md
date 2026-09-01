# Deploy Guide — T-001 "Throne"

Status: build/tests/security review complete. This guide is a set of **human-executed steps**
(git push, Vercel deploy, Stripe key/webhook creation, running migrations against a real DB).
No agent has credentials or CLI access to run any of this — every step below is PROPOSED,
not performed. Treat each numbered step as something you run yourself, in order.

Target: Vercel, Stripe **TEST mode only** (AC22 enforces this at boot — do not paste a live
`sk_live_...` key anywhere in this flow).

---

## 0. Prereqs / current state

- No git repo exists yet in this directory.
- Vercel CLI is not installed locally.
- No Postgres instance provisioned yet.
- No Stripe TEST account/keys/webhook wired up yet.
- `npm run build` requires **no** env vars (no DB/Stripe call at build/module scope), so the
  Vercel build itself won't fail on missing secrets — but the app will 500 on first request
  until env vars are set (AC22: boot check on `STRIPE_SECRET_KEY` prefix).

---

## 1. Init git repo + first commit

```bash
cd ~/Downloads/project-2
git init
git add -A
git status   # sanity-check what's staged before committing
git commit -m "Throne: initial commit, ready for launch"
```

**What goes in:** `app/`, `lib/`, `db/`, `scripts/`, `tests/`, `package.json`,
`package-lock.json`, `README.md`, `.env.example`, config files, and `.eaos/` (task spec, design
doc, ADRs, this guide). `.eaos/` staying in git history is fine — it is planning/process
artifacts, not app runtime code, and Vercel's build does not read it.

**What must stay out:**
- `.env` / `.env.local` — never commit real secrets. Already covered by `.gitignore`
  (`.env` is ignored, `.env.example` is explicitly un-ignored). Confirm before committing:
  `git status` should **not** list `.env`.
- `node_modules`, `.next`, `*.tsbuildinfo` — already in `.gitignore`.

Double-check nothing secret slipped in:
```bash
git show --stat HEAD | grep -i '\.env$' && echo "STOP: .env is tracked" || echo "clean"
```

---

## 2. Get the repo onto Vercel — two paths, pick one

### Path A — GitHub + Vercel dashboard import (recommended, no local CLI needed)
1. Create a new empty GitHub repo (private is fine).
2. `git remote add origin <your-repo-url>` then `git push -u origin main`.
3. In the Vercel dashboard: **Add New → Project → Import** the GitHub repo. Framework preset
   Next.js is auto-detected. Do **not** click Deploy yet — set env vars first (Step 4), or set
   them now and redeploy after; either order works, but the first deploy will 500 until they're
   set.

### Path B — Vercel CLI
```bash
npm i -g vercel        # not currently installed
vercel login
vercel link             # creates/links the Vercel project from this directory
vercel deploy           # preview deploy first
vercel deploy --prod    # promote to production once verified
```

Either path produces a live URL (`https://<project>.vercel.app` or your custom domain). You
need this URL before Step 5 (Stripe webhook endpoint).

---

## 3. Provision Postgres and run the migration

1. Provision a Postgres instance — Vercel Marketplace Postgres (Neon) is the path of least
   friction since it wires `DATABASE_URL` into the Vercel project automatically; any managed
   Postgres (Neon, Supabase, RDS) works equally well since the app uses raw `pg`, no ORM lock-in.
2. Get the **pooled** connection string (README's `Pool max: 3` note assumes serverless-friendly
   pooling — use the pooled/pgbouncer endpoint, not a direct connection, since Vercel functions
   are short-lived and concurrent).
3. Run the migration once, from your machine, pointed at the real `DATABASE_URL`:
   ```bash
   DATABASE_URL="<pooled-connection-string>" npm run migrate
   ```
   This applies `db/migrations/001_init.sql` (the only migration — see Rollback section, it's
   additive-only) and records it in `_migrations`.
4. Sanity check: connect with `psql` (or the provider's SQL console) and confirm `ownerships`
   and `processed_events` tables exist with the partial unique index
   `ownerships_single_current`.

---

## 4. Set env vars in Vercel

Vercel dashboard → Project → Settings → Environment Variables. Set all five for
**Production**, and also for **Preview** if you plan to use preview deploys for anything beyond
this launch:

| Var | Value |
|---|---|
| `DATABASE_URL` | pooled connection string from Step 3 |
| `STRIPE_SECRET_KEY` | TEST secret key, **must start with `sk_test_`** (Step 5) |
| `STRIPE_WEBHOOK_SECRET` | from the webhook endpoint you create in Step 5 — set this *after* creating the endpoint |
| `NEXT_PUBLIC_BASE_URL` | the live URL from Step 2, e.g. `https://throne.vercel.app` |
| `SEED_PRICE_CENTS` | `100` (or your chosen genesis price) |

Redeploy after changing env vars (Vercel does not hot-reload them into a running deployment).

---

## 5. Stripe TEST mode setup

1. In the Stripe Dashboard, ensure you're in **Test mode** (toggle top-right).
2. Developers → API keys: copy the **Publishable key** (`pk_test_...`, only needed if you
   later add client-side Stripe.js — currently unused per the codebase, Checkout Session URL
   redirect is server-driven) and the **Secret key** (`sk_test_...`). Set the secret key as
   `STRIPE_SECRET_KEY` in Vercel (Step 4).
3. Developers → Webhooks → Add endpoint:
   - URL: `https://<your-live-domain>/api/stripe/webhook`
   - Events to send: `checkout.session.completed` and
     `checkout.session.async_payment_succeeded` (the second covers delayed-payment methods;
     the DB's unique index on `checkout_session_id` — AC19 — guarantees this can never produce
     a duplicate reign even if both fire for one session).
4. Copy the endpoint's **Signing secret** (`whsec_...`) into `STRIPE_WEBHOOK_SECRET` in Vercel.
5. Redeploy so the new env vars take effect.

---

## 6. Go-live verification runbook (manual — covers the ACs sandbox/CI couldn't exercise)

Run these against the live production URL, in Stripe TEST mode, after Step 5's redeploy.

1. **Genesis purchase**
   - Load the live URL. Confirm "Vacant" state, buy price = `SEED_PRICE_CENTS` ($1.00), and
     the "TEST MODE — no real money" banner is visible (AC23).
   - Submit a display name + URL, proceed to Stripe Checkout, pay with `4242 4242 4242 4242`,
     any future expiry/CVC/ZIP.
   - Confirm redirect to `/?purchase=pending` does **not** itself change the owner (AC9) —
     reload immediately and check it's still showing the prior state until the webhook lands.
   - Within a few seconds, reload `/`: new owner shown, amount paid correct, buy price now
     `ceil(1.5 × paid)`.
   - Verify DB: a new row in `ownerships` with `is_current = true`, correct `paid_cents`,
     `payment_intent_id`, `checkout_session_id`, `stripe_event_id`.
   - Verify Stripe dashboard (test mode → Payments): one succeeded PaymentIntent for the
     charged amount, no refund (AC14 — genesis has no prior owner to refund).

2. **A takeover, with refund**
   - Repeat as a different buyer. Buy price should be 1.5× the prior owner's paid amount.
   - Pay with `4242 4242 4242 4242`.
   - After the webhook lands, reload `/`: new buyer is king, prior owner now appears in
     History with reign start/end timestamps (AC17).
   - Verify DB: prior owner row `is_current = false`, `ended_at` set; new owner row
     `is_current = true`.
   - Verify Stripe dashboard: exactly one refund issued against the prior owner's original
     PaymentIntent, for exactly what they paid (AC13).

3. **Webhook redelivery does not double-refund (AC15/AC19)**
   - In the Stripe Dashboard, find the `checkout.session.completed` event for the takeover
     above (Developers → Webhooks → your endpoint → Events) and click **Resend**.
   - Confirm the endpoint returns 2xx and mutates nothing: reload `/`, owner/history unchanged.
   - Verify Stripe dashboard: still exactly **one** refund for that PaymentIntent (Refunds
     list), not two. This confirms the idempotency key derived from the ownership row id
     worked (ADR-002).

4. **Live-key rejection guard (AC22)**
   - This is a negative test — do **not** actually redeploy with a live key against real
     Stripe. Instead confirm the guard exists: in `lib/env.ts`, the boot/request check rejects
     any `STRIPE_SECRET_KEY` not prefixed `sk_test_`. If you ever paste a `sk_live_...` key
     into Vercel by mistake, the app should fail closed (500 or refuse to boot) rather than
     silently charge real money. Sanity check this once in a **local** `.env` (never against
     the deployed prod env vars) by setting `STRIPE_SECRET_KEY=sk_live_x` and confirming
     `npm run dev` / the checkout endpoint refuses to proceed, then revert it.

If all four checks pass, launch is verified. If any fail, do not announce the URL — go to
Rollback below or fix forward before re-verifying.

---

## 7. Rollback

**Trigger:** a bad deploy ships (broken webhook handling, env var misconfig, regression found
post-launch).

**DB migration reversal — not needed.** Checked `db/migrations/001_init.sql`: it is a single
additive migration (`CREATE TABLE IF NOT EXISTS`, `CREATE UNIQUE INDEX IF NOT EXISTS`,
`CREATE INDEX IF NOT EXISTS`) with no `ALTER`/`DROP` and no destructive statements. There is
currently no migration history to roll back — schema is forward-only by design (README/ADR
note this explicitly). Rolling back the app code does **not** require touching the database.

**App rollback — Vercel instant rollback:**
- Dashboard: Project → Deployments → find the last known-good deployment → **⋯ → Promote to
  Production**. This is effectively instant and swaps traffic back with no rebuild.
- CLI equivalent: `vercel rollback` (or `vercel promote <deployment-url>`).

**After rollback:**
- If the bad deploy already processed live webhook events (rows already written), those rows
  are historical fact and don't need cleanup — the schema doesn't support deletion of
  ownership history by design (AC17's ledger is append-only).
- If a webhook was misconfigured and events were missed during the bad window, Stripe retains
  failed/undelivered webhook events for a period and they can be resent manually from the
  Dashboard (Developers → Webhooks → Events → Resend) once the good deployment is live again —
  safe to do because of the idempotency guarantees verified in Step 6.3.
- No env var changes are needed for a code-only rollback (same `DATABASE_URL`/Stripe keys
  still apply). If the bad deploy shipped alongside a bad env var change, revert the env var in
  Vercel settings *before* promoting the previous deployment, then redeploy/promote.

---

## 8. Post-launch monitoring

- **Vercel function logs** (Dashboard → Project → Logs, or `vercel logs <deployment-url>`) —
  watch `/api/stripe/webhook` and `/api/checkout` for 4xx/5xx spikes right after launch.
- **Stripe Dashboard events** (test mode → Developers → Events, and → Payments/Refunds) —
  confirm each Checkout completion has exactly one matching refund (when there's a prior
  owner) and no repeated refund attempts.
- **`npm run reconcile`** — retries any `refund_status = 'pending'|'failed'` row using the same
  deterministic idempotency key (AC16's retry path). **Known gap: there is no cron/scheduled
  job wired up.** Run it manually after launch and periodically while the app is live:
  ```bash
  DATABASE_URL="<pooled-connection-string>" STRIPE_SECRET_KEY="sk_test_..." npm run reconcile
  ```
  If sustained traffic is expected, consider wiring this to a Vercel Cron (`vercel.json`
  `crons` entry hitting a protected route) as a fast-follow — flagging as a gap, not blocking
  today's launch since refund failures don't roll back ownership (AC16) and the app stays
  correct in the interim, just with a stuck refund until reconciled.

---

## Owners / links

- Task: T-001 "Throne" — spec at `.eaos/T-001/artifacts/task-spec.md`, design at
  `.eaos/T-001/artifacts/design-doc.md`, ADRs in the same directory.
- Runbook this extends: `README.md` §"Runbook: local, from a clean clone" and §"Deploying to
  Vercel" (kept as the canonical local-dev flow; this document is the authoritative go-live
  and rollback procedure).
