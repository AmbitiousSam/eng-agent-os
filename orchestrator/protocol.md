# EAOS Communication Protocol

Communication is **baked into the OS** — it does not rely on any harness feature (no Agent
Teams, no peer-messaging plugin). The orchestrator owns coordination through files it
controls. This makes the system portable, autonomous, auditable, and resumable.

## The model: orchestrator-mediated, file-based

```
            ┌─────────────────────────────────────────────┐
            │            ORCHESTRATOR (the /agentic-os run) │
            │  - sole writer of the war room                │
            │  - spawns subagents, collects their messages  │
            │  - relays messages between agents             │
            │  - enforces gates + convergence rule          │
            └───────┬───────────────────────────┬──────────┘
        spawn (Task)│                            │append
                    ▼                            ▼
            ┌──────────────┐            ┌────────────────────┐
            │  subagent     │ returns   │ .eaos/<id>/warroom │
            │ (architect…)  │ messages  │  .md  (append-only)│
            │ writes its    │──────────▶│  + artifacts/      │
            │ own artifacts │           └────────────────────┘
            └──────────────┘
```

**Rule 1 — One writer.** Only the orchestrator writes `warroom.md`. Subagents return their
messages as their final output; the orchestrator appends them. This eliminates write races
even when agents run in parallel.

**Rule 2 — Agents own their artifacts.** Subagents write their distinct work-product files
(`design-doc.md`, `test-plan.md`, code, etc.) under `.eaos/<id>/artifacts/`. Distinct files →
no races. They reference artifacts by path; never paste large blobs into messages.

**Rule 3 — Peer messaging = orchestrator relay.** "A asks B" means A returns a QUESTION, the
orchestrator passes it into B's prompt, B returns the answer, the orchestrator records both.

**Rule 4 — Resumable.** State lives entirely in `.eaos/<id>/`. If a run stops, re-reading the
war room + artifacts lets the orchestrator continue from the last completed phase.

## Channels

1. **War Room** — `.eaos/<task-id>/warroom.md`, append-only, orchestrator-written. The team's
   shared log and single source of truth.
2. **Returned messages** — each subagent's final output is a block of protocol messages.
3. **Artifacts** — `.eaos/<task-id>/artifacts/…` durable work products.

## Message types

| Type | Meaning |
|---|---|
| `PROPOSE` | Here is my plan / design / implementation |
| `QUESTION` | Blocking clarification; the asker waits for an answer |
| `CHALLENGE` | I disagree — must include evidence or a concrete alternative |
| `REVIEW` | Structured feedback: `approve` / `request-changes` / `block` |
| `RISK` | A flagged risk with severity (`low`/`med`/`high`) + mitigation |
| `DECISION` | A resolved choice; becomes an ADR in `.eaos/memory/decisions/` |
| `HANDOFF` | My part is done; here's what's ready and what's next |
| `STATUS` | progress / blocked / done |

## Message schema (what a subagent returns; what the orchestrator appends)

```yaml
- id: msg-014                 # orchestrator assigns sequential ids
  from: developer
  to: [architect]            # agent name(s), "all", or "human"
  type: QUESTION
  ref: .eaos/T-101/artifacts/design-doc.md#caching
  priority: blocking         # blocking | normal | fyi
  body: >
    One or two tight sentences: the issue + what you need to proceed.
```

## Convergence rule (resolving disagreement)

1. A CHALLENGE must carry evidence or a concrete alternative, else the orchestrator drops it.
2. The orchestrator relays it back **once** for a single reply exchange.
3. Still split? The **phase owner decides** — architect owns design, developer owns
   implementation, QA owns test adequacy. **Security may `block` on a high-severity finding
   (hard veto).**
4. The orchestrator records the outcome as an ADR and preserves dissent as a noted RISK.
5. Only irreducible product/business trade-offs escalate to the **human**.

This caps "agents arguing forever" at one round + a deterministic owner — and keeps the run
autonomous.

## Human-gate policy

The run is autonomous except at these gates (see also `agentic-os.md` Step "Autonomy"):
blocking product questions, irreducible product/business trade-offs, deadlocks
(> `max_same_issue_loops`), destructive/costly real-world actions (deploy/push/migrate/spend),
and un-mitigable high-severity security findings. Everything else proceeds without asking.
