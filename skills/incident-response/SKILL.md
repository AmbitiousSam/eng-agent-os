---
name: incident-response
description: >
  Investigate a production incident: ingest the alert, scope blast radius, diagnose using AWS
  signals correlated with the codebase, produce immediate vs later actions, and write the RCA.
  Use when responding to a live incident (alarm, page, or "prod is broken" report).
---

# Incident Response

`playbooks/incident-response.md` is the canonical procedure — phase sequence
(INGEST → SCOPE → DIAGNOSE → MITIGATE-ADVISE → RESOLVE-PLAN → RCA → STABILIZE), entry/exit
gates, and roster all live there. Follow it; the `incident-commander` persona
(`agents/incident-commander.md`) owns execution end to end and adds commander-specific
technique for DIAGNOSE/MITIGATE-ADVISE/RCA. This skill exists to ground the codebase side of
DIAGNOSE and to pin the AWS access surface — it does not restate the phases.

**Ground in the codebase (DIAGNOSE).** Map the affected service to its repo via
`.eaos/memory/codebase/map.md` (run `codebase-map` first if this service isn't mapped yet).
Find the commit(s) in the suspect deploy; build a mini impact map (what it touched, callers,
what else could be affected) the same way GROUND does for a normal task.

**RCA and memory.** The RCA has one canonical home: `.eaos/incidents/<incident-id>/RCA.md`
(`templates/incident-rca.md`). At STABILIZE, write a one-line pointer to
`.eaos/memory/lessons/<incident-id>.md` linking back to it — don't duplicate the RCA into
memory. Promote to `.eaos/memory/patterns/` if the failure mode looks recurring.

## AWS read-only surface (use these call families only)
`describe-*`, `get-*`, `list-*` on the relevant service; CloudWatch Logs Insights queries;
CloudWatch metrics `get-metric-data`; X-Ray `get-trace-summaries`/`batch-get-traces`;
CloudTrail `lookup-events`. Never a mutating verb (`update-*`, `delete-*`, `put-*` outside of
tagging, `restart-*`, `terminate-*`, `rollback`, `scale`, `deploy`).
