---
name: incident-response
command: /incident
trigger: "kind == incident"
roster:
  always: [incident-commander]
  optional: [codebase-analyst, sre-observability, developer, security-reviewer]
phases: [INGEST, SCOPE, DIAGNOSE, MITIGATE-ADVISE, RESOLVE-PLAN, RCA, STABILIZE]
inherits_kernel: true
exit_condition: "cited root-cause hypothesis (or explicit unknown+needs), immediate actions delivered, RCA filed to memory"
---

# Playbook: Incident Response (read-only, advisory)

Live-incident process. Selected by `/incident` or `kind: incident`. The **incident-commander**
persona owns it end to end, running `skills/incident-response/SKILL.md`. Speed-first per
`routing.yaml > incident` (`fast_gates`, `mitigate_before_root_cause`): stop the bleeding with
*advised* actions before deep diagnosis; ceremony is cut, kernel safety is not.

**Non-negotiable:** read-only against the cloud. Every mitigation is a numbered step a HUMAN
executes. The tool/agent never deploys, rolls back, restarts, or mutates anything.

| Phase | Entry gate | Participants | Exit gate |
|---|---|---|---|
| **INGEST** | alert/page/report received | incident-commander | service, account/region, symptom, start time, severity guess captured (one sharp question max if critical info missing) |
| **SCOPE** | ingested | incident-commander | blast radius: what/who/since-when/trend → severity set (sev1–4) |
| **DIAGNOSE** | scoped | incident-commander (+codebase-analyst for repo/impact map) | change→symptom correlation done (CloudTrail-first), codebase grounded, **cited hypothesis** (evidence: logs/metrics/commit/file:line) or explicit unknown + what's needed |
| **MITIGATE-ADVISE** | hypothesis or sev1/2 pressure (may run BEFORE diagnosis completes) | incident-commander | numbered immediate actions, smallest-safe-first, each with why + exact step + risk — human-executed |
| **RESOLVE-PLAN** | mitigated/stable | incident-commander (+developer) | the real fix written as a task-spec for a follow-up `/agentic-os` run |
| **RCA** | resolved/stable | incident-commander (+sre-observability) | `templates/incident-rca.md` completed: timeline, root cause vs symptom, detection gaps, action items |
| **STABILIZE** | RCA done | orchestrator | RCA → `.eaos/memory/lessons/`; recurring cause → propose a new guide/sensor (harness steering loop); pattern → memory |

## Notes
- **Mitigate-before-root-cause:** for sev1/sev2, MITIGATE-ADVISE runs as soon as a plausible
  safe action exists — diagnosis continues in parallel. Speed beats certainty when bleeding.
- **Human gates still apply** (kernel): any suggested destructive step is executed only by a
  human; security may veto a risky mitigation.
- **Two entry points, one brain:** this playbook and the standalone `sre-incident-responder`
  tool implement the same process. The tool can serve as this playbook's signal collector
  (read-only) when installed; the skill defines the procedure either way.
- After the incident, the RESOLVE-PLAN task-spec flows into `feature-delivery`/`bug-fix` as a
  normal task — closing the loop from operate back to build.
