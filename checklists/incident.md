---
name: incident
description: Load when production is broken now (alarm, page, "prod is down"); read-only diagnosis against AWS, human-executed mitigation, and the RCA.
sources: [agents/incident-commander.md, playbooks/incident-response.md, skills/incident-response/SKILL.md, templates/incident-rca.md, templates/postmortem.md, orchestrator/routing.yaml (incident, autonomy.human_gates)]
---

# Incident checklist

## Hard rules
- **Read-only against AWS. Always.** You may call `describe-*`, `get-*`, `list-*`, log/metrics/trace queries, and CloudTrail lookups. You may **never** call a mutating or destructive API (no `restart`, `update-*`, `delete-*`, `rollback`, `deploy`, `scale`, `terminate`, flag toggles, etc.) — not even ones that "should be safe." If a fix requires an action, you **propose it as a numbered, human-executed step**. This is the same `destructive_action` human gate the rest of EAOS uses — it is not weaker here just because it's urgent.
- Allowed call families: `describe-*`, `get-*`, `list-*` on the relevant service; CloudWatch Logs Insights queries; CloudWatch `get-metric-data`; X-Ray `get-trace-summaries` and `batch-get-traces`; CloudTrail `lookup-events`. Never a mutating verb (`update-*`, `delete-*`, `put-*` outside tagging, `restart-*`, `terminate-*`, `rollback`, `scale`, `deploy`).
- Never page, notify or post beyond what is configured. Do not escalate severity or contact additional people on your own initiative.
- Cite everything. A finding without a log excerpt, metric value, trace ID, `file:line` or commit SHA is a hypothesis; label it as one. Never fabricate a plausible-sounding cause.
- Timeboxed urgency, not panic. Immediate actions come fast; the RCA follows. Do not block the mitigation list on finishing the RCA. For sev1 and sev2, mitigation advice runs as soon as a plausible safe action exists and diagnosis continues in parallel.
- Security may veto a risky mitigation.

## Ingest and scope
- Capture: alarm name, service, account and region, severity, start time, links (dashboard, log group, incident channel or ticket). If critical information is missing, one sharp question at most.
- Blast radius: what, who, since when, trend. Set severity sev1 to sev4 (sev1 highest).

## Diagnose
- Pull CloudWatch metrics, logs and traces for the window from start minus 30 minutes to now.
- Query CloudTrail for changes in that window: deploys, config, IAM and security-group changes, scaling events. A change immediately before the symptom is the top suspect; chase it first. CloudTrail is usually the highest-value single signal.
- Map the affected service to its repo through the codebase map; if the service is not mapped, build the map first (`checklists/research.md`). If the suspect is a deploy, find the commits (`git log --since=<window>`, `git blame`, `git show`) correlated with the CloudTrail deploy events; if it is config or infra, find the IaC file that owns it. Build a mini impact map for the suspect change: what it touched, callers, what else could be affected.
- State a hypothesis with a confidence level backed by cited evidence, or say plainly that you do not have one and list what is still needed.

## Immediate actions (human-executed)
- Numbered, smallest safe mitigation first. Each item: what, why (tied to the diagnosis), the exact command or console step, and the blast radius. Never run any of them yourself.
- Rollback is the default on ambiguity when users are impacted.

## Later actions
- The real fix is written as a task spec for a follow-up build run, with acceptance criteria.

## RCA (`templates/incident-rca.md`; blameless)
- One canonical home: `.eaos/incidents/<incident-id>/RCA.md`. Never a second copy elsewhere.
- Header: severity, services, account and region; start, detected, mitigated, resolved timestamps; detection-to-mitigation and total impact durations.
- Impact: what broke, for whom, how badly, with metrics and logs cited.
- Timeline, every row cited (log, metric, CloudTrail event, commit).
- Root cause: the actual cause, not the symptom, in one paragraph with evidence. Contributing factors (missing alarm, thin coverage on the changed path, config drift).
- Detection gap: why detection took this long; was there a guide, sensor, alarm, structural test or fitness function that should have caught it earlier, and is that gap now closed or still open.
- Response retro: what worked and what did not in the response itself. What went well, wrong, and where luck helped.
- Immediate actions taken (link to `report.md`); action items with type (prevent, detect, mitigate), owner, target and linked task.
- Confidence in the root cause and what would raise it.

## Outputs
- `.eaos/incidents/<incident-id>/report.md` (immediate and later actions), `RCA.md`, `timeline.md`.
- A one-line pointer at `.eaos/memory/lessons/<incident-id>.md` linking to the RCA; do not duplicate the RCA into memory. A recurring or systemic cause proposes a new guide or sensor.
- Optional short summary (severity, one-line status, immediate actions, path to the report) to a configured Microsoft Teams incoming webhook; the report files are the source of truth.
