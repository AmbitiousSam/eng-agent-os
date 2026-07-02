---
name: release
command: /agentic-os
trigger: "kind == release"
roster:
  always: [devops-engineer, sre-observability]
  optional: [platform-engineer, developer, qa-engineer]
phases: [PLAN-ROLLOUT, PREFLIGHT, STAGE, PROGRESS, WATCH, COMPLETE-OR-ROLLBACK, STABILIZE]
inherits_kernel: true
exit_condition: "released at 100% with guardrails green, or cleanly rolled back with cause recorded"
---

# Playbook: Release (progressive delivery, human-executed)

Progressive rollout of an already-built, launch-review-approved artifact. Agents orchestrate
and advise; a **human executes every mutation** (kernel human gates: never deploy, push, or
spend without a human). The launch-review GO (`templates/launch-review.md`) and the pre-push
gate are prerequisites, not steps this playbook re-litigates.

| Phase | Entry gate | Participants | Exit gate |
|---|---|---|---|
| **PLAN-ROLLOUT** | kind == release, artifact identified | devops-engineer (+platform-engineer) | strategy chosen (flag / canary / blue-green); guardrail metrics defined (error rate, latency p99, saturation, business KPI) each with an **explicit abort threshold**; rollback plan written |
| **PREFLIGHT** | rollout plan approved | devops-engineer | launch-review GO verified; artifact immutable (pinned digest/version); rollback **rehearsed**, not just documented |
| **STAGE** | preflight green | devops-engineer, sre-observability | deployed to staging or 1% canary — human executes each step; baseline metrics captured |
| **PROGRESS** | canary green through soak | devops-engineer, sre-observability (+qa-engineer) | staged ramp 1→5→25→100%; each step requires guardrails green for the soak window; agent watches metrics and **advises** proceed / hold / abort; human clicks |
| **WATCH** | ramping or at 100% | sre-observability | full soak window observed; guardrails green; anomalies triaged |
| **COMPLETE-OR-ROLLBACK** | soak complete OR abort threshold breached | devops-engineer, sre-observability | breach → instant rollback recommended (never argue with the guardrail); user-impacting → hand off to `incident-response`. Success → 100% confirmed + cleanup (stale flags, old versions) |
| **STABILIZE** | released or rolled back | orchestrator (+tech-writer via devops notes) | release notes written; what the guardrails caught recorded; patterns → memory |

## Rules

- **Thresholds are pre-committed.** Guardrail abort thresholds are decided in PLAN-ROLLOUT,
  before the ramp starts, and are never renegotiated mid-flight. If the number trips, you
  roll back — the debate already happened.
- **Every ramp step is human-confirmed.** Each promotion (1→5→25→100%) is a destructive-action
  gate: the agent presents evidence and a recommendation; the human executes.
- **Rollback is the default on ambiguity.** A cheap rollback beats a clever diagnosis at 25%
  of traffic. Diagnose after the bleeding stops; if users are impacted, that diagnosis runs
  under the `incident-response` playbook.
- **Advise, never operate.** The agent reads dashboards and CI/CD state; it does not deploy,
  flip flags, shift traffic, or restart anything.
