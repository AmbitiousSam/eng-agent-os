# EAOS Adapters — run the same OS from any agentic IDE

EAOS is deliberately harness-agnostic: the brain is markdown (command + playbooks + personas +
protocol), and runtime state is plain files (`.eaos/`). Any tool that can **read/write files**
can run it. But "subagent support" in the table below does not mean equivalent quality — see
[What degrades and why](#what-degrades-and-why) before you assume a 🟡 row behaves like Claude
Code.

| Tool | Adapter | Parallel agents? |
|---|---|---|
| **Claude Code** | native — `setup.sh` installs `/agentic-os` | ✅ Task subagents (fresh isolated context per spawn) |
| **Cursor** (2.4+) | `adapters/cursor/` → rules + subagents | 🟡 manual port: copy personas by hand; quality depends on the tool's subagent + context-isolation support |
| **Windsurf / Devin Desktop** | `adapters/windsurf/` → `/agentic-os` workflow | 🟡 manual port: copy personas by hand; quality depends on the tool's subagent + context-isolation support |
| **Codex CLI / app** | `adapters/codex/` → AGENTS.md + `.codex/agents` | 🟡 manual port: copy personas by hand; quality depends on the tool's subagent + context-isolation support |
| **ANY AGENTS.md-reading tool** (Zed, opencode, CodeWhale, Swival, Copilot CLI, …) | `adapters/AGENTS.md` → copy to repo root | 🟡 per tool |
| anything else (files only, no subagents) | [`adapters/solo-mode.md`](solo-mode.md) | ❌ single context — use solo-mode, not role-play |

> **Universal fallback:** `adapters/AGENTS.md` uses the AGENTS.md standard that most agents now
> read automatically. If your tool isn't listed above, start there — it requires zero
> tool-specific setup. If it has no subagent/context-isolation feature at all, go straight to
> [`adapters/solo-mode.md`](solo-mode.md) instead of role-playing the team.

## What degrades and why

EAOS's quality in Claude Code comes from four mechanical properties, not from the personas'
wording:

1. **Fresh, isolated subagent contexts.** Each spawn starts with no memory of how the work was
   built. This is what makes maker≠checker *real* — the reviewer and verifier literally cannot
   see the developer's reasoning, only the artifacts.
2. **Genuine multi-sampling.** Independent agents draw independent samples from the model;
   disagreement is a real second opinion, not the same context re-reading its own output.
3. **Model-tier routing.** Cheap/fast models for mechanical roles, stronger models for judgment
   calls — a real cost/quality trade, not just a label.
4. **Frontmatter tool scoping.** A read-only reviewer literally cannot edit files; the boundary
   is enforced by the harness, not by the reviewer's good behavior.

A tool without subagents (or without real context isolation between them) loses all four —
there is one context, one continuous memory, one sample. Manually role-playing the personas in
that single context keeps the *ceremony* (the persona names, the message types, the phase
structure) but not the *mechanism* that made the ceremony worth anything: the "reviewer" is the
same model, in the same context, that just wrote the code, grading its own homework with a
different hat on. That's single-agent quality at multi-agent token cost — worse than just
asking the model to do the task well once.

This is why the 🟡 rows above say "manual port" rather than "✅": copying the persona files into
a tool's subagent format is necessary but not sufficient. If that tool's subagents don't give
each spawn a genuinely separate context (no shared scratchpad, no visible prior reasoning), you
have not reproduced EAOS's quality guarantee — you've reproduced its file layout. Verify your
tool's isolation behavior before trusting a 🟡 row to behave like Claude Code's ✅ row. When in
doubt, or when the tool has no subagent feature at all, use
[`adapters/solo-mode.md`](solo-mode.md) — it drops the ceremony that can't be enforced and
keeps the one trick that ports anywhere: a second, genuinely fresh session as the checker.

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
