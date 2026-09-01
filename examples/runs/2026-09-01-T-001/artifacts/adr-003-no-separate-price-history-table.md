# ADR-003: No separate `price_history` table — `ownerships` is the price ledger

- **Status:** accepted
- **Superseded-by:** —
- **Date:** 2026-09-01
- **Task:** T-001
- **Deciders:** architect

## Context
The task brief asked for "ownership rows + price history + processed_events". AC17 requires a
reverse-chronological list of past owners with price paid and reign start/end; AC2 requires the live
buy price. Both are read paths.

## Decision
Do not create a `price_history` table. `ownerships` records `paid_cents` per reign, which *is* the
price series:

```sql
SELECT id, display_name, url, paid_cents, started_at, ended_at, is_current
FROM ownerships ORDER BY started_at DESC, id DESC;   -- AC17
```
The live price is a pure function of the single current row:
`price = current ? nextPrice(current.paid_cents) : SEED_PRICE_CENTS` (AC2/AC3). Genesis price comes
from `SEED_PRICE_CENTS` (env), not from a DB row, so no seed data is required beyond an empty table.

## Alternatives considered
- **`price_history(id, price_cents, effective_at, ownership_id)`.** Rejected: every value is derivable
  from `ownerships`; it adds a write to the hot, lock-held transaction and creates a second source of
  truth that can disagree with the ledger after any partial failure.
- **`throne_state(current_price_cents)` cached column.** Rejected: same drift risk; the computation is
  one integer multiply.

## Consequences
+ Two tables total. One insert + one update in the hot transaction.
+ The price series can never disagree with the ownership ledger — it is the same rows.
− Changing `SEED_PRICE_CENTS` after deploy but before the first purchase silently changes the genesis
  price. Documented in the README; harmless in TEST mode.
− A future "price curve changed on date X" feature would need real history. Explicitly out of scope
  (spec: no pricing rule other than fixed 1.5x).
