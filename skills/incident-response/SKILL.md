---
name: incident-response
description: >
  Investigate a production incident: ingest the alert, scope blast radius, diagnose using AWS
  signals correlated with the codebase, produce immediate vs later actions, and write the RCA.
  Use when responding to a live incident (alarm, page, or "prod is broken" report).
---

# Incident Response

Follow this procedure (the `incident-commander` persona owns it end to end):

1. **Ingest.** Extract: service, account/region, alarm/metric, severity guess, start time,
   links. Missing something critical (which service/account)? Ask one sharp question, don't guess.

2. **Scope.** What's broken, for whom, since when, trending worse/stable/recovering. This sets
   severity and urgency.

3. **Correlate change → symptom.** Query CloudTrail for deploys/config/IAM/scaling changes in
   the window just before the symptom started. A change right before the break is the top
   suspect — chase it first, before broader log spelunking.

4. **Ground in the codebase.** Map the affected service to its repo via
   `.eaos/memory/codebase/map.md` (run `codebase-map` first if this service isn't mapped yet).
   Find the commit(s) in the suspect deploy; build a mini impact map (what it touched, callers,
   what else could be affected) the same way GROUND does for a normal task.

5. **State a cited hypothesis.** Root cause + confidence + the evidence (log excerpt, metric,
   trace ID, `file:line`, commit SHA) that backs it. No confident cause found? Say so and list
   what's needed — never fabricate.

6. **Immediate actions — fast.** Numbered, smallest-safe-mitigation-first, each with why + exact
   command/step + risk. Human-executed only; never run them yourself (AWS access is read-only).

7. **Later actions.** The real fix, written as a normal task spec for a follow-up `/agentic-os` run.

8. **RCA.** Use `templates/incident-rca.md`: timeline, root cause vs symptom, contributing
   factors, detection-gap analysis, response retro, action items with owners, and whether a
   guide/sensor gap caused this and whether it's now closed.

9. **Memory.** Write `.eaos/memory/incidents/<id>.md`; promote to `.eaos/memory/patterns/` if
   the failure mode looks recurring.

## AWS read-only surface (use these call families only)
`describe-*`, `get-*`, `list-*` on the relevant service; CloudWatch Logs Insights queries;
CloudWatch metrics `get-metric-data`; X-Ray `get-trace-summaries`/`batch-get-traces`;
CloudTrail `lookup-events`. Never a mutating verb (`update-*`, `delete-*`, `put-*` outside of
tagging, `restart-*`, `terminate-*`, `rollback`, `scale`, `deploy`).
