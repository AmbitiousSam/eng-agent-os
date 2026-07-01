# Engineering Agentic OS (EAOS)

A portable "operating system" that runs software engineering work as a **collaborating team
of AI agents** — architect, developer, QA, security, devops, platform, SRE, reviewer, writer —
coordinated by an orchestrator that runs a real engineering loop (understand → plan → build →
review → test → ship → stabilize) and pulls in only the agents a task actually needs.

It runs on **stock Claude Code subagents** (no experimental features required — the
orchestrator owns coordination itself). EAOS works **standalone**; if
[`agency-agents`](https://github.com/msitarzewski/agency-agents) is present, EAOS can delegate
specialized subtasks to those personas. The layer EAOS adds over a plain persona library:
**real agent-to-agent collaboration** — routing, a shared war room, review loops, memory, and
human gates.

> Full design rationale lives in [`AGENT_OS.md`](./AGENT_OS.md). Read that first.

## EAOS vs. plain Claude Code subagents

| Plain subagents | EAOS |
|---|---|
| Isolated experts you invoke one at a time | A **routed team** the orchestrator assembles per task |
| No shared state; context lost between them | A **war room** + artifacts + project **memory** (auditable, resumable) |
| You decide who runs and when | **routing.yaml** activates the fewest agents the task needs |
| No convergence when they disagree | **One exchange → phase owner decides**; security can veto |
| Edits can be unscoped / hallucinated | **GROUND** maps the repo + an impact map before editing |
| Free-for-all on actions | **Human gates**: no deploy/push/migrate/spend without confirmation |

## Quickstart (new machine)

```bash
git clone <your-fork>/eng-agent-os && cd eng-agent-os
./setup.sh                  # installs command, personas, skills, config into ~/.claude
./scripts/eaos-doctor.sh    # verify install + that this project is ready  (or: make doctor)
```

Then **restart Claude Code** (slash commands load at startup), and from inside any project:

```
/agentic-os Add per-API-key rate limiting to our public REST API
```

> The command is also installed as `/agent-os` (alias). If `/agentic-os` doesn't autocomplete,
> run `./scripts/eaos-doctor.sh` — it tells you exactly what's missing.

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
| `setup.sh` | Bootstrap: install command, personas, skills, config (+ optional agency-agents) |
| `scripts/` | `validate-eaos.py`, `eaos-doctor.sh`, `push-to-github.sh` |
| `Makefile` | `make install / doctor / validate / test` |
| `orchestrator/` | The **kernel**: orchestrator role + routing + protocol + the loop *runner* |
| `playbooks/` | **Processes** (feature-delivery, bug-fix, …) that ride on the kernel |
| `agents/` | The 11 engineering personas incl. `codebase-analyst` (+ relation to agency-agents) |
| `skills/` | Reusable procedures (intake, test-plan, deploy guide, codebase-map, bug-triage) |
| `templates/` | Output templates (spec, design, ADR, review, test plan, impact/codebase map) |
| `memory/` | Durable project knowledge (decisions / patterns / lessons / codebase map) |
| `CUSTOMIZE.md` · `RUN.md` · `docs/IDE-SETUP.md` | Customization, Claude Code run guide, Cursor/Windsurf adapters |
| `examples/` · `ROADMAP.md` | Worked walkthrough · phased build plan + business pack |

## Kernel + playbooks (v2)

EAOS separates a constant **kernel** from pluggable **playbooks**:

- **Kernel** (`orchestrator/`) — orchestrator, protocol, war room, memory, human gates, and the
  pre-push gate. Never changes per process.
- **Playbooks** (`playbooks/`) — a process = phases + roster + gates + exit condition. The loop
  runner selects one by task `kind`/command and runs it under the kernel. `feature-delivery` is
  the default; `bug-fix` for `kind: bug`. Adding a process (incident-response, rfc, release…) is
  *one file* + a line in `routing.yaml > playbooks` — the engine is untouched.

This is what lets EAOS grow toward a full engineering-org lifecycle without rewrites: every new
way of working is a playbook on the same kernel.

## Modes — it knows when *not* to activate itself

EAOS scales effort to the task (set by complexity at intake). It won't run a 10-agent loop for a
typo.

| Mode | Triggers | Who runs |
|---|---|---|
| **trivial** | typo, one-line config, copy fix, dep bump | developer only (quick localize + self-review) |
| **small** | tiny feature/fix | requirements + developer + code-reviewer |
| **standard** | normal feature/bug | + GROUND (codebase map/impact), architect, QA, review/test loops |
| **complex** | new service, cross-cutting, perf/security-critical | + security, devops, platform, SRE, tech-writer |

The 4-agent **MVP loop** (requirements → architect+developer plan → developer implements →
reviewer reviews) is the recommended starting point; the full specialist set is opt-in for
standard/complex tasks. See `AGENT_OS.md` §13.

## Safety model

One of the reasons to trust it on a real repo: it cannot take irreversible actions on its own.

- **No destructive/costly action without your confirmation** — it will *propose* a deploy,
  `git push`, migration, or anything that spends money, but never execute it autonomously.
- **Least privilege** — each persona's tools are scoped in frontmatter (e.g. the reviewer is
  read-only; the writer can't run shell).
- **Security can hard-veto** — a high-severity finding blocks delivery until mitigated.
- **Full audit trail** — every decision/question/handoff is in `.eaos/<id>/warroom.md`.
- **Bounded autonomy** — it stops at defined human gates (`routing.yaml > autonomy`) and
  otherwise proceeds without pestering you. Set `mode: supervised` to confirm every phase.

## Develop / validate

```bash
make doctor      # install + project readiness
make validate    # mechanical repo consistency (routing ↔ personas ↔ templates)
make test        # shell syntax checks + validator (CI entrypoint)
```

`scripts/validate-eaos.py` parses `routing.yaml`, every persona's frontmatter, and cross-checks
that routing names, agents, and template references all line up — so the OS contract is
*enforced*, not just documented.

## MVP first

Start with 4 agents and one linear loop (requirements → architect+developer → developer →
reviewer). See `AGENT_OS.md` §13. Everything else is additive.

## License / attribution

Builds on and installs [`agency-agents`](https://github.com/msitarzewski/agency-agents) (MIT).
EAOS is the coordination layer; agency-agents supplies extra specialist personas.
