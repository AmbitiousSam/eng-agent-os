---
name: requirement-intake
description: >
  Turn a raw engineering request into a structured task-spec with acceptance criteria,
  complexity score, signal tags, and blocking questions. Use at INTAKE.
---

# Requirement Intake

Given a raw request, produce a `task-spec.md`:

1. **Restate** the goal in one sentence; list explicit scope and out-of-scope.
2. **Acceptance criteria** — write each as a checkable statement ("Returns 429 when a key
   exceeds N req/min"). No criterion without a test.
3. **Assumptions** — everything you're taking for granted.
4. **Classify**
   - `complexity`: trivial (≤1 file, no logic risk) / small / standard / complex (new
     service, cross-cutting, or high uncertainty).
   - `signals`: tag from `orchestrator/routing.yaml` — auth, pii, payments, public-api,
     perf-critical, new-service, infra, data-migration, breaking-change, ui, …
5. **Open questions** — mark each `blocking` (must answer before PLAN) or `fyi`.

Output with `templates/task-spec.md`. Keep questions few and sharp.
