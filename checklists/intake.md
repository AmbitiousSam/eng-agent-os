---
name: intake
description: Load when turning a raw request into a task spec with acceptance criteria, classification and the few questions that genuinely block.
sources: [agents/requirements-analyst.md, skills/requirement-intake/SKILL.md, templates/task-spec.md, orchestrator/routing.yaml (autonomy.clarification, stakes_levels, stakes_rules, complexity_levels, signals, task_kinds), commands/agentic-os.md (Step 1)]
---

# Intake checklist

## Spec shape (`templates/task-spec.md`)
- Restate the goal in one sentence. List scope and an explicit out-of-scope.
- Write every acceptance criterion as a checkable statement ("Returns 429 when a key exceeds N req/min"). No criterion without a way to test it; a criterion nobody can check is a spec bug.
- List assumptions: everything taken for granted.
- Scope check before starting: uncommitted work in the checkout, and open PRs touching the same files (`gh pr list`, `gh pr diff <n> --name-only`). On overlap, stop and ask; another agent or the human may be mid-task.
- Classify: `complexity`, `stakes`, `kind`, `signals`.
- List open questions, each marked `blocking` or `fyi`.

## Questions versus assumptions
- Default to assumptions, not questions. Pick the most reasonable interpretation, record it under Assumptions, proceed. A correction at the end is cheaper than an interruption up front.
- Mark a question `blocking` only if all three hold: it materially changes the approach; it cannot be inferred from the codebase, conventions, task text or a sane default; guessing wrong means real rework. Otherwise it is an assumption.
- Never ask about naming, wording or copy; reversible or low-cost choices (a swappable library, a default value); style or formatting; anything the codebase already demonstrates. Decide and note it.
- Ask: "per-API-key vs per-IP rate limiting"; "hard-delete or soft-delete user data". Assume: date format (locale default), button label, which test runner (the repo's).
- Cap blocking questions at 3 per run and batch them into one round. Zero blockers is the common case; do not manufacture any.

## The two things that are never assumed
- Deliverable-class words in the ask are blocking questions, never assumptions: *workflow, pipeline, CI/CD, deploy, release, migration, rollout, runbook, dashboard*. Ask in one line what is meant, or, if the codebase or a sibling repo demonstrates the house pattern, cite that as the answer in the spec. "Most likely means X" for such a word is a spec bug. (2026-09-09: "recreate the workflows and cdk" was assumed to mean "the runbook"; twelve agents ran a full lifecycle on it; rejected in one line.)
- Identity and attribution constraints become acceptance criteria, not notes: commit author, e-mail form, "only my name", branch name, PR title. Each is checked at commit time with `git log --format='%an <%ae>%n%(trailers)'`. Never add `Co-Authored-By` or "Generated with" trailers unless the human asked for them.

## Deploy-shaped work
- If signals include infra, ci-cd, deploy or data-migration, add the executed-rehearsal criterion: "the deliverable has been executed against real state: dry-run plus local build, plus a real deploy of the smallest unit into a scoped target where one exists, and the result is recorded". Synth, diff, lint and grep are static; a deliverable that has never run cannot be verified (see `checklists/deploy-rehearsal.md`, `checklists/verdict.md`).

## Classification
- `complexity`: trivial (at most 1 file, no logic risk) | small | standard | complex (new service, cross-cutting, or high uncertainty). Make a best-effort tag and note uncertainty; do not block on it.
- `kind`: feature | bug | refactor | chore | incident | question | product | release | venture. A bug spec states expected versus actual and its acceptance is "bug gone plus a regression test". A question wants understanding, not a change. An incident means production is broken now.
- `signals`: db-schema-change, data-migration, public-api, auth, pii, payments, infra, ci-change, perf-critical, new-service, breaking-change, slo-impacting, ui. `new-repo` marks greenfield. Signals decide which checklists load; the research pass may add signals the ask did not mention (the change touches the auth module), and those win over the ask's phrasing.
- `stakes` measures what breaks if the work is wrong, independent of how hard it is:
  - toy: nothing deploys, no real users, money or data at risk (demos, spikes, learning). Skip the launch review and the deploy, platform, operability and documentation work. Security review and independent verification are never stakes-skipped when money or auth signals are present.
  - internal: real users are teammates; blast radius is inconvenience. Skip the launch review unless auth, pii or payments pulls it back.
  - production: external users, money paths, PII, or anything deploy-bound. Nothing is skipped.
