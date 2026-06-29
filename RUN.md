# Running EAOS in Claude Code

## One-time setup
```bash
cd ~/Downloads/eng-agent-os
./setup.sh          # clones agency-agents + installs personas, skills, /agentic-os command, config into ~/.claude
```
Restart Claude Code (or reload) so it picks up the new command and agents.

## Use it (from inside any project)
```
/agentic-os <your task>
```

### Example: the task planner in this demo
```
/agentic-os Build a modern, production-shippable daily task planner web app. It must feel
designed by a real product team (not AI-generated): a clean design system with light/dark,
priority + due dates + projects, filter/search, progress, drag-to-reorder, edit, delete-with-undo,
full keyboard + screen-reader support, persistence, and no security holes. Client-only v1, no
build step, deployable to any static host.
```

## What happens
1. **Requirements** writes a spec with testable acceptance criteria + classifies the task.
2. **Ground** (skipped here — greenfield; on an existing repo it maps the code + writes an impact map).
3. **Clarify** — it asks you only the blocking questions (e.g. backend vs client-only), then runs autonomously.
4. **Plan** — architect + developer co-design (with one challenge round); ADRs recorded.
5. **Implement** — developer builds; **QA** writes tests in parallel.
6. **Review** — code-reviewer (+ security) loop until approved.
7. **Test** — QA runs tests; bugs loop back.
8. **Deploy/Docs/Stabilize** — deploy guide, README, retro + scorecard.

Everything is logged to `./.eaos/T-001/` (war room + artifacts) in the project you run it in.

## Knobs
- **Autonomy / human gates:** `~/.claude/eaos/routing.yaml` → `autonomy`.
- **Which agents run when:** same file → `agents.conditional`.
- **Model per role (cost/quality):** `models.by_agent` (reasoning=opus, coding=sonnet, cheap=haiku).
- **Loop guard / budget:** `loop_guard`, `budget`.

## Tip
Multi-agent runs cost more tokens than a single chat. For small tasks the routing rules keep it
lean (trivial → fast-path, greenfield → skip GROUND, specialists only when signaled). For big
features, that's where the value is.
```
