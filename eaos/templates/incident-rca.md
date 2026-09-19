# RCA — <incident-id>: <one-line title>

- **Severity:** SEV<N> · **Service(s):** <…> · **Account/Region:** <…>
- **Start:** <timestamp> · **Detected:** <timestamp> · **Mitigated:** <timestamp> · **Resolved:** <timestamp>
- **Detection → mitigation:** <duration> · **Total impact duration:** <duration>

## Impact
<what broke, for whom, how badly — cite metrics/logs>

## Timeline (cited)
| Time | Event | Source |
|---|---|---|
| … | … | log/metric/CloudTrail/commit link |

## Root cause
<the actual cause, not the symptom — one paragraph, with evidence citations>

## Contributing factors
- <e.g. missing alarm, insufficient test coverage on the changed path, config drift>

## Detection gap
Why did it take this long to detect? Was there a guide or sensor (per harness-engineering
thinking) that *should* have caught this earlier — a missing alarm, a missing structural test,
a missing fitness function? Is that gap now closed, or still open?

## Response retro
What worked well, what didn't, in the response itself (not the code).

## Immediate actions taken
(link to `report.md` in this incident's folder — the human-executed mitigation list)

## Action items (later actions)
| Item | Owner | Target | Linked task |
|---|---|---|---|
| … | … | … | T-NNN |

## Confidence
State your confidence in this root cause and what, if anything, would raise it.
