# ADR-004: Losing buyer gets a full auto-refund and no `ownerships` row

- **Status:** accepted
- **Superseded-by:** —
- **Date:** 2026-09-01
- **Task:** T-001
- **Deciders:** architect

## Context
Two buyers create Checkout Sessions at the same price P against the same incumbent. Both pay. Only
one can be king (AC20/AC21). The loser has been charged real (test) money and must be made whole,
without corrupting history (AC17's "after N successful purchases the list has N entries") and without
triggering a second refund of the incumbent.

## Decision
The compare-and-set on `expectedOwnerId` (ADR-001) detects the loser inside the transaction. Then:
- **No** `ownerships` row is inserted. **No** `is_current` change. **No** touch of the incumbent's
  `refund_status` (so the incumbent's single refund obligation stays exactly one).
- The `processed_events` row is stamped `outcome='lost'`, `loser_refund_status='pending'`, plus
  `loser_amount_cents` and `loser_payment_intent_id` for bookkeeping and retry.
- COMMIT, then post-commit `stripe.refunds.create({payment_intent, amount: amount_total})` with
  `Idempotency-Key = throne:refund:loser:<checkout_session_id>`; status written back.
- Webhook returns 200 (AC12).

Refund accounting invariant (asserted by the concurrency test): **exactly one refund per ended
`ownerships` row, plus exactly one refund per `outcome='lost'` event, and no others.**

## Alternatives considered
- **Insert the loser as `is_current=false, ended_at=now()`.** Rejected: it would appear in the
  AC17 history list as a reign that never happened, break the "N purchases → N entries" assertion,
  and put a row into the `refund_status IN ('pending','failed')` sweep that is semantically a
  different kind of obligation.
- **"Highest price wins" / re-price the loser upward.** Rejected: both sessions were created at the
  same price, so there is nothing to compare; and re-charging without consent is unacceptable.
- **Let the loser keep the charge and take the throne next (queue).** Rejected: queues are out of
  scope and it silently changes what the buyer agreed to pay.
- **Refund manually / email the loser.** Rejected: no email capture, no admin UI.

## Consequences
+ History stays a clean, exact record of actual reigns.
+ The incumbent can never be double-refunded, because only the transferred path marks them `pending`.
+ Loser refunds are retryable through the same reconcile sweep as owner refunds.
− Losers are invisible on the public page. Their only trace is a `processed_events` row plus the
  Stripe refund. Acceptable at this scale; noted as a low risk.
− A loser is out of pocket for the Stripe refund settlement window (irrelevant in TEST mode).
