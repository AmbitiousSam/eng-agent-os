# EAOS Roadmap

## Engineering phases

| Phase | Goal | Build | Done when |
|---|---|---|---|
| **0 Bootstrap** | installable on any machine | `setup.sh` clones agency-agents + installs OS | agents callable in Claude Code |
| **1 MVP loop** | clarify + co-plan + review | orchestrator + requirements/architect/developer/reviewer, linear | one task runs end-to-end |
| **2 QA + iteration** | tests + backward loops | qa-engineer, TEST phase, request-changes loop, convergence rule | bugs route back & resolve |
| **3 Ops + specialists** | full team + parallelism | security/devops/platform/sre/tech-writer + signals + in-phase parallel | specialists activate only when signaled |
| **4 Memory + efficiency** | learn + stay cheap | ADRs/patterns/lessons, cache-reuse, token budget, model overrides | repeat tasks reuse prior decisions |
| **5 Hardening + portability** | tune + port | refine skip rules from real runs; LangGraph escape hatch; convert to a 2nd harness | runs on a non-Claude-Code harness |
| **6 Business pack** | expand to a company | executive + GTM agent pack on same machinery | a business task runs the same loop |

## MVP definition (Phase 1)
4 agents, one linear loop, one war-room file, no parallelism, no specialists:
`INTAKE → CLARIFY → PLAN(architect+developer) → IMPLEMENT → REVIEW`.
Proves the three hard things: clarification-before-build, co-planning, review loop.

## Phase 6 — business/startup extension (preview)
The orchestrator, protocol, routing engine, war room, and memory **do not change**. You add:
- `agents/business/`: CEO, CTO, Product Manager, Business Planner, Finance, Marketing, Sales.
- a `loop.md` business profile: `opportunity → product spec → GTM → financial model → build
  (delegates to the engineering loop) → launch → measure`.
- new signals: `revenue-impact`, `fundraising`, `gtm`, `pricing`, `hiring`.
- model routing extends unchanged (strategy/finance → reasoning; copy/format → cheap).

Result: EAOS becomes the **engineering division** of a larger Agentic Operating Company.
```
