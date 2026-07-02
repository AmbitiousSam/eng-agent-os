---
name: product-framing
command: /agentic-os
trigger: "kind == product"
roster:
  always: [requirements, architect]
  optional: [developer, platform-engineer, tech-writer]
phases: [FRAME, PRFAQ, EPIC-BREAKDOWN, SEQUENCE, HANDOFF]
inherits_kernel: true
exit_condition: "PRFAQ approved by human + ordered epic/task specs ready to feed feature-delivery runs"
---

# Playbook: Product Framing

For product-shaped asks — "build me a X", "I want an app that…", "MVP for…". A whole product
is too big for one delivery run, and product judgment (what to build, for whom, what to cut)
is **human-owned**. This playbook converts vision into an executable, ordered backlog.
**It builds NOTHING itself** — every task it emits feeds a normal `feature-delivery` run.

| Phase | Entry gate | Participants | Exit gate |
|---|---|---|---|
| **FRAME** | product ask received | requirements (+architect) | product restated: users, problem, success metrics; explicit **out-of-scope** list |
| **PRFAQ** | framed | requirements, tech-writer if rostered | working-backwards one-pager (`templates/prfaq.md`); **human gate: the human approves the PRFAQ before anything is built** |
| **EPIC-BREAKDOWN** | PRFAQ approved by human | architect + requirements | epics → tasks via `templates/epic.md`; each task written as a normal task-spec with acceptance criteria |
| **SEQUENCE** | epics drafted | architect | tasks ordered by dependency + risk (**riskiest assumptions first**); parallelizable work marked |
| **HANDOFF** | sequence approved | orchestrator | each task queued as a `/agentic-os` feature-delivery run; memory carries decisions between runs; STABILIZE records the product map to memory |

## Rules
- **The human owns product judgment.** No epic breakdown, no code, no scaffolding before the
  PRFAQ is explicitly approved. If the human edits it, re-derive scope from the edited version.
- **Riskiest assumptions first.** Sequence so the tasks most likely to invalidate the product
  land earliest — kill bad ideas cheap.
- **Tasks are real task-specs.** Every task must stand alone: acceptance criteria, dependencies,
  enough context that a feature-delivery run needs no product archaeology.
- **Memory is the thread.** Decisions made here (naming, stack, cut lines) go to
  `.eaos/memory/` so downstream runs inherit them instead of re-litigating.
