# Engineering Agentic OS (EAOS)

A small layer for coding agents. The model leads. EAOS supplies the three things a model cannot
give itself, and enforces them with a script whose exit codes the agent cannot argue with:

1. **Working state that outlives a context.** A typed board on disk, so a fresh chat or a parallel
   worker sees what its siblings found.
2. **A check made without the maker's reasoning.** A clean-context checker grades the acceptance
   criteria, the open risks and **scenarios** written before any code and hidden from the builder.
3. **Evidence that cannot be talked into existence.** Check results are bound to a code snapshot and
   void when the code changes. Nothing that did not execute is `verified`. A task nobody judged
   cannot close.

Works in **Claude Code, Cursor and Codex**. No personas, no phase pipeline.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/AmbitiousSam/eng-agent-os/main/install.sh | bash
```

That is the whole install. It needs `git` and `python3`, takes a few seconds, and is safe to re-run
(re-running is also how you update). It works globally: nothing is copied into your projects.

Then open any repository and type:

| Host | Type this |
|---|---|
| Claude Code | `/agentic-os <your task>` (restart Claude Code once after the first install) |
| Cursor | `/agentic-os <your task>` |
| Codex | `$agentic-os <your task>` |

Follow-up messages are plain conversation. Do not re-type the command in the same chat.

### If you are an AI agent asked to install EAOS

Run exactly the one command above in a terminal. Success is the line `Healthy.` near the end of its
output. Do not clone manually, edit settings files or copy anything into the user's project. If the
command fails, show the user its last ten lines and stop. To verify later:
`bash ~/.eaos-src/eaos/runtime/eaos-doctor.sh`.

### What the installer puts where

| Path | What | Used by |
|---|---|---|
| `~/.eaos-src/` | this repository (the installer updates it with `git pull`) | installer |
| `~/.claude/commands/agentic-os.md` | the front door | Claude Code |
| `~/.claude/agents/eaos-{builder,reader,checker}.md` | three tool-scoped boundaries | Claude Code |
| `~/.agents/skills/agentic-os/SKILL.md` | the same front door as a global skill, generated at install | Cursor, Codex |
| `~/.claude/eaos/` | the runtime script, checklists, templates, config | every host |
| `~/.claude/settings.json` | three hook entries, only if Claude Code is installed; the file is backed up first | Claude Code |

In your projects EAOS writes one folder, `.eaos/`, holding task state. Add it to `.gitignore` or
commit it, your choice. Earlier EAOS versions are cleaned up automatically: a file is deleted only if
it is byte-identical to what EAOS shipped; anything you customised is moved to
`~/.claude/eaos/quarantine/`.

Options: `EAOS_NO_HOOKS=1` skips the hooks, `EAOS_REF=v4.2.0` pins a release, `EAOS_SRC=<dir>` moves
the checkout. **Uninstall:** `bash ~/.eaos-src/setup.sh --uninstall`. Working from a clone instead:
`./setup.sh`, then optionally `./eaos/runtime/install-eaos-hooks.sh`.

## What a task looks like

You type the task. The agent then, on its own:

1. Opens a task with a stakes level: `toy`, `internal` or `production`. Stakes decide how much
   process sits between start and finish, nothing else.
2. Records acceptance criteria. At internal stakes and above it also writes scenarios, stored outside
   the workspace where the builder will not look.
3. Works in units. Findings, decisions and risks go on the board, not into its own narration.
4. Runs the project's real test, lint, type and build commands through the runtime, which binds each
   result to the current code snapshot.
5. Hands the result to an independent checker that never sees how it was built. In Claude Code that
   is a subagent. In Cursor and Codex the agent stops and gives you a ready packet to paste into a
   new chat.
6. Closes with a verdict the runtime computes (`verified`, `conditional-manual`, `partial`,
   `unverified`) and a final report: asked, built, checked with proof, decided, not done, needs you.

It always stops for you before: push or merge to a shared branch, deploy, migration, spending money,
deleting data, rewriting history on a branch the task did not create.

You never run the runtime script. The agent does, the way it runs `git`.

## What differs per host

| Capability | Claude Code | Cursor, Codex |
|---|---|---|
| Board, snapshot-bound evidence, scenarios, verdict rules, refusals | enforced | enforced (same script) |
| Independent checker | isolated subagent | a new chat you open with the supplied packet |
| Parallel read-only researchers | subagents | not available |
| Spawn budget, session binding, stop-time audit, context size | hooks | not available |

`eaos/adapters/README.md` has the full table. `eaos/adapters/AGENTS.md` is a drop-in for hosts that read
`AGENTS.md` but do not load skills.

## Status, honestly

v4.2.0. Twelve real runs on a private production codebase were reviewed and every defect they
exposed was fixed (`lab/evals/results/2026-09-18-v4-first-runs.md`). In those runs the checker caught
real bugs three times, no session compacted, and tasks used 1 to 4 subagents.

Not yet shown: that EAOS beats the same model with no EAOS. The controlled experiment is
pre-registered and its grader is built, but it has not been run. The Cursor and Codex path is built
from their documented skill loading and has not been exercised on a real task. Developed and tested
on macOS. Read `lab/EVAL-PROTOCOL.md` before believing any claim here, including this one.

## Repository map

Three folders. The product is `eaos/`, about thirty files, and it is all the installer copies.

| Path | What |
|---|---|
| `install.sh`, `setup.sh` | one-step installer; the installer proper (`--dry-run`, `--uninstall`) |
| `eaos/agentic-os.md` | the front door, about 100 lines, loaded once per context |
| `eaos/agents/` | builder, reader, checker: tool-scoped boundaries, no personas |
| `eaos/checklists/` | eleven, loaded on demand: intake, build, research, review, security, test-adequacy, verdict, deploy-rehearsal, operability, incident, reporting |
| `eaos/runtime/` | `eaos` (the script the agent runs), the Claude Code hook and its installer, doctor, `routing.yaml` |
| `eaos/adapters/` | skill header for Cursor and Codex, `AGENTS.md` fallback, solo-mode procedure, capability table |
| `eaos/templates/` | final report, ADR, task spec, test plan and the other documents the checklists name |
| `tests/` | `run.sh` runs everything: runtime tests, hook tests, installer tests, repo validator |
| `lab/` | not product: specs, research, review records, experiment protocol, measured results |

v3 (personas and playbooks) is preserved on branch `v3`, release v3.0.0.
