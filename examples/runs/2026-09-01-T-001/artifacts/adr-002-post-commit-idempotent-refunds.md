# ADR-002: Refunds issued post-commit with deterministic idempotency keys + reconcile sweep

- **Status:** accepted
- **Superseded-by:** —
- **Date:** 2026-09-01
- **Task:** T-001
- **Deciders:** architect

## Context
On a takeover the prior owner must be refunded exactly `paid_cents` against their stored
`payment_intent_id` (AC13), at most once even under duplicate webhook delivery (AC15/AC19), and a
refund failure must not roll back the ownership transfer or cause a Stripe retry storm (AC16). Stripe
calls are network I/O with unbounded latency; the transfer transaction holds a global advisory lock.

## Decision
- The DB transaction commits the transfer and marks the prior row `refund_status='pending'`. **No
  Stripe call happens inside the transaction.**
- Immediately after COMMIT the handler calls `stripe.refunds.create({payment_intent, amount: prior.paid_cents})`
  with `Idempotency-Key = throne:refund:ownership:<prior_ownership_id>`; the loser refund uses
  `throne:refund:loser:<checkout_session_id>`. Both keys derive from durable ids, not from anything
  in memory, so they are identical on every retry, restart, and reconcile pass.
- Success → `refund_status='succeeded', refund_id, refunded_at`. Failure → `refund_status='failed'`,
  `refund_error` recorded, `console.error` structured log, **webhook still returns 2xx**.
- Recovery is a `reconcilePendingRefunds()` function over
  `WHERE refund_status IN ('pending','failed') AND NOT is_current` that re-issues with the same key. It
  runs (a) as `npm run reconcile` and (b) as a bounded best-effort tail on every webhook request.
- **Revision (security review, 2026-09-01):** the original text of this ADR claimed re-attempts "can
  never double-refund" on the strength of the Idempotency-Key alone. That's overstated — Stripe expires
  idempotency keys after 24h, so a reconcile pass more than a day after the original attempt would no
  longer be deduplicated by the key. Before every `refunds.create` call, `lib/refunds.ts` now calls
  `stripe.refunds.list({ payment_intent, limit: 10 })` and short-circuits to the existing refund if one
  is found. This is the durable de-dup check; the idempotency key is a same-day fast path on top of it,
  not the only line of defense.
- Genesis (no prior owner) makes no refund call at all (AC14).

## Alternatives considered
- **Refund inside the transaction.** Rejected: holds the global lock across a Stripe round-trip; a
  Stripe timeout after the refund actually succeeded would roll back the transfer, leaving a refunded
  prior owner still on the throne — the worst possible state.
- **Return 5xx on refund failure and let Stripe retry the webhook.** Rejected by AC16: the transfer is
  already committed, so retries re-enter the idempotency short-circuit and 5xx forever; Stripe
  eventually disables the endpoint.
- **A cron job / queue for retries.** Rejected: explicitly out of scope, and unnecessary given the
  idempotency key makes retry trivially safe from any caller.
- **Random/UUID idempotency keys stored in the DB before the call.** Rejected: needs an extra write
  and an extra crash window; the ownership row id is already unique and durable.

## Consequences
+ Transaction stays short; the lock is never held over network I/O.
+ Every crash window resolves to at-most-one refund (see the crash matrix in the design doc).
+ AC15 is verifiable directly against the Stripe test API (`refunds.list` shows exactly one).
− A short window exists where the prior owner is `pending` and not yet refunded.
− A refund can sit `failed` indefinitely if nobody buys again and nobody runs `reconcile`. Recorded
  as a med-severity risk; mitigated by the README documenting `npm run reconcile`.
