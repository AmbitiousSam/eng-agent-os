# Using EAOS in other IDEs (Cursor · Windsurf / Devin Desktop · Codex)

> **Ready-made adapters now live in [`adapters/`](../adapters/README.md)** — Cursor rule,
> Windsurf/Devin workflow, and a Codex AGENTS.md snippet. Copy the file into your tool's
> rules/workflows location and you're done; this doc explains the mapping behind them.
> Runtime state (`./.eaos/`) is identical across tools, so a task started in Claude Code can
> be resumed in Cursor or Codex. **None of these adapters reproduce Claude Code's quality
> guarantee automatically** — see `adapters/README.md`'s "What degrades and why" section. If
> your tool doesn't give each spawn a genuinely isolated context, use
> [`adapters/solo-mode.md`](../adapters/solo-mode.md) instead of role-playing the personas.

EAOS has two layers, and they port differently:

- **The coordination brain is 100% portable.** The war room, artifacts, memory, protocol,
  loop, and templates live in `.eaos/` — they're just files. Any agentic tool that can read and
  write files in the repo uses them unchanged. Coordination was built as files *on purpose* so
  it never depends on a single vendor's feature.
- **The driver needs a thin per-tool adapter** — how the loop is *invoked* and how subagents
  (on different models) are *spawned*. As of writing, several major tools advertise native
  subagent-like features — verify against your tool's current docs, since this space moves
  fast and the adapter's correctness depends on what your specific version actually supports.

## Primitive mapping

| EAOS primitive | Claude Code (shipped) | Cursor (as of writing) | Windsurf / Devin Desktop (as of writing) |
|---|---|---|---|
| Persona = markdown + YAML frontmatter, per-agent model | `~/.claude/agents/*.md` | **subagents** (md + frontmatter: name/description/model/`readonly`) | **subagents** (Devin Local) |
| `/agentic-os` slash driver | `commands/agentic-os.md` | custom command / driver subagent | **`/workflow`** in `.windsurf/workflows/*.md` |
| Skills (`SKILL.md`) | `~/.claude/skills/` | **Skills** (SKILL.md manifests) | rules + workflows |
| Rules / standards | `CLAUDE.md` | `.cursor/rules/*.mdc` | `.windsurf/rules/*.md` |
| Spawn subagents + agent-to-agent | Task tool | **subagents + "Build in Parallel"** | subagents (Devin Local) |
| Per-agent model routing | frontmatter `model:` | per-subagent model config | per-subagent |
| War room / artifacts / memory | `.eaos/` files | `.eaos/` files | `.eaos/` files |

> Note: as of writing, Windsurf and Devin Desktop are referenced together here because of a
> reported Cognition/Windsurf relationship. This repo has not verified that claim independently
> — check your tool's current docs/branding before relying on it, and treat "Windsurf / Devin
> Desktop" in this doc as "whichever of the two your install actually is."

## Cursor setup

1. Copy the personas from `agents/*.md` into Cursor's subagents directory (Cursor uses the same
   markdown + YAML frontmatter format; add the `readonly` flag for read-only roles like
   `code-reviewer` and `codebase-analyst`, and set `model:` per the tiers in `routing.yaml`).
2. Copy `skills/*/SKILL.md` into Cursor Skills.
3. Put team standards from this repo into `.cursor/rules/*.mdc` (e.g. "always escape user input
   before innerHTML", "tests come from the spec").
4. Turn `commands/agentic-os.md` into a Cursor custom command (or a top-level "orchestrator"
   subagent). It drives the same loop and uses **Build in Parallel** to fan out specialists.
5. Keep `.eaos/` in the repo — the war room/artifacts/memory work identically.

## Windsurf / Devin Desktop setup

1. Save `commands/agentic-os.md` as a workflow: `.windsurf/workflows/agentic-os.md`. It's then
   invoked as **`/agentic-os <task>`** in Cascade — same UX you have in Claude Code.
2. Put personas + standards into `.windsurf/rules/*.md` (and/or as subagents in Devin Local).
3. Copy skills' procedures into workflows or rules.
4. `.eaos/` files travel with the repo and are used unchanged.

## Graceful degradation (tools without subagents)

If your tool has no subagent feature — or you can't verify that its subagents give each spawn a
genuinely isolated context — do not have one agent role-play the team sequentially. That keeps
the persona names and phase headers but not the mechanism (fresh-context review, independent
verification, model tiering, tool scoping) that makes the ceremony worth its token cost; see
`adapters/README.md`'s "What degrades and why". Use [`adapters/solo-mode.md`](../adapters/solo-mode.md)
instead: it keeps GROUND, the task spec with acceptance criteria, assume-and-proceed
clarification, and the pre-push/test-build-lint gate, and replaces in-context "verification"
with a second, genuinely fresh session grading the diff against the spec.

## Recommended structure for multi-IDE repos

Commit the tool-neutral OS into the repo and keep thin adapters side by side:

```
your-repo/
├── .eaos/                      # runtime: war room, artifacts, memory (all tools)
├── eng-agent-os/               # the OS source (personas, loop, protocol, templates)
├── .claude/commands/agentic-os.md      # Claude Code adapter
├── .windsurf/workflows/agentic-os.md   # Windsurf/Devin adapter
└── .cursor/rules/ + Cursor subagents   # Cursor adapter
```

agency-agents already ships conversion scripts to several of these targets — reuse them for the
EAOS personas to generate the per-tool variants automatically.

Sources: [Cursor Subagents docs](https://cursor.com/docs/subagents) ·
[Cursor 2.4 changelog](https://cursor.com/changelog/2-4) ·
[Windsurf Workflows docs](https://docs.windsurf.com/windsurf/cascade/workflows) ·
[Windsurf Wave 8 customization](https://devin.ai/blog/windsurf-wave-8-cascade-customization-features)
