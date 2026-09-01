# ADR-001: Current owner representation and race safety

- **Status:** accepted
- **Superseded-by:** —
- **Date:** 2026-09-01
- **Task:** T-001
- **Deciders:** architect

## Context
Exactly one person may hold the throne (AC21). Two buyers can pay concurrently against the same
incumbent at the same price; exactly one must win (AC20). The genesis case is the hard one: with zero
rows in the table there is nothing for `SELECT … FOR UPDATE` to lock, so two first-ever buyers would
both observe "vacant" and both insert.

## Decision
1. **Representation:** the current king is the single `ownerships` row with `is_current = TRUE`.
   Enforced at the DB level by `CREATE UNIQUE INDEX ownerships_single_current ON ownerships (is_current) WHERE is_current`.
2. **Serialization:** every webhook transfer takes `SELECT pg_advisory_xact_lock(7301)` immediately
   after the idempotency insert. Transaction-scoped, so it is released by COMMIT/ROLLBACK and is safe
   under pgbouncer transaction pooling.
3. **Compare-and-set:** the Checkout Session metadata carries `expectedOwnerId`
   (`'genesis'` or the incumbent's id). Inside the lock we re-read the incumbent
   (`SELECT … WHERE is_current FOR UPDATE`) and require the CAS to match. Mismatch → loser path (ADR-004).
4. **Statement ordering:** the prior reign is ended (`is_current=FALSE, ended_at=now()`) **before**
   the new row is inserted, because a unique index is enforced per statement and cannot be deferred.

## Alternatives considered
- **`throne_state` singleton row** holding `current_ownership_id`, locked with `FOR UPDATE`. Rejected:
  a second source of truth that can drift from the ledger, and it still needs seeding/migration care.
  The partial index gives the same invariant with zero extra rows and is directly assertable by AC21.
- **`SELECT … FOR UPDATE` alone.** Rejected: no rows to lock at genesis; the partial unique index
  would turn a race into a 500 rather than a clean loser-refund.
- **`SERIALIZABLE` isolation with retry.** Rejected: serialization failures surface as errors the
  handler must classify and retry, which is more code and more failure modes than one advisory lock,
  for identical throughput at this scale.
- **Optimistic `UPDATE … WHERE id = $expected AND is_current` with rowcount check, no lock.** Correct
  for takeovers but not for genesis (two inserts, both valid until the index fires). Rejected for
  needing a special-case path anyway.

## Consequences
+ Genesis and steady-state use one identical code path.
+ AC21 is provable by the schema, not by application discipline.
+ CAS mismatch is a first-class, testable outcome rather than an exception.
− All takeovers serialize on one global lock. Acceptable: purchases are human-paced and the lock is
  held for milliseconds (no network I/O inside the transaction — see ADR-002).
− The vacate-then-seat ordering means a mid-transaction crash could theoretically leave the throne
  vacant; it cannot, because both statements are in the same transaction and roll back together.
