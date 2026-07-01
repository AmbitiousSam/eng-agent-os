---
name: feature-delivery
command: /agentic-os
trigger: "kind == feature OR kind == chore OR default"
roster:
  always: [requirements, developer, code-reviewer]
  optional: [codebase-analyst, architect, qa-engineer, security-reviewer,
             devops-engineer, platform-engineer, sre-observability, tech-writer]
phases: [INTAKE, GROUND, CLARIFY, PLAN, IMPLEMENT, REVIEW, TEST, DEPLOY, DOCUMENT, STABILIZE]
inherits_kernel: true
exit_condition: "acceptance criteria met; self-review + code checks green before any push"
---

# Playbook: Feature Delivery (default)

The standard build loop — this is the process v1 shipped, now a playbook. Selected by default
and for `kind: feature | chore`. Runs under the kernel (protocol, war room, memory, human gates,
pre-push gate).

| Phase | Entry gate | Participants | Exit gate |
|---|---|---|---|
| **INTAKE** | task received | requirements (+qa reads) | `task-spec.md`: acceptance criteria + complexity + kind + signals |
| **GROUND** | touches existing code (not greenfield) | codebase-analyst | repo map fresh + `impact-map.md` |
| **CLARIFY** | a blocking question clears the bar | analyst/dev/architect → human | no blocking questions (assume-and-proceed default) |
| **PLAN** | spec approved | architect + developer (+platform/security if signaled) | design buildable; ADRs; no open high-sev risk |
| **IMPLEMENT** | design approved | developer (qa writes tests in parallel) | code compiles; self-tests pass |
| **REVIEW** | implementation ready | code-reviewer (+security if signaled) | review `approve`; no blocking findings |
| **TEST** | review approved | qa-engineer | acceptance criteria pass; existing suite green |
| **DEPLOY** | tests pass | devops + platform + sre (as signaled) | deploy guide + rollback; **pre-push gate: self-review then code checks green** |
| **DOCUMENT** | feature complete | tech-writer | docs trace to artifacts |
| **STABILIZE** | all above done | orchestrator | package + retro + patterns → memory |

Backward edges, trivial fast-path, greenfield path, and the pre-push gate are all kernel
behavior (see `orchestrator/loop.md` and `orchestrator/routing.yaml`).
