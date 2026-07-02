# Harness: event-processor

## Topology
An asynchronous consumer/worker: reads from a queue or log, processes, writes to a sink
(DB, another topic, external API). Typical stack: Kafka or SQS/RabbitMQ, a worker service in
Go/TypeScript/Python, a DLQ, Prometheus + Alertmanager (or CloudWatch) for runtime signals.

## Guides (feedforward)

| Guide | What it steers |
|---|---|
| Idempotency by design | Every handler keyed on a message ID with a dedupe store or upsert semantics — processing twice must equal processing once. |
| At-least-once semantics documented | The delivery contract (redelivery, ordering, dedupe window) is written down where the handler lives; no one gets to assume exactly-once. |
| Poison-message / DLQ policy | Unprocessable messages go to the DLQ after N attempts with full context attached; the DLQ has an owner and a replay procedure. |
| Backpressure rules | Bounded prefetch/concurrency; the consumer slows down rather than buffering unboundedly when the sink degrades. |
| No unbounded retries | Every retry loop has a budget, exponential backoff with jitter, and a terminal outcome (DLQ or explicit drop). |
| Sink writes are transactional or compensated | Partial processing never leaves the sink half-written on redelivery. |

## Sensors (feedback)

| Sensor | What it catches | How to implement |
|---|---|---|
| Idempotency replay test | Handler that mutates state twice on redelivery | Test in `tests/architecture/` feeds the same message twice, asserts identical sink state |
| Duplicate-delivery chaos test | Dedupe assumptions that only hold in the happy path | Testcontainers broker delivering each message 2–3x under concurrency, assert no double effects |
| DLQ alert rule | Poison messages silently accumulating | Alert rule: DLQ depth > 0 for 10m pages the owner; rule file checked into the repo |
| Consumer-lag alert | Processing falling behind ingestion | Burrow/CloudWatch lag alert with a threshold derived from the stated freshness SLO |
| Retry-budget check | Retry loops without a cap or backoff | Structural test/lint asserting every retry call site uses the shared bounded-retry helper |
| Throughput budget test | Handler regressions that will surface as lag in prod | k6/bench test asserting messages-per-second floor on the hot path |

## Danger zones

- **"Exactly-once" assumptions** — every broker eventually redelivers; code that isn't idempotent is a time bomb with a production-only fuse.
- **Silent DLQ** — a DLQ nobody watches converts data loss into a surprise weeks later; the alert rule is non-negotiable.
- **Retry storms** — unbounded retries against a degraded sink turn one failure into an outage; budgets and backoff are the circuit breaker.
- **Ordering myths** — partition-level ordering is not global ordering; handlers that need sequence must enforce it themselves.

## Instantiation

1. Copy the Guides table into the project's `CLAUDE.md`; document the delivery contract and DLQ ownership in the GROUND codebase map.
2. Run `skills/fitness-functions` per sensor row: replay/chaos/structural tests into `tests/architecture/`, alert rules as checked-in config validated by a test.
3. Confirm the pre-push gate runs the test sensors; list the runtime sensors (DLQ, lag alerts) with owners in `templates/launch-review.md` before ship.
