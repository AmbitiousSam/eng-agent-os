---
name: test-adequacy
description: Load when deciding whether the tests for a change are enough: deriving cases from the criteria, negative and failure-mode coverage, regression, and what a check may touch.
sources: [agents/qa-engineer.md, skills/test-plan/SKILL.md, templates/test-plan.md, playbooks/bug-fix.md, playbooks/feature-delivery.md, commands/agentic-os.md (Step 7), docs/specs/2026-09-17-eaos-v4-architecture.md (R-2 snapshot before and after), docs/research/2026-09-17-software-factories-study.md (rule 10)]
---

# Test adequacy checklist

## Derive from the criteria, not the implementation
- Design tests from the spec's acceptance criteria. Read the code only to run it, never to derive the expected result; a test derived from the code confirms the code.
- Map every acceptance criterion to at least one test case. A criterion with no test is not done.
- The design's risk register is input: medium and low risks there become test cases; any failure mode raised as a risk (dependency down, fail-open or fail-closed) gets a case.
- Flag any criterion that cannot be tested. That is a spec bug, and it blocks approval rather than being silently skipped.

## Coverage categories (`templates/test-plan.md`)
- Happy path.
- Boundaries and limits.
- Negative and error paths: invalid input, absent or invalid signature returns 4xx and mutates nothing, malformed events do not cause retry storms.
- Concurrency and state: races, idempotent replays, crash windows between two writes.
- Failure modes from the risk register.
- For each case record: id, criterion, category, preconditions, action, expected result, type (unit, integration, e2e), automated or manual.

## Regression means the existing suite
- Run the existing test suite with the verified commands from the codebase map, not only the new tests. Confirm nothing in the blast radius (impact map) broke.
- A bug fix keeps its reproduction test as a permanent regression test; it must fail before the fix and pass after.
- Where the harness offers scoped regression (`codegraph affected`), use it in addition to, not instead of, the full suite.

## What a check may touch
- Test scripts and checks must not mutate product files or live state. A check that rewrites product files (a formatter, a lockfile update) changes the code it claims to verify; its evidence is recorded against neither snapshot and the run is reported as snapshot-unstable (v4 R-2).
- Checks against real infrastructure use dry-run, `describe-*` and `list-*` calls only; a check needing a real mutation is a rehearsal step with human confirmation (`checklists/deploy-rehearsal.md`), not a test.
- Test doubles and harness dependencies stay contained (dev-only, no references from product code, no stray files).

## Legibility
- Capture the why in the test name or comment: which criterion it proves and what a failure means, so a later fresh context can tell a wrong test from a wrong implementation.
- Note which cases are automated and which are manual; a manual case is evidence only when someone ran it and recorded the result.

## After running
- Bugs found go back to the maker with the failing case; re-test after the fix.
- Exit bar: every acceptance criterion has a passing test or a recorded reason it cannot; existing suite green; critical paths covered.
