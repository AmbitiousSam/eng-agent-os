# Engineering Agentic OS (EAOS)

A portable "operating system" that runs software engineering work as a **collaborating team
of AI agents** — architect, developer, QA, security, devops, platform, SRE, reviewer, writer —
coordinated by an orchestrator that runs a real engineering loop (understand → plan → build →
review → test → ship → stabilize) and pulls in only the agents a task actually needs.

It runs on **stock Claude Code subagents** (no experimental features required — the
orchestrator owns coordination itself) and is built to sit **on top of**
[`agency-agents`](https://github.com/msitarzewski/agency-agents), adding the layer that plain
persona libraries lack: **real agent-to-agent collaboration**.

> Full design rationale lives in [`AGENT_OS.md`](./AGENT_OS.md). Read that first.

## Quickstart (new machine)

```bash
git clone <your-fork>/eng-agent-os && cd eng-agent-os
./setup.sh     # clones agency-agents + installs personas, skills, the /agentic-os command,
               # and OS config into ~/.claude
```

Then, **from inside any project**, in Claude Code:

```
/agentic-os Add per-API-key rate limiting to our public REST API
```

That's the whole interface. The command turns the main session into the **orchestrator**: it
creates a war room, runs the full loop (requirements → clarify → plan → implement → review →
test → ops → docs → stabilize), spawns only the specialists the task needs, and hands you a
complete package. It runs **autonomously**, stopping only at defined human gates (blocking
product decisions, deadlocks, and destructive/costly actions like an actual deploy).

### How it coordinates (no special harness features required)

Communication is baked into the OS, not borrowed from any experimental feature. The
orchestrator is the **sole writer of the war room**; each specialist subagent does its work,
writes its own artifacts, and returns protocol messages; the orchestrator appends them and
**relays** between agents. Peer messaging = orchestrator relay through files. State lives in
`./.eaos/<task-id>/`, so a run is fully resumable.

### Runtime layout (project-local, created on first run)

```
./.eaos/
├── T-001/
│   ├── warroom.md          # the team conversation (orchestrator-owned)
│   └── artifacts/          # spec, impact-map, design, ADRs, tests, deploy guide, docs
└── memory/
    ├── decisions/ patterns/ lessons/   # this codebase's accumulated knowledge
    └── codebase/map.md                 # cached repo map (built once, refreshed on git change)
```

> **First run on a repo** spends a little extra time building the repo map (structure, run/test
> commands, conventions, danger zones). After that it's cached and only refreshed when the code
> changes, so later tasks start fast. Every task also gets an **impact map** — exactly which
> files/symbols/tests it touches — so the team edits the right places and stays in scope.

## What's in here

| Path | Purpose |
|---|---|
| `AGENT_OS.md` | The complete design document (architecture, flows, routing, roadmap) |
| `commands/agentic-os.md` | The `/agentic-os` slash command — the autonomous orchestrator driver |
| `setup.sh` | Bootstrap: clone agency-agents + install command, personas, skills, config |
| `orchestrator/` | Orchestrator role spec + routing rules + message protocol + loop state machine |
| `agents/` | The 10 engineering personas (+ how they relate to agency-agents) |
| `skills/` | Reusable procedures (intake, test-plan, deploy guide) |
| `templates/` | Output templates (spec, design, ADR, review, test plan) |
| `memory/` | Durable project knowledge (decisions / patterns / lessons) |
| `examples/` | A full worked walkthrough |
| `ROADMAP.md` | Phased build plan + the future business pack |

## MVP first

Start with 4 agents and one linear loop (requirements → architect+developer → developer →
reviewer). See `AGENT_OS.md` §13. Everything else is additive.

## License / attribution

Builds on and installs [`agency-agents`](https://github.com/msitarzewski/agency-agents) (MIT).
EAOS is the coordination layer; agency-agents supplies extra specialist personas.
