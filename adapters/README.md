# EAOS Adapters — run the same OS from any agentic IDE

EAOS is deliberately harness-agnostic: the brain is markdown (command + playbooks + personas +
protocol), and runtime state is plain files (`.eaos/`). Any tool that can **read/write files**
can run it — subagent support makes it parallel; without subagents it runs as one agent
role-playing the team sequentially (same process, same artifacts, no parallelism).

| Tool | Adapter | Parallel agents? |
|---|---|---|
| **Claude Code** | native — `setup.sh` installs `/agentic-os` | ✅ Task subagents |
| **Cursor** (2.4+) | `adapters/cursor/` → rules + subagents | ✅ subagents / Build-in-Parallel |
| **Windsurf / Devin Desktop** | `adapters/windsurf/` → `/agentic-os` workflow | ✅ subagents (Devin Local) |
| **Codex CLI / app** | `adapters/codex/` → AGENTS.md + `.codex/agents` | ✅ TOML subagents |
| anything else (files only) | point it at `commands/agentic-os.md` | 🟡 sequential role-play |

## The contract every adapter relies on
1. The driver is `commands/agentic-os.md` — a tool-neutral procedure.
2. Config lives in `orchestrator/` (routing, protocol, loop) + `playbooks/` + `agents/`.
3. Runtime state is `./.eaos/` in the target repo — identical across tools, so you can start a
   task in Claude Code and resume it in Cursor.

## Install per tool
- **Cursor:** copy `adapters/cursor/eaos.mdc` into the repo's `.cursor/rules/`; import
  `agents/*.md` as Cursor subagents (same frontmatter format; add `readonly: true` for
  code-reviewer / codebase-analyst / incident-commander per their tools).
- **Windsurf/Devin:** copy `adapters/windsurf/agentic-os.md` into `.windsurf/workflows/` →
  invoke as `/agentic-os` in Cascade.
- **Codex:** append `adapters/codex/AGENTS-snippet.md` to `~/.codex/AGENTS.md` (or the repo's
  `AGENTS.md`); optionally define the personas as TOML subagents in `.codex/agents/`.

> Paths/feature names move fast in these tools — if an install path has changed in your
> version, the adapter content is still correct; only the destination differs. Check your
> tool's docs for "rules", "workflows", or "subagents" locations.
