---
name: bug-fix
command: /agentic-os
trigger: "kind == bug"
roster:
  always: [requirements, codebase-analyst, developer, code-reviewer]
  optional: [qa-engineer, security-reviewer, sre-observability]
phases: [INTAKE, GROUND, CLARIFY, PLAN, IMPLEMENT, REVIEW, TEST, STABILIZE]
inherits_kernel: true
exit_condition: "reproduction test passes as a permanent regression test; existing suite green"
---

# Playbook: Bug Fix (reproduce-first)

Selected when the task is `kind: bug`. Same kernel, but GROUND runs the **bug-triage** skill and
nothing is fixed until reproduced.

| Phase | Entry gate | Participants | Exit gate |
|---|---|---|---|
| **INTAKE** | bug reported | requirements | spec: expected vs actual, acceptance = "bug gone + regression test" |
| **GROUND** | not greenfield | codebase-analyst | **reproduction** (ideally a failing test) + located source + one-paragraph root cause |
| **CLARIFY** | can't reproduce / ambiguous | analyst → human | reproduced, or escalated with what's needed (version/env/data/logs) |
| **PLAN** | root cause known | developer (+architect if structural) | minimal-fix approach + blast radius (impact map) |
| **IMPLEMENT** | approach agreed | developer | minimal fix applied; repro test now passes |
| **REVIEW** | fix ready | code-reviewer (+security if signaled) | approve; fix stays in scope (no drive-by refactor) |
| **TEST** | review approved | qa-engineer | repro test kept as regression; existing suite green |
| **STABILIZE** | fixed | orchestrator | retro; if latent elsewhere, note pattern → memory |

Reproduce-first, minimal-fix, and keep-the-regression-test are the discipline here. All kernel
gates (pre-push self-review + code checks, human gates) still apply.
