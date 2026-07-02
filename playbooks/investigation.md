---
name: investigation
command: /agentic-os
trigger: "kind == question"
roster:
  always: [codebase-analyst]
  optional: [architect, sre-observability, security-reviewer]
phases: [FRAME, INVESTIGATE, ANSWER, STABILIZE]
inherits_kernel: true
exit_condition: "a cited answer (file:line / metrics / docs evidence) or an explicit unknown + what would resolve it"
---

# Playbook: Investigation (read-only)

For when the task is a **question**, not a change: "how does auth work here?", "why is this
slow?", "what would it take to migrate X?", "is this pattern safe?". A complete engineering
team doesn't just build and fix — it explains, assesses, and estimates. This playbook is that
capability. Strictly read-only: no code is modified.

| Phase | Entry gate | Participants | Exit gate |
|---|---|---|---|
| **FRAME** | question received | codebase-analyst | the question restated precisely + what evidence would answer it |
| **INVESTIGATE** | framed | codebase-analyst (+architect for design questions, +sre for perf/runtime, +security for risk) | evidence gathered: repo map/impact map, code paths (`file:line`), git history, metrics/docs as relevant |
| **ANSWER** | evidence sufficient OR exhausted | lead participant | a direct answer with citations; confidence stated; unknowns + what would resolve them listed explicitly |
| **STABILIZE** | answered | orchestrator | answer archived to `.eaos/<id>/artifacts/answer.md`; reusable insight → memory patterns; if the answer implies work, a task-spec drafted for a follow-up run |

## Rules
- **Cite or say unknown.** Every claim traces to `file:line`, a commit, a metric, or a doc.
  No confident hand-waving — an explicit "unknown, here's what would resolve it" beats a guess.
- **Read-only.** If the investigation reveals something worth changing, the output is a
  *task-spec* for a `feature-delivery`/`bug-fix` run — never an in-place edit.
- **Cheap by default.** Usually one agent (codebase-analyst); specialists join only when the
  question is architectural, performance, or security shaped. Trivial questions ("where is X
  defined?") skip straight to ANSWER.
