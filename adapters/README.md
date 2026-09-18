# EAOS adapters — capability, not equality

EAOS v4 is markdown plus a shell CLI, so any host that can run a command can use it. A
new chat reproduces a context boundary; it does not reproduce permissions or enforcement.
`orchestrator/routing.yaml > adapters` records, per host, what each capability actually
is: **enforced** (a runtime or hook refuses the wrong action), **measured** (recorded, not
prevented), **advisory** (a documented rule), **manual** (the human does it), **planned**.

| Capability | Claude Code | Other hosts |
|---|---|---|
| Fresh-context unit | enforced (Agent subagent) | manual: new chat + `eaos status --packet` |
| Checker without the maker's transcript | advisory (prompt construction; artifacts stay readable) | advisory |
| Spawn budget and blocked-task gate | enforced via PreToolUse hook, fail-open on infrastructure | advisory |
| Stop-time audit | enforced via Stop hook, fail-open on infrastructure | advisory |
| Check evidence bound to a snapshot | enforced by `eaos check` + `unit handoff` | enforced (same CLI) |
| Writer lease | advisory (runtime lease; edits not gated) | advisory |
| Context ceiling | measured (Stop hook records size; cannot force a reset) | manual |

`solo-mode.md` is the manual procedure for a host without subagents: the checker is a new
session given only the spec, the diff, the board view for checkers and the check commands.
The `cursor/`, `codex/` and `windsurf/` directories hold host-specific notes from v3 and are
kept for reference; every claim in them is advisory until probed on that host.
