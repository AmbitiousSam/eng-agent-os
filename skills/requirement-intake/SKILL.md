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
6. **Deliverable words are never assumptions.** If the ask names a deliverable class —
   *workflow, pipeline, CI/CD, deploy, release, migration, rollout, runbook, dashboard* —
   what exactly is meant is a `blocking` question, not an "Assumption N". Real run
   2026-09-09: "recreate the workflows and cdk" was assumed to mean "the runbook", twelve
   agents ran a full lifecycle on it, and the human rejected the result in one line.
7. **Constraints on identity and attribution become acceptance criteria.** Commit author,
   e-mail form, "only my name", branch name, PR title: each gets an AC checked at commit
   time (`git log --format='%an <%ae>%n%(trailers)'`), never a note.
8. **Deploy-shaped work carries an executed-rehearsal AC.** If signals include infra,
   ci-cd, deploy or data-migration, add: "the deliverable has been executed against real
   state — dry-run plus local build, plus a real deploy of the smallest unit into a scoped
   target where one exists — and the result is recorded". Synth, diff, lint and grep are
   static; a deliverable that has never run cannot be `verified`.

Output with `templates/task-spec.md`. Keep questions few and sharp.
