# Design: hosts own their subagents (v4.5.0)

Approved by Siva 2026-09-19. Supersedes the headless work shipped in v4.4.0.

## Why

v4.4.0 added `eaos checker run`, `eaos drain`, host detection and a paste packet, all on the premise
that Cursor and Codex cannot spawn an isolated context. The premise was wrong and was never checked.
Cursor has custom subagents with their own context window, can run them in parallel, and loads them
from `~/.claude/agents/` (Cursor docs, "Custom Subagents"), which is exactly where EAOS installs
`eaos-builder`, `eaos-reader` and `eaos-checker`. The hosts manage their own parallel agents. EAOS
should not.

## What changes

1. **Runtime (`eaos/runtime/eaos`):** delete `checker run`, `drain`, `detect_host`, `host_argv`,
   `run_host`, `auth_hint`, `eaos_path_for_prompt`, `front_door_for`, `checker_prompt`, their argparse
   entries and the `shlex` / `shutil` imports. Delete the fake-host tests.
2. **Front door (`eaos/agentic-os.md`):** one instruction for every host: spawn `eaos-checker`. One
   fallback line: a host that cannot start a fresh context tells the human the check needs a new chat
   and stops; it never grades its own work.
3. **Skill header (`eaos/adapters/skill-head.md`):** a few lines: the same three agents load from
   `~/.claude/agents/`; hooks are Claude Code only. No packet.
4. **Goal checklist:** two ways to keep one item per context: subagents in the same chat until the
   context ceiling, otherwise a fresh chat per item.
5. **Files deleted:** `eaos/adapters/solo-mode.md`, `eaos/adapters/AGENTS.md`. Installer, doctor and
   validator stop referencing them; `--uninstall` and the next install remove installed copies.
6. **README, `routing.yaml`, `eaos/adapters/README.md`:** independent checker = subagent on every host.

## Not doing

- Merging the Claude command and the skill into one file: changes the entry point twelve real runs used.
- Cursor hooks for the scenario guard and pen gate: real gain, separate work, after a real Cursor run.
- Anything for Codex agent loading: not verified from Codex's own docs.
- `readonly: true` on the checker: it must run tests and record verdicts through the script.

## Verification

`bash tests/run.sh`. Then one real internal-stakes task in Cursor via `/agentic-os`, looking for an
`eaos-checker` subagent being spawned and verdicts recorded by it.
