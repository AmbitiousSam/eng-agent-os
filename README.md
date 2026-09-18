# Engineering Agentic OS (EAOS)

EAOS v4 is a small layer you bolt onto a coding agent. The model leads. EAOS supplies the
three things a model cannot give itself and enforces them at boundaries:

1. **Working state that outlives a context** — a typed, revisioned board on disk with
   budgeted views, so a fresh context or a parallel worker sees what its siblings found.
2. **A check made without the maker's reasoning** — a clean-context checker that grades
   criteria, risks and **scenarios** (end-to-end expectations written at intake and held
   outside the workspace, which builders never see) with executed evidence.
3. **Evidence and verdicts that cannot be talked into existence** — a runtime whose exit
   codes are binding: check evidence bound to a code snapshot, canonical verdicts, risks
   that must be answered, one writer per workspace, an audit.

It constrains actions and evidence, not the model's reasoning. There is no persona roster
and no phase pipeline. Role knowledge lives in short checklists loaded on demand.

Status: v4.2.0. Hardened by twelve reviewed real runs (`lab/evals/results/2026-09-18-v4-first-runs.md`);
no controlled comparison against v3 or a plain agent has been run yet (experiment E0 is
pre-registered and its grader is built). v3 lives on the `v3` branch (release v3.0.0). Read
`lab/EVAL-PROTOCOL.md` before believing any claim here, including this one.

## Quickstart (Claude Code)

```bash
git clone https://github.com/AmbitiousSam/eng-agent-os.git && cd eng-agent-os
./setup.sh                       # installs the front door, 3 boundary agents, checklists, runtime
./runtime/install-eaos-hooks.sh  # optional: spawn budget, audit and context size without model cooperation
./runtime/eaos-doctor.sh         # verify
```

`setup.sh` also cleans up what earlier EAOS versions installed (personas, the agency-agents
library, skills, playbooks): a file is removed only if its content matches the manifest of
what EAOS shipped (`runtime/legacy-manifest.sha256`); anything customised or unknown is
quarantined under `~/.claude/eaos/quarantine/` with a manifest. `./setup.sh --dry-run`
prints the plan first. Restart Claude Code, then from inside any project:

```
/agentic-os Add per-API-key rate limiting to our public REST API
```

Follow-ups are plain messages. On a fresh context for an existing task, run
`~/.claude/eaos/bin/eaos status --packet <task>` first.

## Cursor, Codex, other hosts

Run `./setup.sh` once (it installs under `~/.claude/` whether or not Claude Code is present), then
copy `adapters/AGENTS.md` into your project root. It points the agent at the same front door and the
same runtime script. What differs is stated there: no isolated subagents, so the independent check is
a new chat the human opens with a ready-made packet. `adapters/README.md` lists what is enforced,
measured or advisory per host.

## What is in the repo

The product is the first five rows, about twenty files. You never run the runtime script yourself;
the agent does, the way it runs `git`.

| Path | What |
|---|---|
| `commands/agentic-os.md` | the front door, about 100 lines, loaded once per context |
| `agents/` | three boundaries: builder, reader, checker. Tool-scoped, no personas |
| `checklists/` | eleven, loaded on demand: intake, build, research, review, security, test-adequacy, verdict, deploy-rehearsal, operability, incident, reporting |
| `runtime/` | `eaos` (board, units, snapshot-bound checks, scenarios, verdicts, audit), the Claude Code hook, the hook installer, doctor, `routing.yaml` |
| `adapters/` | `AGENTS.md` entry for Cursor and Codex, the solo-mode procedure, the capability table |
| `templates/` | report, ADR, task spec, test plan and the other documents the checklists name |
| `tests/` | 169 runtime tests, 86 hook assertions, installer tests, the repo validator |
| `lab/` | not product: specs, research, review records, experiment protocol, measured results |

## Trust model

Exit codes are rules; prompt text is a wish. A criterion that did not execute is never
`verified`. A high risk without a verdict blocks completion. Evidence is void the moment the
code changes. What a hook cannot enforce is labelled advisory in `routing.yaml > adapters`.
