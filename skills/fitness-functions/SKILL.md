---
name: fitness-functions
description: >
  Turn architecture decisions (ADRs) into enforceable computational checks.
  Used by the architect at PLAN.
---

# Fitness Functions

For each **significant ADR**, emit an executable structural check into the PROJECT — so the
design is policed by CI/pre-push forever, not by prose that drifts the day the architect
leaves the context window.

## Procedure (per ADR)

1. **Classify the decision:**

   | Class | Example |
   |---|---|
   | layering / boundary | "handlers never import repositories directly" |
   | dependency direction | "core depends on nothing in adapters/" |
   | naming / location | "all events live in src/events/, suffixed *Event" |
   | size / complexity | "no module over 400 lines / cyclomatic cap" |
   | API surface | "only index.ts exports cross-package symbols" |

2. **Pick the cheapest enforcement for the stack:**
   - **JS/TS:** `dependency-cruiser` rule or `eslint-plugin-boundaries`.
   - **Python:** `import-linter` contract.
   - **Java:** ArchUnit test.
   - **Any language (fallback):** a small script (grep/AST walk) run inside the test suite,
     exiting non-zero on violation.

3. **Write the check into `tests/architecture/`** (or the repo's own convention), referencing
   the ADR id in its name/comment — e.g. `tests/architecture/adr-007-no-adapter-imports.test.ts`.

4. **Register the check** so it runs with the normal test suite. That makes it automatically
   part of the pre-push gate's `code_checks` — no routing change needed.

5. **Record it in the ADR's Consequences:** `enforced by tests/architecture/<file>`.

## Rule

An ADR **without** a fitness function must state why. Some decisions are genuinely
un-checkable ("prefer boring technology") — say so explicitly in the ADR rather than
leaving the enforcement question silently open.
