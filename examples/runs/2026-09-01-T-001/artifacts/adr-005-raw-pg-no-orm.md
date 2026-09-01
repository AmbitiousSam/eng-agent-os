# ADR-005: Raw `pg` + plain SQL migrations, no ORM

- **Status:** accepted
- **Superseded-by:** —
- **Date:** 2026-09-01
- **Task:** T-001
- **Deciders:** architect

## Context
The stack fixes Postgres via `pg` and `DATABASE_URL`. The brief allows an ORM only "if it saves work".
The whole app is roughly a dozen queries, two of which need Postgres features ORMs abstract away
poorly: `pg_advisory_xact_lock`, `INSERT … ON CONFLICT DO NOTHING RETURNING`, and a partial unique
index. The human wants it live today.

## Decision
Use `pg` directly. A module-level `Pool({ connectionString, max: 3, ssl })` reused across serverless
invocations, a `withTx(fn)` helper that BEGIN/COMMIT/ROLLBACKs on a dedicated client, and parameterized
queries everywhere (`$1`-style — no string interpolation into SQL, ever). Migrations are numbered
`.sql` files in `db/migrations/` applied by `scripts/migrate.ts` (read files, run in order inside a
transaction, record applied names in a `_migrations` table). Row types are hand-written interfaces in
`lib/types.ts`.

## Alternatives considered
- **Prisma.** Rejected: install + `prisma generate` on the critical path, a migration engine to learn,
  awkward escapes to `$queryRaw` for the advisory lock and `ON CONFLICT … RETURNING`, and a
  meaningful serverless cold-start cost — all for ~12 queries.
- **Drizzle.** Lighter and would work, but still a schema DSL plus a migration toolchain to configure,
  and the partial unique index and advisory lock would be raw SQL anyway. Not worth the setup time
  today.
- **Kysely.** Type-safe query building, but requires generated or hand-written DB types regardless —
  the same hand-written interfaces we already need, plus a dependency.

## Consequences
+ Zero codegen; `npm install && npm run migrate && npm run dev` works immediately.
+ The exact SQL in the design doc is the exact SQL in the repo — reviewable, and the concurrency
  guarantees are visible rather than hidden behind an abstraction.
− Row types are hand-maintained; a schema change that isn't mirrored in `lib/types.ts` compiles fine
  and fails at runtime. Mitigated by two tables, a strict `tsconfig`, and integration tests that hit
  a real Postgres.
− Manual SQL is an injection surface. Mitigated by an absolute rule of parameterized queries only;
  the test suite greps for template-literal interpolation inside `q(`/`client.query(`.
