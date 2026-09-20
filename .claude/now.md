# Now — EAOS

_Last updated: 2026-09-20_

## State
- **v4.5.8 released**, installed on this machine, doctor Healthy, `main` clean and pushed. Gate: `bash tests/run.sh`.
- 17 real runs reviewed, all in `lab/evals/results/2026-09-18-v4-first-runs.md`. Everything has had a real run
  EXCEPT Cursor and the controlled comparison.

## NEXT SESSION: brainstorm "the next step for EAOS", at the core-foundations level
Siva opened `/superpowers:brainstorming` for this and chose to restart with a fresh mind. Start there. Known so far:
- It is a **personal tool**. Distribution and adoption are explicitly LAST. Not a commercial conversation.
- He is thinking about **core foundations**, not a feature or a pain point. He declined to pick a "biggest pain".
  Do not steer him into the run/fix loop or into synergina backlog.
- Follow the brainstorming skill: one question at a time, 2-3 approaches, design, approval before any code.

### Evidence to bring to that conversation (from the runs, not opinion)
1. The checker is the part that works: failed a criterion against the lead's own spec (run 15); goal-level acceptance
   caught two integration bugs every item checker passed (run 17). Item-level checks were weaker: graded by reading
   diffs (run 14), approved metric gaming via a `loose()` helper (run 16).
2. Every UI run closed conditional for one reason: nothing can look at a screen (runs 14, 15, 17).
3. The model sizes work better than the reviewer did, four runs in a row (toy / internal / not-a-goal). The goal
   level only fired when the prompt said "treat this as a goal"; it then worked.
4. Host baseline is 73-85k tokens before EAOS does anything; front door is ~2k of it. Goal run: 13 subagents, lead 76k -> 161k.
5. One runtime fix stalled a live goal three times; a stopped chat needs the human. Now gated by a test.
6. Runtime is ~3.9k lines; v3 verbs (phase, append, gate, loopback) remain because 63 tests use them as setup.
7. Unproven: EAOS vs the same model with no EAOS (E0 pre-registered, grader built at `~/.eaos-holdouts/E0/`, never
   paste it); anything in Cursor; Codex loading `~/.claude/agents/`.

## Open items (small)
- Cursor test is prepared, not run: restart Cursor, in synergina
  `/agentic-os Fix the 4 react-hooks/exhaustive-deps warnings in platform/src/app/(dashboard)/user/network/network-hub-client.tsx. Internal stakes.`
  Watch for an `eaos-checker` subagent starting (not readable from disk; no hooks in Cursor so spawn count reads 0).
- Siva's, in synergina: commit `feat/follow-through` (74 files, conditional: two browser checks on a throwaway local
  Mongo, never the shared Atlas DB); commit `chore/t17-25-lint-zero`; decide on the `loose()` helper; rotate
  `CHAT_ENCRYPTION_KEY` (`training-ai-service/.env.example:86`).
- Do not update EAOS while a goal is open in a project.
