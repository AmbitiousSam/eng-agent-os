---
name: triage
description: >
  Scheduled discovery — scan the repo's health signals and produce a prioritized
  triage inbox; propose tasks, never start them without approval.
---

# Triage (scheduled discovery)

The discovery step of the loop: the OS finds work instead of waiting for it. This skill
is **strictly read-only** — it observes, correlates, and proposes. It never fixes.

## Scan (all read-only)

1. **CI status.** Latest pipeline runs, failing tests, flaky jobs. Note run IDs.
2. **TODOs/FIXMEs.** `grep -rn "TODO\|FIXME\|HACK\|XXX"` across source (skip vendor/,
   node_modules/, .eaos/). Cluster by area; old ones matter more than fresh ones.
3. **Stale branches.** Branches with no commits in >30 days that are ahead of main —
   abandoned work or unlanded fixes.
4. **Dependency alerts.** If present: audit output, Dependabot/Renovate files, lockfile CVEs.
5. **Recurring lessons.** Read `.eaos/memory/lessons/` — anything hit ≥2 times is a
   systemic issue worth a proposed task.
6. **Issue tracker** (only if an MCP is configured): open bugs with no owner, aging P1/P2s.

## Output

Write `.eaos/memory/triage.md`:

```
# Triage Inbox — <date>

| # | Finding | Evidence | Proposed action | Suggested playbook | Priority |
|---|---------|----------|-----------------|--------------------|----------|
| 1 | Flaky auth test | ci run #482, test_login:88 | fix flake, quarantine if needed | bug-fix | P1 |
```

Priorities: **P1** breaks people now, **P2** will break soon or blocks work, **P3** hygiene.

## Rules

- **Every finding cites evidence** — file:line, CI run ID, log excerpt, branch name.
  No evidence, no entry.
- **Dedupe** against existing `triage.md` entries and open tasks in `.eaos/`. Update
  the evidence on a repeat sighting instead of duplicating the row.
- **NEVER auto-start work.** The human reads the inbox, picks items, and runs
  `/agentic-os <item>` on each — or approves a batch. Triage produces candidates only.
- **Tag the playbook** that fits each item: `bug-fix`, `feature-delivery`, or
  `investigation` — so the pick-up cost is one command.

## Scheduling

Designed to run unattended on a schedule (cron, scheduled task, or a nightly CI job)
or on demand via `/triage`. Since it is read-only and dedupes itself, running it too
often is harmless.
