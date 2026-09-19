---
name: operability
description: Load for new-service, perf-critical, slo-impacting or infra work before it ships; SLOs, alerts, runbook, and the crash-loop and config-drift check.
sources: [agents/sre-observability.md, templates/launch-review.md (Operational Readiness), skills/deployment-guide/SKILL.md (Verification), commands/agentic-os.md (Step 8; the R-OBS-A crash-loop lesson of 2026-09-09), .claude/log.md (2026-09-11 entry)]
---

# Operability checklist

## Define healthy before shipping
- Write the SLOs: what "healthy" means for this change in latency, error rate and capacity. Assess the SLO impact (latency, error budget, capacity) of the change on anything it touches.
- Define the guardrail metrics that would tell you to stop a rollout: error rate, latency p99, saturation, the business KPI, each with an explicit threshold decided before the rollout, not during it.

## Every failure mode gets a signal
- Every new failure mode raised as a risk has a corresponding alert or metric. A risk with no signal is unobserved, not accepted.
- Metrics, logs and traces for the new paths are named in the plan; dashboards cover the new failure modes.
- Logging on the new paths redacts PII and secrets.

## Alerts
- Alerts are actionable. Page on symptoms users feel, not on every blip.
- Each alert names what it means, who it wakes, and the runbook entry it points at.

## Runbook
- Runbook entry for the change: what breaks, how it looks (which alarm, which log line, which metric), what to do, and the rollback path.
- On-call is informed of the change and its blast radius before it ships.
- A feature flag or kill switch exists for risky paths and the runbook says how to use it.

## Crash-loop and config-drift check (part of the rehearsal, before the launch review)
- Compare the task definition, service config or equivalent unit definition in source with the live one returned by `describe-*`. Differences are config drift and need a written disposition.
- Watch the deployed unit through at least one full start cycle: a service that starts, fails health checks and restarts is a crash loop and is a finding with a verdict, not a "follow-up". (2026-09-09: R-OBS-A was filed as follow-up past a launch GO and proven a crash loop only when the human asked for a rehearsal.)
- Confirm the post-deploy checks and the alerts actually fire on the scoped unit deployed during the rehearsal (`checklists/deploy-rehearsal.md`).

## Missing observability is a detection gap
- When an incident RCA asks why detection took as long as it did, the answer names the missing alarm, metric or structural test and whether that gap is now closed (`checklists/incident.md`).
