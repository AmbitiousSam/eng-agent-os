---
name: reporting
description: Load when writing the final report, docs, a changelog or an ADR for finished work; claims trace to artifacts, plain language, and the attribution rule.
sources: [agents/tech-writer.md, templates/final-report.md, templates/adr.md, commands/agentic-os.md (Step 9, Step 10 final package), playbooks/feature-delivery.md (DOCUMENT), orchestrator/routing.yaml (autonomy.pre_push.self_review attribution item)]
---

# Reporting checklist

## Compile, never invent
- Every statement traces to an artifact: spec, design, ADR, diff, test output, review notes, verdict table, deploy guide, rehearsal report. If something is not in an artifact, ask; do not guess and do not describe behaviour that was not built.
- Verify README, API docs and changelog entries against the artifacts; fix drift between them (a webhook event list in the README that omits one the deploy guide requires is a defect).
- Keep it factual and tight.

## Final report (`templates/final-report.md`; the last artifact on a task)
- Written for the person who asked, not for another engineer. Plain language, no jargon, no file paths in the body; artifact links at the bottom.
- What you asked for: one or two plain sentences restating the request.
- What was built: what changed and what it does now, from the user's point of view. If nothing shipped (an investigation, a rejected verdict), say so plainly.
- What we checked, and the proof: a short table of requirement, met (Yes / No / Partial), and how we know, in plain words. This is the verdict table translated, not re-graded; a criterion the verdict marked `manual_confirmation_required` or `blocked` is reported as not yet confirmed, never as done.
- Key decisions and why: the top three, one sentence each, why this over the alternative.
- What was NOT done, and risks accepted: everything intentionally left out, deferred or shipped with a known gap, with its practical consequence, stated plainly rather than hedged.
- What needs your decision: the open questions only the human can answer (deploy now or wait; anything to change before it goes live; anything to walk through together).
- The report states the enforcement level each runtime capability actually ran under (v4 §11).
- Deliver the contents of the final report as the closing message, verbatim, not a paraphrase. Then ask whether they want any change, or the destructive deploy step executed.

## Attribution
- Commit author, e-mail and trailers match the human's attribution instruction exactly. No `Co-Authored-By` and no "Generated with" trailer unless the human asked for it. Check with `git log --format='%an <%ae>%n%(trailers)'` before reporting the work as done.

## ADRs (`templates/adr.md`)
- Fields: title, status (accepted | superseded), superseded-by, date, task, deciders.
- Context (the forces and the problem), decision, alternatives considered with why each was rejected, consequences (positive and negative; any dissent preserved as a recorded risk).
- Consequences name the fitness function that enforces the decision (`enforced by tests/architecture/<file>`) or state why the decision is uncheckable (`checklists/build.md`).
- A superseded ADR is marked, not deleted; readers skip superseded ADRs.

## Retrospective
- Record what was not done and why, the loop-backs and what each attempt changed, and any rule the run exposed as missing.
- If the change altered structure, commands or key modules, refresh the codebase map and re-stamp its SHA so the next task starts from an accurate map.
