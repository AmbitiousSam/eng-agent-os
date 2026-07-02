# Harness: web-api-service

## Topology
A synchronous business API — REST or GraphQL — with authenticated clients, a versioned public
contract, and a relational database. Typical stack: Node/TypeScript or Go, Postgres, OpenAPI or
GraphQL schema, JWT/OIDC auth, structured JSON logging.

## Guides (feedforward)

| Guide | What it steers |
|---|---|
| Layering: handler → service → repo | Handlers parse/respond only; business logic in services; SQL only in repos. No layer skipping. |
| Input validation at the edge | Every request body/param validated against a schema in the handler; services trust their inputs. |
| Error taxonomy | One enumerated error set (validation / auth / not-found / conflict / internal) mapped to status codes; no ad-hoc throws. |
| Pagination convention | Cursor-based, single shape (`items`, `next_cursor`, `limit` cap) on every list endpoint from day one. |
| No PII in logs | Log IDs and event names, never emails, tokens, names, or payloads; a denylist of field names is the rule. |
| API versioning discipline | Public contract changes are additive; breaking changes require a new version and a deprecation window. |
| Migrations forward-only | Schema changes ship as reversible-by-roll-forward migrations, never manual DB edits. |

## Sensors (feedback)

| Sensor | What it catches | How to implement |
|---|---|---|
| Dependency-direction check | Handler importing repo, repo importing service | dependency-cruiser rule in `tests/architecture/` forbidding cross-layer imports |
| API-contract diff | Accidental breaking change to the public contract | `oasdiff` (or `graphql-inspector`) against the committed spec, fail on `breaking` |
| Authz coverage test | A route shipped without an auth check | Test enumerates the router table, asserts every route declares auth middleware or an explicit `public` marker |
| Latency budget test | p95 regression on hot endpoints | k6 smoke with per-endpoint p95 thresholds, budgets checked into the repo |
| PII-in-logs scanner | Email/token/name leaking into log output | Test drives key flows with a capturing logger, regex-scans output for PII patterns and denylisted fields |
| Error-taxonomy conformance | Handlers returning off-taxonomy status codes | Contract test asserting error responses match the shared error schema |

## Danger zones

- **Authz gaps** — the one missing check on the one forgotten route is the classic breach; that's why coverage is asserted structurally, not reviewed manually.
- **Silent contract breaks** — a renamed field is invisible in code review and fatal to clients; only the diff sensor sees it.
- **N+1 queries behind the repo layer** — clean layering hides them; the latency budget is the tripwire.
- **PII creep in debug logging** — added under incident pressure, never removed; the scanner outlives the incident.

## Instantiation

1. Copy the Guides table into the project's `CLAUDE.md` as binding conventions; link the GROUND codebase map to the layering rule.
2. Run `skills/fitness-functions` on each sensor row to turn it into an executable check in `tests/architecture/`, named after the rule it enforces.
3. Confirm the pre-push gate runs the new suite, and record the runtime sensors (latency budget, log scanner scope) in `templates/launch-review.md`.
