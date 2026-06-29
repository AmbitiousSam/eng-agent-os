# EAOS Memory

Durable project knowledge that makes the OS smarter over time. The orchestrator reads this at
PLAN (to reuse) and writes at STABILIZE (to capture).

> At runtime this lives **project-local** at `./.eaos/memory/` (created on first run), so each
> codebase accumulates its own decisions. This folder in the repo is the template/reference.

```
.eaos/memory/
├── decisions/   # ADRs (immutable). One file per decision: adr-NNN-<slug>.md
├── patterns/    # Reusable solutions: <name>.md  (e.g. distributed-rate-limit.md)
├── lessons/     # Retrospective notes per task: T-NNN.md  (what went well / to improve)
└── codebase/    # Cached repo map: map.md + map.meta (git SHA it was built at)
```

The **codebase map** is the team's understanding of THIS repo (structure, run/test commands,
conventions, key modules, danger zones). It's built once by the Codebase Analyst at the first
GROUND phase and refreshed incrementally when git HEAD moves — so tasks don't re-read the whole
tree every time. See `agents/codebase-analyst.md` and `skills/codebase-map`.

**Rules**
- ADRs are append-only; supersede with a new ADR rather than editing.
- Before deriving a design, check `decisions/` and `patterns/` for an existing answer.
- A pattern is promoted from a lesson only after it's worked on ≥2 tasks.

**Retention (so memory doesn't become a context swamp)**
- **`index.md`** is the only thing always loaded at PLAN — a one-line summary + link per active
  decision/pattern. Full files are pulled only when relevant. Keep the index curated.
- **Decisions** carry a `Status` and an optional `Superseded-by: ADR-NNN`. The orchestrator
  loads only `accepted` ADRs; superseded ones stay for history but are skipped.
- **Patterns** that haven't been used in N tasks (default 10) get archived to
  `patterns/_archive/` and dropped from the index.
- **Lessons** older than a release can be summarized into a pattern (or pruned); they're
  retrospective notes, not long-term truth.
- **Codebase map** is regenerated on git drift; it's a cache, never hand-edited.
- Periodically run a memory pass: merge duplicate patterns, mark stale decisions superseded,
  and rebuild `index.md`. Store conclusions, never transcripts.
