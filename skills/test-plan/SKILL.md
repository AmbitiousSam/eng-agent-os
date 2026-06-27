---
name: test-plan
description: >
  Derive a test plan from a task-spec's acceptance criteria (not from the implementation).
  Use during IMPLEMENT/TEST.
---

# Test Plan

From `task-spec.md` acceptance criteria, produce `test-plan.md`:

1. **Map each acceptance criterion → at least one test case.**
2. **Add categories:** happy path, boundary/limits, negative/error paths, concurrency/state,
   and any failure mode raised as a RISK (e.g. dependency-down → fail-open).
3. For each case: id, preconditions, action, expected result, type (unit/integration/e2e).
4. **Coverage check:** every acceptance criterion has a test; flag any that can't be tested.
5. Note which cases are automated vs manual.

Design from the spec so tests aren't biased by the code. Output with `templates/test-plan.md`.
