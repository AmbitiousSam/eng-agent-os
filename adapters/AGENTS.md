# EAOS in this repository (Cursor, Codex, any agent that reads AGENTS.md)

Copy this file to the root of a project as `AGENTS.md`. It is a pointer, not a second copy of the
rules: the rules live in one place, `~/.claude/commands/agentic-os.md`, installed by EAOS `setup.sh`.

## When a task is more than a one-line answer

1. Read `~/.claude/commands/agentic-os.md` once and follow it. Where it says `$ARGUMENTS`, that is the
   task you were just given.
2. The runtime script is `~/.claude/eaos/bin/eaos`. You run it in the terminal; the human never does.
   Its exit codes are binding: 0 ok, 1 refused, 2 usage, 3 conditional, 4 lock busy (retry).
3. Checklists are in `~/.claude/eaos/checklists/`. Load one when its trigger applies, never all.

## Host deltas: read before the front door

- **Claude Code:** use `/agentic-os <task>` instead of this file. Boundary agents and hooks exist there.
- **Cursor, Codex, anything without isolated subagents:** where the front door says to spawn
  `eaos-builder` or `eaos-reader`, do that work yourself inside the unit. Where it says to spawn
  `eaos-checker`, **stop and ask the human to open a new chat** with the checker packet below. A check
  made in the context that built the code is not a check. Procedure: `~/.claude/eaos/adapters/solo-mode.md`.
- Spawn counting and session binding are hook features of Claude Code. Elsewhere they are absent; the
  board, snapshot-bound evidence, scenarios, verdict rules and refusals work the same, because they
  live in the script.

## The checker packet (paste into the new chat)

```
You are the independent checker for EAOS task <T-nnn> in this repository. You have not seen how it was
built. Read ~/.claude/agents/eaos-checker.md and ~/.claude/eaos/checklists/verdict.md, then run:
  ~/.claude/eaos/bin/eaos status --packet <T-nnn>
  ~/.claude/eaos/bin/eaos board view <T-nnn> --for checker
  ~/.claude/eaos/bin/eaos scenario list <T-nnn> --for checker
Grade every criterion and scenario by executing something, record each with `eaos verify` /
`eaos scenario grade`, and finish with APPROVE, CONDITIONAL or REJECT.
```

## Always

Human gate before: push or merge to a shared branch, deploy, migration, spend, data deletion, history
rewrite on a branch this task did not create. Prepare it, show the exact command, stop.
