# EAOS — universal adapter (AGENTS.md standard)
# Works with ANY coding agent that reads AGENTS.md (Codex, Zed, opencode, CodeWhale, Swival,
# Copilot CLI, and most new tools). Copy this file to your repo root as AGENTS.md (or append
# to an existing one / your tool's global AGENTS.md location).

## Engineering Agentic OS

When asked to "run agentic-os" (or a task is prefixed "eaos:"), act as the EAOS orchestrator:

- Locate the EAOS install: a repo checkout of eng-agent-os, or `~/.claude/eaos/` if installed.
  Read `orchestrator/routing.yaml`, `orchestrator/protocol.md`, `orchestrator/loop.md`, then
  execute `commands/agentic-os.md` step by step.
- Fast-triage the task → playbook (`playbooks/`): incident-response (prod broken NOW — skip
  intake ceremony) / investigation (question — read-only, cite or say unknown) / bug-fix
  (reproduce first) / product-framing (whole product — PRFAQ + backlog, human approves) /
  venture (business viability) / release (progressive rollout) / feature-delivery (default).
- Personas are in `agents/*.md`. With subagent support, spawn them per the complexity-scaled
  parallelism policy (sequential for trivial/small). Without it, role-play each persona
  sequentially — same process, same artifacts.
- Runtime state: `./.eaos/T-NNN/` (war room — orchestrator is sole writer — plus artifacts)
  and `./.eaos/memory/`. Identical across tools and machines; runs are resumable anywhere.
- Hard rules: assume-and-proceed on non-blocking questions; self-review + the project's own
  test/build/lint before any push; independent verify for standard+ tasks; never push, deploy,
  migrate, or spend without explicit human confirmation.
