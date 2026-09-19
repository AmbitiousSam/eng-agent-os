---
name: review
description: Load when reviewing a diff, and again on the final diff before any push (the pre-push self-review and project code checks).
sources: [agents/code-reviewer.md, templates/review-notes.md, orchestrator/routing.yaml (autonomy.pre_push), commands/agentic-os.md (Step 6, Step 8 pre-push gate), playbooks/feature-delivery.md, playbooks/bug-fix.md]
---

# Review checklist

## Scope of a review
- Read-only: comment, do not edit.
- Judge correctness, edge cases, readability, design adherence, scope adherence and convention fit. Does it work, does it handle the edges, does it read well, does it match the design?
- Acceptance-criteria grading is not the reviewer's call; it belongs to the independent check (`checklists/verdict.md`). Do not grade it twice. Exception: on trivial and small work no independent check runs, so the self-review below is the only criteria gate.

## Findings (`templates/review-notes.md`)
- Verdict: `approve` | `request-changes` | `block`.
- Itemise every finding with severity (blocking, major, minor, nit), `file:line`, and the spec or design reference. When something deviates, cite the exact spec or design clause.
- Distinguish blocking findings from nits. `request-changes` and `block` go back to the maker with the findings; a fix is re-reviewed.
- Check the diff stays within the impact map's scope (no unrelated changes, no drive-by refactor around a bug fix) and matches repo conventions.
- Re-verify previously closed findings on the final diff; note any drift.

## Over-engineering lens (every diff)
- Produce a delete-list: code that should not exist. New dependencies where stdlib, native or platform suffices; wrappers around one call; abstractions with one caller; configuration for imagined futures; rewrites of what the codebase already had. Each entry names what to delete and the smaller replacement (the ladder in `checklists/build.md`).
- Cutting safety, validation or accessibility is never a valid simplification; flag that as a finding instead.
- On `approve`, delete-list items are not blocking: hand them to the maker as optional cleanup and record them on the board so they are not lost.

## Pre-push self-review (a fresh pass on the FINAL diff, not the earlier review)
- The diff matches the spec and design and stays within the impact map (no scope creep).
- Every prior review finding and every QA bug is actually resolved.
- No leftovers: debug logs, TODOs, commented-out code, dead code.
- No secrets, keys, tokens or `.env` committed.
- Commit author, e-mail and trailers match the human's attribution instruction exactly. No `Co-Authored-By` or "Generated with" trailer unless the human asked for it. Check with `git log --format='%an <%ae>%n%(trailers)'`.
- Acceptance criteria all met: only when complexity is below standard (on standard and complex work the independent check owns this; do not grade it twice).
- Any item fails: fix first. Never push unreviewed or flagged code.

## Project code checks (after the self-review)
- Run the project's own test, build and lint with the verified commands from the codebase map. Run all that exist; a missing one is skipped, not failed. This is the actual code passing, not a structural validator.
- Any check red: do not push. Fix, re-check.
- All green: propose the push. Pushing is a destructive action and stays human-confirmed even when green.
