# EAOS across hosts

EAOS is markdown plus one runtime script the agent runs. The host (Claude Code, Cursor, Codex) owns
models, tools, permissions and subagents. EAOS does not manage agents; it names three boundaries
(`eaos-builder`, `eaos-reader`, `eaos-checker`) and the host spawns them, each in its own fresh context.
Claude Code and Cursor both load them from `~/.claude/agents/`, where `setup.sh` installs them.

`routing.yaml > adapters` records what each capability actually is per host: **enforced** (the script
or a hook refuses the wrong action), **measured** (recorded, not prevented), **advisory** (a documented
rule), **absent**.

| Capability | Claude Code | Cursor, Codex |
|---|---|---|
| Board, snapshot-bound evidence, scenarios, goals, verdict rules | enforced (script) | enforced (same script) |
| Fresh-context builder, reader, checker | host subagent | host subagent |
| Checker never receives the maker's transcript | advisory (how the lead builds the prompt) | advisory |
| Spawn budget, session binding, stop-time audit | hook, fails open on infrastructure | absent |
| Scenario store unreachable by tools; one writer per workspace | hook (not against a disguised shell command or `sed`) | absent |
| Context ceiling | measured by hook; cannot force a reset | absent |

`skill-head.md` is the header `setup.sh` puts in front of the front door when it generates the global
skill for Cursor and Codex. A host with no way to start a fresh context gets one rule from the front
door: say the check needs a new chat and stop; never grade your own work.
