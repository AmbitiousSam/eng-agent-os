# EAOS agents ↔ agency-agents

EAOS ships **11 coordination-aware engineering personas** (this folder), including the
`codebase-analyst` that maps existing repos. `setup.sh` also
installs the [`agency-agents`](https://github.com/msitarzewski/agency-agents) library under
the `agency-` prefix in `~/.claude/agents/`.

**How they relate:**
- EAOS personas are the **team roles in the loop** — they know the protocol, the war room,
  and the convergence rule.
- agency-agents personas are **deep specialists** (frontend wizard, etc.) with no awareness
  of the loop.
- An EAOS agent (usually `developer`) **delegates** to an agency persona for specialized work
  via the orchestrator's `Task` tool, then folds the result back into the loop. This avoids
  duplicating specialist expertise while keeping coordination in one place.

**Naming:** keep EAOS persona `name:` values unique from the `agency-` prefixed ones so both
can coexist. If you want an agency persona to participate in the loop directly, copy it here
and add the protocol section (Activates / Reads / Produces / May send / Rules).

**Model tiers** are declared per persona in frontmatter and can be overridden in
`orchestrator/routing.yaml`.
