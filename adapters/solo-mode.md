# EAOS Solo Mode — the honest degraded mode for tools without subagents

Use this instead of role-playing the EAOS personas sequentially in a single context. Role-play
keeps the ceremony (persona names, message types, phase headers) but not the mechanism that
makes EAOS worth its token cost: a single context reviewing and verifying its own work is not
independent review, no matter what name you give it. Solo mode drops the ceremony it can't
actually enforce and keeps the parts that are real work regardless of tooling — plus the one
trick that restores genuine independence in any tool.

**Use this when:** your tool has no subagent feature, or you aren't sure its subagents give each
spawn a truly separate context (no shared history, no visible prior reasoning). If your tool
*does* give you that isolation, prefer a real adapter (`cursor/`, `windsurf/`, `codex/`) and
actual subagent spawns instead of this file.

## What you keep

1. **GROUND.** Before writing code, build (or refresh) a repo map and a task-specific impact
   map — same content as `skills/codebase-map/SKILL.md` and `templates/impact-map.md`: stack,
   structure, verified test/build/lint commands, conventions, danger zones, and exactly which
   files/symbols/tests this task touches. Do this even solo — guessing at scope is how single
   agents drift.
2. **A written task spec with testable acceptance criteria.** Use `templates/task-spec.md`'s
   shape: goal, scope, out-of-scope, numbered acceptance criteria, assumptions, open questions.
   Write it down before implementing, even if no one else will read it — it's what the second
   session (below) grades against.
3. **Assume-and-proceed clarification.** Don't stall on non-blocking questions. Ask only if the
   answer would change the approach, can't be inferred from the codebase or task text, and is
   expensive to get wrong. Otherwise pick the sane default, record it under "Assumptions" in the
   spec, and keep moving.
4. **Pre-push checklist (self-review).** Before finishing, review your own final diff against
   the spec and impact map:
   - matches spec + design, stays in scope (no drive-by refactors)
   - every issue you noticed mid-build is actually resolved
   - no leftovers: debug logs, TODOs, commented-out or dead code
   - no secrets/keys/tokens or `.env` committed
   - all acceptance criteria met (in solo mode there is no separate verifier gate)

   (Canon for this checklist and the clarification bar is `orchestrator/routing.yaml >
   autonomy` — if this list and routing.yaml ever differ, routing.yaml wins.)
5. **The project's own test/build/lint gate.** Run whatever the repo actually uses (from your
   repo map). Never call the task done on a red build, whether or not anyone is watching.

## What you drop

- **Multi-persona role-play.** Don't write "as the architect... as the developer... as the
  reviewer..." in sequence. It's the same model, same context, same memory of what it just did,
  wearing different labels — it adds token cost and false confidence, not independence.
- **War-room message ceremony.** No `PROPOSE`/`CHALLENGE`/`REVIEW`/`HANDOFF` transcript between
  personas that don't actually exist as separate contexts. Just build the thing and keep the
  spec + diff.
- **Protocol message types in general.** They model real inter-agent communication; there's no
  second agent here to communicate with.
- **An in-context "verifier."** Grading your own stop condition in the same context you built in
  is exactly the failure mode EAOS's verifier exists to prevent. Don't simulate it — replace it
  (next section).

## The one portable isolation trick: a second fresh session

This is the part of EAOS that's worth preserving in any tool, because it doesn't depend on
subagents at all — it depends on you, the human, opening a second window:

1. Finish the implementation and run your local test/build/lint gate until green.
2. Open a **second, brand-new chat/session** in the same tool (or any tool) — one that has
   **no history** of how you built this. Do not summarize your reasoning into it.
3. Paste exactly three things into that fresh session:
   - the task spec (goal + acceptance criteria + scope)
   - the final diff (or a link/path to it)
   - the exact commands to run the project's checks
4. Ask it to grade each acceptance criterion **pass/fail with evidence** (file:line, or actual
   test output it re-runs itself), and to give an overall **APPROVE / REJECT**. Tell it
   explicitly: "you were not involved in building this; grade only from what's in front of you."
5. If it rejects any criterion, fix in your original session and repeat from step 1. Don't
   argue the second session out of a REJECT from inside the first session — that reintroduces
   the same-context problem you just fixed.

This single move — a genuinely fresh context with no authoring memory — is what maker≠checker
actually requires. It costs one extra conversation, not a fleet of simulated personas, and it
works in every chat tool that exists.

## The eaos CLI works here too

Solo users can (and should) use `eaos verify` and `eaos report` for the DoD table from step 5
above — it's plain stdlib python (`scripts/eaos` in an eng-agent-os checkout, or
`~/.claude/eaos/bin/eaos` once installed), so it works in any tool, subagents or not. Record
each acceptance criterion with `eaos verify <id> --criterion "AC-1" --verdict pass|fail
--evidence "..."`, then run `eaos verify <id> --require` before calling the task done. `eaos
report <id>` refuses to assemble the final report if that fails — the same protection against
an unevidenced "pass" that the fresh-session trick gives you against an uncheckable one.
