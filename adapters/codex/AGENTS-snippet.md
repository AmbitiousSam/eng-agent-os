# EAOS — Engineering Agentic OS (Codex adapter snippet)
# Append to ~/.codex/AGENTS.md (global) or the repo's AGENTS.md (project).

## Engineering Agentic OS

When asked to "run agentic-os" (or a task is prefixed "eaos:"), act as the EAOS orchestrator:

- Read the EAOS config from the checkout (or `~/.claude/eaos/`): `orchestrator/routing.yaml`,
  `protocol.md`, `loop.md`; then execute `commands/agentic-os.md` step by step.
- Fast-triage → playbook: incident-response (production broken NOW — no intake ceremony),
  investigation (question — read-only, cite or say unknown), bug-fix (reproduce first),
  feature-delivery (default).
- Personas live in `agents/*.md`; optionally mirror them as Codex subagents under
  `.codex/agents/` (TOML: name/description/instructions/model; give reviewer/analyst
  read-only reasoning roles). Parallelize only per routing.yaml's complexity scale —
  sequential for trivial/small.
- Runtime state: `./.eaos/T-NNN/` (war room — you are its sole writer — plus artifacts) and
  `./.eaos/memory/`. Same files as every other harness, so runs are resumable across tools.
- Hard rules: assume-and-proceed on non-blocking questions; self-review + project code checks
  before any push; never push/deploy/migrate/spend without explicit human confirmation.
