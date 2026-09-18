# Solo mode — EAOS on a host with no subagents

Use this on a host that cannot spawn an isolated context (or when you choose not to). The
boundaries are the mechanism; a role-play of "builder, then checker" inside one context
keeps the names and loses the mechanism. Every step below uses the same runtime CLI, so
the evidence and verdicts are identical to the Claude Code path; only the way a fresh
context is obtained differs (a new chat instead of a subagent).

## The procedure

1. **Start.** `eaos init && eaos task new "<title>" --kind ... --stakes ...`. Read
   `checklists/intake.md` for anything beyond a trivial change. Record criteria with
   `eaos verify` as you go. Two things are never assumed: a deliverable-class word in the
   ask (workflow, pipeline, deploy, release, migration, rollout) is a question; an
   identity or attribution constraint becomes a criterion.
2. **Work in units.** `eaos unit start --title --kind build --scope`, then
   `eaos writer claim`. One writer per workspace; you are it. Post findings, decisions and
   risks to the board with `eaos board post` (≤400 chars, detail in a `--ref` file).
3. **Evidence, not claims.** Run the project's checks through the runtime:
   `eaos check <task> --category test --cmd "<command>"`. Then
   `eaos unit handoff <task> <unit> --ready` (or `--blocked --reason`). The runtime
   refuses a READY handoff without passing evidence bound to the current code.
4. **The checker is a new chat.** Open a genuinely new session. Give it only:
   `agents/eaos-checker.md`, the task spec, `eaos board view <task> --for checker`, the
   snapshot id from `eaos snapshot`, the check commands, and `checklists/verdict.md`.
   Not your transcript, not your notes, not your self-review. It records verdicts with
   `eaos verify` and returns APPROVE / CONDITIONAL / REJECT.
5. **Fresh context on resume.** When your session is long or `eaos status --packet` says
   OVER CEILING, finish the unit, hand off, and start a new chat that begins with the
   packet. State lives in `.eaos/`, not in the transcript.
6. **Finish.** `eaos verify --require` (0 or 3), `eaos report`, `eaos episode close`, then
   the final report from `templates/final-report.md`.

## What this does not give you

Read-only enforcement for the checker, hidden evaluator scenarios, or a writer lease the
host actually gates. Those are advisory here (`runtime/routing.yaml > adapters`).
What it does give you is the part the evidence says matters most: a clean context for the
check, and evidence the runtime will not accept from the wrong snapshot.
