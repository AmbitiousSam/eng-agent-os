---
name: sensor-feedback
description: >
  Convert any failing check into LLM-optimized fix instructions ("positive prompt
  injection"). Used by the orchestrator whenever a sensor goes red.
---

# Sensor Feedback

Whenever a **sensor** fails — test, lint, build, review finding, fitness function, or a
verifier REJECT — the orchestrator relays it to the fixing agent in this exact structure.
Never a raw log dump: raw output buries the signal and burns context.

## Relay format

| Field | Content |
|---|---|
| **WHAT** | one line: check name + location |
| **EVIDENCE** | the minimal failing output — trimmed, ≤15 lines |
| **WHY** | which acceptance criterion / ADR / gate it blocks |
| **FIX DIRECTION** | the most likely correction, stated as an instruction |
| **VERIFY** | the exact command that proves it's fixed |

## Example

```
WHAT:  test failure — rate-limit headers (tests/api/ratelimit.test.ts)
EVIDENCE:
  ✕ returns Retry-After on 429
    expected headers to contain "retry-after", got undefined
WHY:   blocks AC-3 ("throttled clients are told when to retry"); pre-push gate is red
FIX DIRECTION: add a Retry-After header to the 429 response in src/middleware/ratelimit.ts:84
VERIFY: npm test -- ratelimit
```

## Rules

- If the fix direction is unknown, say **"direction unknown — investigate X first"** rather
  than fabricating a plausible-sounding cause. A wrong direction is worse than none.
- Cap the total relay at **~30 lines** so the fixing agent's context stays lean; link to the
  full log in `artifacts/` instead of pasting it.
- One relay per failure; batch related failures from the same root cause into one relay.
