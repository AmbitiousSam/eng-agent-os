# Engineering Agentic OS (EAOS)

> A portable "operating system" for running software engineering work as a collaborating
> team of AI agents — not a pile of isolated prompts. Runs natively on Claude Code
> subagents today (no experimental features needed), and is structured to port to other harnesses later.
> Built to sit **on top of** [`agency-agents`](https://github.com/msitarzewski/agency-agents),
> reusing its personas where useful and adding the missing layer: **collaboration**.

---

## 0. The one-paragraph version

EAOS is a thin, version-controlled layer made of three things: **(1) agent personas**
(markdown role definitions), **(2) a communication protocol** (a strict message schema +
a shared "war room" file so agents can ask each other questions, challenge assumptions,
and review work), and **(3) an orchestrator** (a lead agent that runs a loop: understand →
plan → build → review → test → ship → stabilize, activating only the agents a given task
actually needs). Because all three are just files, the "OS" is portable: today it runs on
Claude Code's subagents and experimental Agent Teams; tomorrow the same persona/protocol
files convert to Codex, Cursor, or Copilot. Business roles (CEO, CTO, PM, finance…) are a
future *agent pack* that plugs into the same orchestrator and protocol unchanged.

---

## 1. Why this exists (the gap in `agency-agents`)

`agency-agents` gives you 61 strong, personality-driven personas you copy into
`~/.claude/agents/`. They are excellent *individually*. What's missing is everything that
makes a real engineering org work:

| Real team behavior | Plain persona library | EAOS adds |
|---|---|---|
| Architects & devs plan *together* | each runs alone | shared planning round + war-room |
| Devs ask before building | one-shot output | clarification gate (blocking questions) |
| QA reviews *requirements*, not just code | post-hoc | QA joins at intake & design |
| Reviewers challenge assumptions | no channel | structured disagreement protocol |
| Only the right people get pulled in | you pick manually | orchestrator routes dynamically |
| Don't burn budget on everyone | flat | model routing + skip rules |

EAOS does **not** replace `agency-agents` — it **consumes** it. Your bootstrap clones
agency-agents, and EAOS personas either reference those files or override them.

---

## 2. Overall architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         EAOS  (the portable layer)                     │
│                                                                        │
│   ┌────────────┐     reads      ┌──────────────────────────────────┐  │
│   │ ORCHESTRATOR│◀────routing────│ routing.yaml  (who/when/which     │  │
│   │  (lead)     │     rules      │ model + skip rules)               │  │
│   └─────┬───────┘                └──────────────────────────────────┘  │
│         │ spawns / messages                                            │
│         ▼                                                              │
│   ┌─────────────────────────  AGENT POOL  ───────────────────────┐    │
│   │ requirements │ architect │ developer │ reviewer │ qa │ devops │    │
│   │ platform │ security │ sre-observability │ tech-writer         │    │
│   └───────────────────────────────────────────────────────────────┘   │
│         │ all communicate through ▼                                    │
│   ┌──────────────────────────────────────────────────────────────┐    │
│   │  PROTOCOL: message schema + WAR ROOM (warroom.md) + ARTIFACTS  │    │
│   └──────────────────────────────────────────────────────────────┘    │
│         │ persists to ▼                                                │
│   ┌──────────────────────────────────────────────────────────────┐    │
│   │  MEMORY: project memory, decisions (ADRs), patterns, lessons   │    │
│   └──────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
            │ runs on                          │ borrows personas from
            ▼                                  ▼
   Claude Code subagents (Task tool)     agency-agents (cloned)
            │ later ports to
            ▼
   Codex CLI · Cursor · Copilot · LangGraph wrapper
```

Four layers, each independently replaceable:

1. **Substrate** — the harness that actually executes agents (Claude Code now).
2. **Persona layer** — markdown role files (`agents/*.md`), some inheriting agency-agents.
3. **Coordination layer** — orchestrator + routing + protocol + war room.
4. **Memory layer** — durable project knowledge (decisions, patterns, lessons).

The value is that layers 2–4 are *just files in a git repo*, so the whole "OS" moves between
machines and harnesses.

---

## 3. Engineering agents and responsibilities

Eleven core engineering agents. Each persona file declares: role, when it activates, what it
produces, who it talks to, and which model tier it runs on.

| Agent | Mandate | Key outputs | Default model |
|---|---|---|---|
| **Requirements Analyst** | Turn a vague ask into a crisp, testable spec; classify kind; surface unknowns | `task-spec.md`, open-questions list | Reasoning (Opus) |
| **Codebase Analyst** (Navigator) | Map the existing repo; localize the change; reproduce bugs | `codebase/map.md`, `impact-map.md`, repro test | Coding (Sonnet) |
| **Architect** | System design, trade-offs, interfaces, risk register | `design-doc.md`, ADRs, sequence/component sketches | Reasoning (Opus) |
| **Developer** | Implement to spec; ask blocking questions first | code, PR description, self-test notes | Coding (Sonnet) |
| **Code Reviewer** | Correctness, readability, maintainability, diff review | `review-notes.md`, change requests | Coding (Sonnet)/Opus for hard calls |
| **QA Engineer** | Review *requirements* + code; design test cases & edge cases | `test-plan.md`, test code, bug reports | Coding (Sonnet) |
| **Security Reviewer** | Threat model, authn/z, secrets, deps, OWASP | security findings, severity-ranked | Reasoning (Opus) |
| **DevOps Engineer** | CI/CD, build/release, IaC, rollout & rollback | pipeline config, deploy guide | Coding (Sonnet) |
| **Platform Engineer** | Runtime fit: cloud services, cost, scaling, networking | platform plan, capacity notes | Reasoning (Opus)/Sonnet |
| **SRE / Observability** | SLOs, metrics/logs/traces, alerts, reliability | observability plan, runbook | Sonnet |
| **Tech Writer** | README, API docs, changelog, deployment guide, summaries | docs, release notes | Cheap/fast (Haiku) |

Plus the **Orchestrator** (lead) — not a worker; it routes, sequences, runs the loop, and
forces convergence on disagreements. Runs on the Reasoning tier.

> These map cleanly onto agency-agents divisions where they exist; where agency-agents has
> a stronger persona (e.g. its frontend specialist), the EAOS developer agent can *delegate*
> to it rather than duplicate it. See `agents/README.md`.

---

## 4. Agent communication patterns

Three channels, deliberately constrained so coordination stays cheap and auditable.

> **Self-owned, no special harness features.** Communication is baked into the OS — it does
> NOT depend on Claude Code's experimental Agent Teams or any peer-messaging plugin. The
> orchestrator (the `/agentic-os` run on the main session) is the **sole writer of the war
> room**; specialists return messages and the orchestrator relays them. This keeps the system
> portable, autonomous, and resumable. See `orchestrator/protocol.md`.

**(a) The War Room (`.eaos/<task-id>/warroom.md`)** — an append-only file written ONLY by the
orchestrator. It's the team's "Slack channel" and the single source of truth. It survives
context limits because it's on disk, not in any one agent's window.

**(b) Returned messages (orchestrator-relayed)** — a targeted question from one agent to
another ("Developer → Architect: write-through or write-back?") is implemented as: the
developer *returns* a QUESTION → the orchestrator passes it into the architect's prompt → the
architect returns an answer → the orchestrator records both. Peer messaging without peers
talking directly. No race conditions, fully logged.

**(c) Artifacts (`.eaos/<task-id>/artifacts/…`)** — the durable work products (spec, design,
code, tests, review notes), each a distinct file. Agents reference artifacts by path, never
paste large blobs into messages.

Every message uses one **message type** (the protocol):

```
PROPOSE   — "here's my plan/design/implementation"
QUESTION  — blocking clarification, must be answered before requester proceeds
CHALLENGE — "I disagree, and here's why + evidence"
REVIEW    — structured feedback on an artifact (approve / request-changes / block)
RISK      — a flagged risk with severity + mitigation
DECISION  — a resolved choice (becomes an ADR)
HANDOFF   — "my part is done, here's what's ready and what's next"
STATUS    — progress / blocked / done
```

Schema for every entry (see `orchestrator/protocol.md`):

```yaml
- id: msg-014
  from: developer
  to: [architect]          # or "all"
  type: QUESTION
  ref: artifacts/T-101/design-doc.md#caching
  priority: blocking       # blocking | normal | fyi
  body: >
    Spec says "low latency reads" but write volume is high. Write-through
    doubles write cost. Is stale-by-2s acceptable so I can use write-back?
  needs_answer_by: planning-gate
```

This makes disagreement and clarification *first-class*, not buried in prose.

---

## 5. Task orchestration logic — the engineering loop

The orchestrator runs a state machine. Each phase has an **entry gate** (conditions to enter),
**participants** (chosen by routing), and an **exit gate** (what must be true to advance).
Loops are explicit: any phase can send work *back*.

```
        ┌──────────────┐
        │  INTAKE       │  Requirements Analyst (+QA reads along)
        │  classify     │  → task-spec.md, complexity, KIND, signals
        └──────┬───────┘
               ▼
        ┌──────────────┐   Codebase Analyst (skip if greenfield)
        │  GROUND       │   → repo map (cached) + impact-map.md;
        │  map+localize │     for bugs: reproduce + root-cause. May re-route.
        └──────┬───────┘
               ▼
        ┌──────────────┐   QUESTION loop: analyst/dev/architect raise blocking Qs
        │  CLARIFY      │   (incl. ambiguities GROUND found) answered before exit
        └──────┬───────┘
               ▼
        ┌──────────────┐   Architect + Developer PLAN TOGETHER (+platform/security if flagged)
        │  PLAN/DESIGN  │   CHALLENGE allowed; ends in DECISION (ADRs)
        └──────┬───────┘
               ▼
        ┌──────────────┐   Developer implements; QA writes tests in parallel
        │  IMPLEMENT    │   blocking QUESTIONs pause only the asker
        └──────┬───────┘
               ▼
        ┌──────────────┐   Code Reviewer + (Security/QA as routed)
        │  REVIEW       │   REVIEW=request-changes → back to IMPLEMENT
        └──────┬───────┘
               ▼
        ┌──────────────┐   QA runs/expands tests; bugs → back to IMPLEMENT
        │  TEST/QA      │
        └──────┬───────┘
               ▼
        ┌──────────────┐   DevOps + Platform + SRE: deploy plan, rollout/rollback, SLOs
        │  DEPLOY/OPS   │
        └──────┬───────┘
               ▼
        ┌──────────────┐   Tech Writer assembles docs + release notes (cheap model)
        │  DOCUMENT     │
        └──────┬───────┘
               ▼
        ┌──────────────┐   Orchestrator compiles final package + retrospective → MEMORY
        │  STABILIZE    │
        └──────────────┘
```

**Convergence rule (how disagreements resolve):**
1. CHALLENGE must include evidence or a concrete alternative — opinions alone are dropped.
2. The two agents get **one** exchange to resolve in the war room.
3. If still split, the **owning agent of that phase decides** (architect owns design,
   developer owns implementation, QA owns test adequacy, security can *block* on a
   high-severity finding — a hard veto).
4. The decision is recorded as an **ADR**; the loser's objection is preserved as a noted risk.
5. Only genuinely irreducible product/business trade-offs escalate to **you** (the human).

This caps the "agents argue forever" failure mode at one round + a deterministic owner.

---

## 6. How the orchestrator decides which agents to activate

Activation is driven by `routing.yaml`: a **complexity score** + **signal tags** extracted at
intake, matched against rules. The default is *minimal*: pull the fewest agents that satisfy
the task.

**Step 1 — Classify (at INTAKE).** The analyst tags the task:

- `complexity`: trivial / small / standard / complex (0–3)
- `signals`: e.g. `db-schema-change`, `public-api`, `auth`, `pii`, `infra`, `perf-critical`,
  `new-service`, `ui`, `payments`, `data-migration`, `breaking-change`

**Step 2 — Map signals → agents (always-on vs conditional):**

```yaml
always:        [requirements, developer, reviewer]          # every non-trivial task
conditional:
  architect:   complexity>=standard OR new-service OR breaking-change OR perf-critical
  qa:          complexity>=small OR public-api OR data-migration
  security:    auth OR pii OR payments OR public-api OR new-service
  devops:      infra OR new-service OR ci-change OR breaking-change
  platform:    new-service OR perf-critical OR infra
  sre:         new-service OR perf-critical OR slo-impacting
  tech_writer: public-api OR new-service OR complexity>=standard
skip_when_trivial: [architect, qa, security, devops, platform, sre, tech_writer]
```

**Step 3 — Efficiency guards (keep it lean):**

- **Trivial tasks** (typo, rename, one-line fix) bypass the loop: developer + a quick
  self-review, no war room.
- **Batching:** independent agents in the same phase run *in parallel* (QA writes tests
  while reviewer reviews).
- **Token budget:** the orchestrator gets a per-task budget; if a phase would exceed it,
  it drops the lowest-value conditional agent and notes the omission.
- **The "separate-engineer" test** (from multi-agent best practice): only fan out work that
  you could hand to different engineers with no further conversation; otherwise keep it
  sequential. Multi-agent runs can cost ~10–15× a single chat, so fan-out must earn it.
- **Cache hits:** if MEMORY already has an ADR/pattern for this, reuse it instead of re-deriving.

---

## 7. Phase-by-phase flows (what each phase actually does)

**Requirement analysis flow.** Analyst restates the request, lists assumptions, defines
acceptance criteria as testable statements, and emits *open questions*. QA reads along and
adds testability concerns. Exit gate: acceptance criteria exist and no `blocking` questions
remain unanswered.

**Planning & design flow.** Architect proposes a design (`PROPOSE`); developer reviews it for
*implementability* and raises `QUESTION`/`CHALLENGE`; platform/security join if their signals
fired. They co-produce `design-doc.md` and ADRs. Exit gate: design approved by developer
(can-build) and no open high-severity risks.

**Implementation flow.** Developer implements against spec+design. Blocking questions pause
only the developer, not the whole team. QA simultaneously authors `test-plan.md` and test
code from the *spec* (so tests aren't biased by the implementation). Exit gate: code compiles,
self-tests pass, PR description written.

**Code review flow.** Reviewer does a diff review (`REVIEW`: approve / request-changes / block),
checking correctness, edge cases, readability, and adherence to design. `request-changes`
loops back to IMPLEMENT. Security reviewer runs here too when routed. Exit gate: review
approved, no blocking findings.

**Testing & QA flow.** QA executes tests, adds edge/negative cases, validates acceptance
criteria, files bugs (`RISK`/bug reports) that loop back. Exit gate: acceptance criteria
pass; coverage of critical paths confirmed.

**DevOps / platform / deployment flow.** DevOps defines build/release pipeline and
rollout+rollback; platform confirms runtime fit (services, scaling, cost); SRE defines SLOs,
metrics/logs/traces, and alerts, and drafts a runbook. Exit gate: a deploy guide exists with
a tested rollback path.

**Documentation flow.** Tech Writer (cheap model) assembles README/API docs/changelog/deploy
guide and a human-readable summary from existing artifacts — it *compiles*, it doesn't invent.
Exit gate: docs reference real artifacts and pass a quick accuracy check.

**Feedback & iteration loop.** Any phase can emit a `RISK`/`CHALLENGE`/bug that routes work
backward. The orchestrator tracks loop count per task; if a task loops more than N times on
the same issue, it escalates to you with a summary of the deadlock. At STABILIZE, a short
retrospective writes lessons + reusable patterns into MEMORY.

---

## 7b. Working with an existing codebase (comprehension & localization)

The OS never edits code it hasn't oriented in first. This is the **GROUND** phase, owned by the
**Codebase Analyst**, and it produces two artifacts at two scopes:

**1. Repo Map — durable, cached at `.eaos/memory/codebase/map.md`.** Built once per repo (or via
a one-off indexing run), refreshed incrementally when git HEAD moves. It captures the stack,
directory responsibilities, entry points, the actual **build/run/test/lint commands**, test
layout, conventions (naming, error handling, logging, layering), key modules and their public
interfaces, integrations, and **danger zones** (auth, migrations, payments, generated code,
public APIs). Caching matters: the expensive full read happens once, not on every task.

**2. Impact Map — per task, at `.eaos/<id>/artifacts/impact-map.md`.** The localization step:
the exact files/symbols to edit, their callers (blast radius), the tests that cover them,
config/migrations touched, and a confidence note. This is what stops the architect/developer
from designing against an imagined codebase.

How it's done (cheap, grounded): `glob`/`grep`/`read` over the tree, reading existing
README/CLAUDE.md/CONTRIBUTING and package manifests/CI for the real commands, `git log`/`blame`
for recent history, and citing `file:line` for every claim — no assumptions.

**Three behaviors that fall out of this:**

- *Re-routing on evidence.* If the impact map shows the change actually touches a danger zone
  (say, the auth module), GROUND adds that signal and the orchestrator re-runs routing —
  pulling in security/platform **before** planning. What the code shows beats how the ask was
  phrased.
- *Bug tasks are reproduce-first.* When `kind == bug`, GROUND runs **bug-triage**: reproduce
  (ideally a failing test) → locate → write the **root cause** → scope a minimal fix. No fix is
  designed until the bug reproduces; the repro test becomes the permanent regression test. If it
  can't be reproduced, the OS escalates to you rather than guessing.
- *Staying in scope & on-convention.* The developer must edit the files in the impact map and
  follow the repo's conventions; the reviewer checks the diff for scope creep and convention
  drift; QA runs the **existing** suite (regression) in addition to new tests, so changes don't
  silently break the blast radius.

For a brand-new repo (`greenfield`) there's nothing to map — GROUND is skipped, the team
establishes structure, and the analyst maps it at STABILIZE for future tasks.

---

## 8. Example conversation flow between agents

Task: *"Add rate limiting to our public REST API."*

```
[INTAKE]
requirements → all (PROPOSE task-spec.md):
  Acceptance: 429 on exceeding limit; per-API-key; configurable; documented.
  signals: [public-api, perf-critical]  complexity: standard
  open Qs: limit values? per-key or per-IP? shared across instances?

[CLARIFY]
developer → user (QUESTION, blocking): per-key or per-IP, and is the service multi-instance?
user → all (DECISION): per-API-key, yes 3 instances behind a load balancer.

[PLAN/DESIGN]  (routing pulled: architect, platform, security, qa)
architect → all (PROPOSE design-doc.md):
  Token-bucket in Redis (shared across instances), middleware layer.
platform → architect (CHALLENGE, evidence): a managed Redis adds cost + a network hop on
  every request; at our QPS that's ~8ms p50 overhead. Consider the API gateway's built-in
  rate limiter — zero extra infra.
architect → platform (one exchange): gateway limiter can't do per-API-key with our custom
  key scheme. Accept the Redis hop; it's within the 50ms budget.
DECISION (architect owns design) → ADR-007: Redis token-bucket; risk noted: added dependency.
security → all (RISK, medium): ensure limiter fails *open* vs *closed* deliberately; a Redis
  outage shouldn't 500 the whole API. Mitigation: fail-open with alert.
qa → all (PROPOSE test-plan.md): cases — under limit, at limit, over limit, burst, Redis down
  (fail-open), multi-instance fairness.

[IMPLEMENT]   developer builds middleware; QA writes tests in parallel.
[REVIEW]      reviewer (REVIEW: request-changes): header `Retry-After` missing on 429. → loop.
              developer fixes → reviewer (REVIEW: approve).
[TEST/QA]     qa: all pass except multi-instance fairness (bug) → loop → fixed → pass.
[DEPLOY/OPS]  devops: feature-flag rollout + rollback; sre: alert on limiter error-rate & Redis
              latency; SLO unchanged.
[DOCUMENT]    tech-writer: API docs note the 429 + Retry-After + limit config + changelog entry.
[STABILIZE]   orchestrator: package + retro → MEMORY pattern "distributed-rate-limit".
```

Notice: the *platform challenge* changed nothing about the chosen tech but produced a recorded
risk and a budget check; the *security risk* changed the design (fail-open); QA tested from the
spec. That's the collaboration layer doing its job.

---

## 9. Suggested repo / folder structure

```
eng-agent-os/                  # the repo (version this; it IS the distribution)
├── README.md                  # what it is + quickstart
├── AGENT_OS.md                # this design doc (the spec)
├── ROADMAP.md                 # phased plan + business-pack extension
├── setup.sh                   # bootstrap: clone agency-agents + install everything
├── commands/
│   └── agentic-os.md          # the /agentic-os slash command (autonomous driver)
├── orchestrator/
│   ├── orchestrator.md        # orchestrator role spec (the command's canonical form)
│   ├── routing.yaml           # activation + model routing + autonomy gates + budget
│   ├── protocol.md            # message schema + self-owned comms + convergence rule
│   └── loop.md                # phase state machine + entry/exit gates
├── agents/
│   ├── README.md              # how EAOS agents relate to / inherit agency-agents
│   ├── requirements-analyst.md … tech-writer.md   # the 10 team personas
├── skills/                    # requirement-intake / test-plan / deployment-guide
├── templates/                 # task-spec / design-doc / adr / review-notes / test-plan
├── memory/README.md           # decisions/, patterns/, lessons/ structure (reference)
└── examples/rate-limit-walkthrough.md

# Installed by setup.sh into the home dir:
~/.claude/
├── commands/agentic-os.md     # so you can type /agentic-os anywhere
├── agents/*.md                # EAOS team + agency-<name>.md specialists
├── skills/*/SKILL.md
└── eaos/                      # OS config the command reads at runtime
    ├── routing.yaml · protocol.md · loop.md · orchestrator.md · templates/

# Created per-project at runtime (where you invoke /agentic-os):
./.eaos/
├── T-001/warroom.md           # orchestrator-owned conversation log
├── T-001/artifacts/           # spec, design, ADRs, tests, deploy guide, docs
└── memory/{decisions,patterns,lessons}/   # this codebase's accumulated knowledge
```

`setup.sh` clones agency-agents, installs both persona sets into `~/.claude/agents/`, installs
the `/agentic-os` command + OS config, and skills. The repo travels independently and is the
unit you version; runtime state stays project-local so each codebase keeps its own memory.

---

## 10. Suggested technologies / frameworks

- **Substrate (now):** Claude Code subagents invoked via the Task tool, driven by the
  `/agentic-os` slash command on the main session. We deliberately **do not** depend on the
  experimental Agent Teams feature — the orchestrator owns coordination itself (file-based war
  room + relay), so the system works on stock Claude Code and stays portable.
- **Persona format:** plain Markdown with YAML frontmatter (`name`, `model`, `description`,
  `tools`) — same format agency-agents uses, so they interoperate and convert.
- **Coordination state:** files on disk (`.eaos/<id>/warroom.md`, `artifacts/`, `memory/`).
  The orchestrator is the single writer of the war room; no database, no harness features.
- **Skills:** Claude Code skills for repeatable procedures (intake, test-plan, deploy guide).
- **Coding tools / open-source integration:** drive the developer agent with whatever coding
  CLI you prefer — Claude Code itself, or shell out to Aider / OpenHands / Codex CLI for the
  raw code edits — the developer persona just needs file + shell + test tools.
- **Portability layer (later):** agency-agents already ships conversion scripts to Codex CLI,
  Cursor, Copilot, Gemini CLI; reuse them for EAOS personas. A thin **LangGraph** wrapper is
  the escape hatch if you outgrow Claude Code's orchestration and want explicit graph state.
- **Version control:** the whole OS is a git repo; that *is* the distribution mechanism.

---

## 11. Model selection / routing strategy

Three tiers, assigned per agent in frontmatter and overridable per phase in `routing.yaml`.
(Current Claude lineup: **Opus 4.8** = strongest reasoning; **Sonnet 4.6** = balanced/coding;
**Haiku 4.5** = cheap/fast.)

| Tier | Model | Used for | Agents |
|---|---|---|---|
| **Reasoning** | Opus 4.8 | planning, architecture, threat modeling, hard review calls, orchestration | orchestrator, architect, requirements, security, (platform) |
| **Coding** | Sonnet 4.6 | implementation, test code, diff review, pipeline config | developer, qa, reviewer, devops, sre |
| **Cheap/Fast** | Haiku 4.5 | docs, summaries, formatting, changelog, routine checks, status rollups | tech-writer, status/summarize sub-steps |

Routing principles:
- **Escalate on hardness, not on role.** A "standard" implementation review stays on Sonnet;
  a `block`-level or security-sensitive review escalates that single call to Opus.
- **De-escalate boilerplate.** Even reasoning-tier agents drop to Haiku for their pure
  summarize/format sub-steps.
- **Specialists only when signaled.** Security/platform/SRE don't spin up unless their tags
  fired — saving their (often Opus-tier) cost on tasks that don't need them.
- **Budget-aware downgrade.** If a task is over budget, conditional agents downgrade one tier
  before being dropped entirely.

---

## 12. Phased implementation roadmap

**Phase 0 — Bootstrap (½ day).** `setup.sh` clones agency-agents, installs EAOS personas +
skills into `~/.claude/`. Verify agents are callable in Claude Code.

**Phase 1 — MVP loop (2–3 days).** Orchestrator + 4 agents (requirements, architect, developer,
reviewer) + war room + protocol + routing for a single linear pass. No parallelism. (See §13.)

**Phase 2 — QA + iteration (2–3 days).** Add QA agent, the test phase, and backward loops
(request-changes / bug → re-implement). Add the convergence rule.

**Phase 3 — Ops & specialists (3–4 days).** Add security, devops, platform, SRE, tech-writer +
their routing signals. Turn on parallel execution within a phase.

**Phase 4 — Memory & efficiency (2–3 days).** Add MEMORY (ADRs/patterns/lessons), reuse-on-cache,
token budgets, model-routing overrides, retrospectives.

**Phase 5 — Hardening & portability (ongoing).** Tune skip rules from real runs; add the
LangGraph escape hatch if needed; run conversion scripts to a second harness to prove portability.

**Phase 6 — Business pack (future).** See §15.

---

## 13. The MVP you build first

A deliberately tiny version that already feels like a team. **Four agents, one linear loop,
one war-room file, no parallelism, no specialists.**

```
INTAKE (requirements) → CLARIFY (blocking Qs to you) → PLAN (architect+developer co-design)
→ IMPLEMENT (developer) → REVIEW (reviewer) → done
```

Concretely:
1. Run `setup.sh` (Phase 0).
2. From inside your project, run: `/agentic-os <your task>`.
3. It creates `.eaos/T-001/warroom.md`, calls requirements → writes `task-spec.md`.
4. It asks you any blocking questions, then runs architect+developer planning (one CHALLENGE
   round allowed), produces `design-doc.md`.
5. Developer implements; reviewer reviews; request-changes loops once if needed.
6. Orchestrator hands you: code + spec + design + review notes.

This MVP proves the three hard things — **clarification before building, co-planning, and a
review loop** — with the least machinery. Everything after is additive.

This repo ships that MVP: the four agent files, orchestrator, routing (MVP subset), protocol,
and a worked example are all included and runnable.

---

## 14. How prompts, skills, tools, and memory are structured

- **Prompts (personas):** each `agents/*.md` is a structured prompt — identity, activation
  condition, inputs it reads, outputs it must produce, message types it may send, and its
  model tier. Keep them declarative; the orchestrator supplies the task context.
- **Skills:** reusable *procedures* (intake, test-plan, deploy-guide) that any agent can call,
  so the "how" lives in one place and personas stay about "who/what."
- **Tools:** scoped per agent in frontmatter — e.g. tech-writer gets read+write but not shell;
  developer gets shell+tests; reviewer gets read-only + comment. Least privilege keeps agents
  honest and cheap.
- **Memory:** three folders — `decisions/` (ADRs, immutable), `patterns/` (reusable solutions),
  `lessons/` (retro notes). The orchestrator checks memory at PLAN to reuse prior decisions and
  writes to it at STABILIZE. This is what makes the OS get smarter per project over time.

---

## 15. Future extension: startup / business workflows

The whole point of making this an "OS" is that the **orchestrator, protocol, routing engine,
war room, and memory don't change** — you add a new *agent pack* and new *signals*.

- **New pack `agents/business/`:** CEO, CTO, Product Manager, Business Planner, Finance,
  Marketing, Sales. Same persona format, same message types (PROPOSE/CHALLENGE/DECISION fit
  business debate perfectly).
- **New loop preset (`loop.md` profile):** e.g. *opportunity → product spec → GTM → financial
  model → build (hands off to the engineering loop) → launch → measure.* The engineering loop
  becomes a **sub-routine** the CTO/PM invoke.
- **New routing signals:** `revenue-impact`, `fundraising`, `gtm`, `pricing`, `hiring` → pull
  finance/marketing/sales the same way `auth` pulls security today.
- **Cross-pack collaboration:** PM ↔ Architect already speak the same protocol, so "PM asks
  Architect for a feasibility estimate" is just a `QUESTION` across packs — no new plumbing.
- **Model routing extends unchanged:** CEO/strategy/finance reasoning → Opus; marketing copy
  & formatting → Haiku; etc.

So EAOS becomes the *engineering division* of a larger **Agentic Operating Company**, and the
business pack is the executive + go-to-market divisions running on the identical machinery.

---

## 16. Mapping to the 9-component "Agentic OS" model

A useful external framing (MindStudio, *9 Components You Need*) says any agentic OS is really
**structured context management** built from nine components. EAOS implements all nine — and
the two that the framing warns are usually under-built (context compression and out-of-loop
evaluation) are called out so we build them on purpose.

| # | Component | Where EAOS implements it |
|---|---|---|
| 1 | **Identity files** | `agents/*.md` + `orchestrator.md` — versioned personas with role, authority, model tier, tools |
| 2 | **Short-term memory** | the per-task war room + the slices the orchestrator relays into each subagent prompt. **Compression:** the orchestrator passes *summaries/decisions*, not full transcripts (see note below) |
| 3 | **Long-term memory** | `.eaos/memory/` — `decisions/` (ADRs) + `patterns/` + `lessons/`, read at PLAN, written at STABILIZE. (Optional: add a vector store for semantic recall over a large codebase) |
| 4 | **Skills & tools** | `skills/` (intake, test-plan, deploy-guide) + per-agent `tools:` frontmatter (least privilege) |
| 5 | **Planning / reasoning** | the architect↔developer co-design round + the orchestrator's explicit goal restatement at each gate (hierarchical + checkpointed) |
| 6 | **Orchestration** | the `/agentic-os` loop — centralized routing via `routing.yaml`, with agents self-directing within scope (the recommended hybrid) |
| 7 | **Handoff protocols** | the `protocol.md` message schema (PROPOSE/HANDOFF/… with `ref` + decisions + open questions) — structured, parseable handoffs, not raw transcripts |
| 8 | **Evaluation / feedback** | **in-loop:** REVIEW + TEST/QA gates. **out-of-loop:** retrospectives → `lessons/`; *recommended add-on* below |
| 9 | **Security / guardrails** | security-reviewer (hard veto) + least-privilege tools + human gates for destructive actions + the war room as an audit log |

Two deliberate strengthenings prompted by that framing:

- **Context compression (component 2).** The orchestrator must summarize a completed phase
  before starting the next — it passes the *decision and the artifact path*, not the whole
  phase transcript, into the next subagent. This is written into `agentic-os.md` and is what
  keeps long runs inside the context window.
- **Out-of-loop evaluation (component 8).** Beyond the review/test gates, add a lightweight
  `evaluator` pass (cheap model, or a subagent) at STABILIZE that scores the delivery against
  the acceptance criteria and logs a thumbs-up/down + reason to `lessons/`. Over time these
  become an eval set you can run before changing any persona — catching persona regressions
  the way you'd catch code regressions. (Roadmap Phase 4.)

Also worth adopting from the same source: treat **prompt injection** as an input guardrail —
when an agent ingests external content (a fetched page, a dependency's README, an untrusted
file), it should treat embedded instructions as data, not commands. Add this line to the
developer/requirements personas if your tasks pull in external content.

---

## Appendix: design principles (the rules that keep it from becoming a mess)

1. **Files over state.** Everything important is a file in git → portable, auditable, resumable.
2. **Minimal activation.** Default to the fewest agents; make adding agents earn its cost.
3. **Disagreement is bounded.** One exchange, then a deterministic owner decides; security can veto.
4. **Tests come from the spec, not the code.** QA designs from acceptance criteria.
5. **Specialists are signaled, not standing.** Security/platform/SRE appear only when tags fire.
6. **The orchestrator routes; it doesn't do the work.** Keep the lead thin.
7. **Memory compounds.** Every task leaves the system a little smarter.
8. **Substrate is swappable.** Never hardcode a harness assumption into a persona.
```
```

---

### Sources
- [msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents)
- [Shipyard — Multi-agent orchestration for Claude Code in 2026](https://shipyard.build/blog/claude-code-multi-agent/)
- [Claude Subagents Explained: Multi-Agent Orchestration Guide (2026)](https://getaitopia.io/blog/claude-subagents-explained-multi-agent-orchestration)
- [Anthropic — Claude Code Agent Teams docs / multi-agent orchestration](https://medium.com/neuralnotions/multi-agent-orchestration-in-claude-code-the-architecture-and-economics-of-subagents-06d52e69f8b2)
- [MindStudio — How to Build an Agentic Operating System: 9 Components You Need](https://www.mindstudio.ai/blog/how-to-build-agentic-operating-system-9-components)
