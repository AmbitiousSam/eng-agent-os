---
name: goal
description: Load when the ask is bigger than one chat (a product, a feature set, a backlog, an investigation that will spawn work); covers the intent contract, work items, one item per chat, and acceptance of the whole.
sources: [lab/specs/2026-09-17-eaos-v4-architecture.md, lab/evals/results/2026-09-18-v4-first-runs.md (T-017 invented its own backlog; T-029 forced a goal into one chat)]
---

# Goal checklist

A goal is a task of kind `goal`. It owns the intent; ordinary tasks do the work. Nothing is carried
between chats except `.eaos/`.

## 1. Compile the intent, then lock it with the human
- `$E task new "<goal>" --kind goal --stakes internal|production` gives the goal id.
- Write the contract from `templates/intent.md`: requirements `R-1..n`, constraints, non-goals,
  acceptance `A-1..n`. One checkable statement per line, the id first on the line. Acceptance lines
  are end-to-end and observable ("an 8-day-old link does not redirect"), not "tests pass".
- Default to assumptions and record them. At most three blocking questions, in one round.
- `$E goal intent <goal> --file <path>`, **show the contract to the human and wait for a yes**, then
  `$E goal lock <goal>`. A wrong contract executed faithfully is the worst outcome here.
- After the lock the contract changes only through `$E goal amend --file ... --reason "<who asked, why>"`.
  Never reinterpret a requirement quietly; never edit `.eaos/<goal>/intent.md` by hand (the runtime
  detects it and refuses).

## 2. Decompose into items
- `$E goal item <goal> --title "..." --kind investigate|build|fix|ship --serves R-1,R-2 [--after T-nnn]`.
  Each item is its own task and prints its task id. Size an item to fit one chat comfortably.
- An `investigate` item may serve nothing; its deliverable is knowledge plus new or changed items.
- `$E goal check <goal>` must pass: every requirement is served, no item serves nothing, no cycle.

## 3. One item per chat
- `$E goal next <goal>` names the next ready item. Run it **as its own task** under the normal
  front door (criteria, units, checker at its stakes, `$E finish <item>`). Carry the requirement
  ids it serves into its acceptance criteria.
- When the item is finished, stop and tell the human to start a fresh chat with
  `/agentic-os next`. Do not start a second item in the same context.
- An item that closes without a pass blocks the goal. Fix it with a new item; do not reopen verdicts.

## 4. Status and acceptance
- `$E goal status <goal>` prints requirement -> items -> verdicts, and the acceptance lines.
- When `goal next` says all items are closed: acceptance is graded **by the checker in a clean
  context**, given only the intent contract, `goal status` and the repository, by executing each
  `A-n`: `$E verify <goal> --criterion A-1 --verdict ... --evidence "<what ran, what happened>"`.
  This is where drift shows: every item verified and an acceptance line still failing.
- `$E finish <goal>` refuses while any item is open or failed, any requirement lacks an item, the
  contract changed after the lock, or any acceptance line is ungraded.
