# Harnesses — per-topology guide+sensor bundles

A **harness template** is a pre-built bundle of controls for one service topology, in the
harness-engineering sense (Böckeler): **guides** are feedforward controls — conventions, rules,
and skills that steer the agent *before* it acts; **sensors** are feedback controls — tests,
linters, structural checks, and alerts that catch problems *after*. Committing to a topology
narrows variety (Ashby's law), which is exactly what makes a strong, specific harness feasible.
A new service should start governed, not naked.

## Templates

| File | Topology |
|---|---|
| `web-api-service.md` | REST/GraphQL business API (auth, versioned public API, DB) |
| `spa-dashboard.md` | SPA / dashboard frontend |
| `event-processor.md` | Async consumer/worker (queue → process → sink) |

## When these are used

- **New service** — on the `new-service` signal at Step 4 PLAN, the architect selects the
  matching topology template and instantiates it before any code exists.
- **Retrofit** — an existing ungoverned service can adopt a harness incrementally: guides
  first (cheap), then sensors one at a time, starting with the danger zones.

## How it flows

1. Architect picks the topology and copies the template into the plan.
2. **Guides** become project rules — sections in the project's `CLAUDE.md` / conventions doc,
   consulted alongside the GROUND codebase map.
3. **Sensors** become executable checks via `skills/fitness-functions`, landing in
   `tests/architecture/` (or the repo's own convention). Some sensors are runtime alert
   rules rather than tests; those go into the service's alerting config and get named in
   `templates/launch-review.md` before ship.
4. Because sensors live in the project's test suite, the existing **pre-push gate** runs
   them forever. No new machinery — the harness rides the gate.

## Adding a new topology

Copy the structure of any existing template exactly: `## Topology`, `## Guides (feedforward)`,
`## Sensors (feedback)`, `## Danger zones`, `## Instantiation`. Every sensor row must name a
concrete implementation (a tool, a rule, an alert) — a sensor you can't implement is a guide
wearing a costume.

## Versioning caveat (honest)

Instantiated harnesses **drift** from their templates, and that's fine. Once instantiated,
the project owns its copy — it will tighten some sensors, delete others, add its own. Treat
templates as starting points, not synced dependencies. Improvements discovered in projects
should be folded back here deliberately, not assumed to propagate.
