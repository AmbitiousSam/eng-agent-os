# Impact Map — T-NNN: <title>

**Task kind:** feature | bug | refactor | chore

## Files to change
| File | Symbol / area | Why | Risk |
|---|---|---|---|
| `path:line` | `funcName` | <reason> | low/med/high |

## Blast radius (callers / dependents to check)
- `path:line` calls/depends on the above → verify still correct.

## Tests in scope
- Existing: `<test files that cover this>` (must still pass)
- New/updated: `<tests to add>`

## Config / migrations / infra touched
- <…or "none">

## Danger zones hit
- <auth / migration / payment / public-api / none> → signals: [<tags>]

## Confidence
- Sure: <…>
- Verify during PLAN: <…>

---
## (bug tasks only)
**Reproduction:** <failing test path or exact steps>
**Root cause:** <one paragraph — why, not just where>
**Other latent sites:** <same bug elsewhere, or none>
