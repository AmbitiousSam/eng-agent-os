# Memory Index

The lightweight, always-loaded summary of project memory. The orchestrator reads this at PLAN
and only opens a full file when a line looks relevant. Keep entries to one line. Rebuild during
the periodic memory pass.

> At runtime this is `./.eaos/memory/index.md`. This repo copy is the template.

## Decisions (accepted ADRs)
<!-- - ADR-007 · distributed rate limiting via Redis token-bucket (T-101) -->

## Patterns (reusable, used ≥2×)
<!-- - distributed-rate-limit · shared token bucket, fail-open + alert -->

## Lessons (recent, prunable)
<!-- - T-101 · platform challenge surfaced a latency budget check; keep that prompt -->

## Codebase
<!-- - map.md built @ <git-sha>; danger zones: auth/, migrations/ -->
