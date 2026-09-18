# Engineering Agentic OS (EAOS)

EAOS v4 is a small layer you bolt onto a coding agent. The model leads. EAOS supplies the
three things a model cannot give itself and enforces them at boundaries:

1. **Working state that outlives a context** — a typed, revisioned board on disk with
   budgeted views, so a fresh context or a parallel worker sees what its siblings found.
2. **A check made without the maker's reasoning** — a clean-context checker that grades
   criteria and risks with executed evidence.
3. **Evidence and verdicts that cannot be talked into existence** — a runtime whose exit
   codes are binding: check evidence bound to a code snapshot, canonical verdicts, risks
   that must be answered, one writer per workspace, an audit.

It constrains actions and evidence, not the model's reasoning. There is no persona roster
and no phase pipeline. Role knowledge lives in short checklists loaded on demand.

Status: v4 is implemented and under evaluation. The design is
`docs/specs/2026-09-17-eaos-v4-architecture.md` (DRAFT until experiments E0/E1 report);
v3 is preserved at tag `e0-baseline`. Evidence so far is in `evals/`; read
`docs/EVAL-PROTOCOL.md` before believing any claim here, including this one.

## Quickstart (Claude Code)

```bash
git clone https://github.com/AmbitiousSam/eng-agent-os.git && cd eng-agent-os
./setup.sh                       # installs the front door, 3 boundary agents, checklists, runtime
./scripts/install-eaos-hooks.sh  # optional: spawn budget, audit and context size without model cooperation
./scripts/eaos-doctor.sh         # verify
```

`setup.sh` also removes what earlier EAOS versions installed (personas, the agency-agents
library, skills, playbooks). Restart Claude Code, then from inside any project:

```
/agentic-os Add per-API-key rate limiting to our public REST API
```

Follow-ups are plain messages. On a fresh context for an existing task, run
`~/.claude/eaos/bin/eaos status --packet` first.

## What is in the repo

| Path | What |
|---|---|
| `commands/agentic-os.md` | the front door, about 80 lines, loaded once |
| `agents/eaos-{builder,reader,checker}.md` | the three boundaries, tool-scoped, no personas |
| `checklists/` | intake, build, research, review, security, test-adequacy, verdict, deploy-rehearsal, operability, incident, reporting |
| `scripts/eaos` | the runtime: task, unit, board, check, snapshot, writer, verify, report, audit, episode, session, ctx |
| `scripts/eaos-hook.sh` | Claude Code hooks: spawn budget, session binding, audit, context measurement |
| `orchestrator/routing.yaml` | stakes dial, budgets, adapter capability levels |
| `docs/specs/` | v4 draft, v3 (frozen, superseded on freeze only) |
| `evals/` | protocol, pre-registrations, measured results |

## Trust model

Exit codes are rules; prompt text is a wish. A criterion that did not execute is never
`verified`. A high risk without a verdict blocks completion. Evidence is void the moment the
code changes. What a hook cannot enforce is labelled advisory in `routing.yaml > adapters`.
