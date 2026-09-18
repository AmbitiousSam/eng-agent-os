---
name: build
description: Load before designing or writing a code change; covers the buildability check, the least-code ladder, decisions as ADRs and the handoff bar.
sources: [agents/developer.md, agents/architect.md, playbooks/feature-delivery.md, playbooks/bug-fix.md, skills/fitness-functions/SKILL.md, templates/adr.md, orchestrator/routing.yaml (autonomy.pre_push.code_checks), docs/research/2026-09-17-software-factories-study.md (rules 9 and 10)]
---

# Build checklist

## Before writing
- Read the code the change touches first. Be lazy about the solution, never about reading.
- Search before assuming: never conclude that something is unimplemented or absent from one failed search. Try the other names, locations and conventions the repo uses (see `checklists/research.md`).
- Buildability check before writing: review the design for implementability and raise blocking questions now, not after building. Do not start coding with an open blocking question. A design exits planning only when the person building it agrees it can be built.
- Design must fit the real code, files and conventions in the repo map and impact map, not an idealised version.
- A bug is not fixed until it is reproduced (`checklists/research.md`). Plan a minimal fix with its blast radius.

## The ladder: write the least code that works
- Stop at the first rung that holds: 1. Does this need to exist? (YAGNI, skip it) 2. Already in this codebase? (reuse) 3. Stdlib does it? 4. Native platform feature? (`<input type="date">` beats a picker library) 5. Already-installed dependency? 6. One line? 7. Only then: the minimum that works.
- Never on the chopping block: trust-boundary validation, error handling, security, accessibility.
- Prefer the simplest design that meets the acceptance criteria. Justify any added dependency.

## While writing
- Keep changes scoped to the spec and the impact map. Edit the files the impact map names; follow the repo's conventions; no drive-by refactors. A bug fix stays in scope.
- If the impact map turns out incomplete, re-localise (research pass) rather than guess.
- No placeholders, stubs, TODO-later code, commented-out or dead code, or debug logging in the deliverable. A stub that never ran cannot be verified.
- One source of truth per fact: state, configuration and documentation each have one authoritative home; change the home, not a copy. A second store or cached copy of something that already has an authoritative home needs a written reconciliation rule or it does not go in.
- Capture the why: in the test name or comment, the commit message and the PR description, so a later fresh context can tell a wrong test from a wrong implementation.
- Produce a PR description and self-test notes with the change.

## Decisions
- Every significant trade-off gets an ADR (`templates/adr.md`): context, decision, alternatives considered and why rejected, consequences. Dissent is preserved as a recorded risk. A replaced ADR is marked superseded with `Superseded-by`.
- Turn each significant ADR into a fitness function: classify it (layering or boundary, dependency direction, naming or location, size or complexity, API surface); pick the cheapest enforcement for the stack (JS/TS: `dependency-cruiser` or `eslint-plugin-boundaries`; Python: `import-linter`; Java: ArchUnit; any language: a small grep or AST script inside the test suite exiting non-zero on violation); write it under `tests/architecture/` named for the ADR id (`adr-007-no-adapter-imports.test.ts`); register it with the normal suite so it rides the pre-push checks; record `enforced by tests/architecture/<file>` in the ADR's consequences.
- An ADR without a fitness function must say why ("prefer boring technology" is genuinely uncheckable; say so rather than leaving enforcement silently open).
- Take platform and security risks raised against the design seriously; a high-severity security finding blocks until mitigated (`checklists/security.md`).

## Before handoff
- Run the project's own checks with the verified commands from the codebase map (if absent, detect from package.json, Makefile, pyproject, cargo, go): test, build, lint. Run all that exist; a missing one is skipped, not failed. Any red means no handoff.
- Also run the existing suite, not only the new tests, so nothing in the blast radius silently broke.
- Handoff as "ready for review" carries passing, in-category evidence bound to the code it ran against (v4 R-2, R-4). A handoff without it is "blocked, requesting help" and cannot support a success claim.
- The final diff gets the self-review in `checklists/review.md` before any push.
