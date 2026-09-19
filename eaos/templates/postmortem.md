# Postmortem — <incident title>  (blameless)

- **Incident ID:** INC-NNN   ·   **Severity:** sev1 | sev2 | sev3 | sev4
- **Date/Duration:** YYYY-MM-DD, HH:MM–HH:MM (TZ)   ·   **Detected by:** <alert / user / …>
- **Status:** resolved | monitoring
- **Authors:** <agents/humans>

> Blameless: focus on systems and contributing factors, not individuals.

## Impact
<who/what was affected, how much, user-facing symptoms, SLO/error-budget burn>

## Timeline (UTC)
| Time | Event |
|---|---|
| HH:MM | detection / alert fired |
| HH:MM | mitigation started |
| HH:MM | mitigated (bleeding stopped) |
| HH:MM | resolved |

## Root cause
<the underlying contributing factors — why, not who>

## Mitigation & resolution
<what stopped the bleeding, then what actually fixed it>

## What went well / what went wrong / where we got lucky
- Well: <…>
- Wrong: <…>
- Lucky: <…>

## Action items (→ owners)
| Action | Type (prevent / detect / mitigate) | Owner | Link |
|---|---|---|---|
| <e.g. add alert on X> | detect | <who> | <issue> |

## Follow-through
Recurring cause? → propose a new **guide or sensor** (harness steering loop) and record the
pattern in `.eaos/memory/patterns/`. File this postmortem under `.eaos/memory/lessons/INC-NNN.md`.
