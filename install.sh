#!/usr/bin/env bash
# EAOS one-step install / update. Safe to re-run.
#   curl -fsSL https://raw.githubusercontent.com/AmbitiousSam/eng-agent-os/main/install.sh | bash
# Options (env): EAOS_SRC=<dir> where the checkout lives (default ~/.eaos-src)
#                EAOS_NO_HOOKS=1 skip wiring Claude Code hooks      EAOS_REF=<tag|branch> (default main)
set -euo pipefail
SRC="${EAOS_SRC:-$HOME/.eaos-src}"; REF="${EAOS_REF:-main}"
REPO="https://github.com/AmbitiousSam/eng-agent-os.git"
say() { printf "\033[1;36m[eaos]\033[0m %s\n" "$*"; }
for bin in git python3; do command -v "$bin" >/dev/null 2>&1 || { say "missing dependency: $bin"; exit 1; }; done

if [ -d "$SRC/.git" ]; then
  say "Updating $SRC"; git -C "$SRC" fetch -q --tags origin && git -C "$SRC" checkout -q "$REF" && git -C "$SRC" pull -q --ff-only origin "$REF" 2>/dev/null || true
else
  say "Cloning into $SRC"; git clone -q "$REPO" "$SRC" && git -C "$SRC" checkout -q "$REF"
fi
bash "$SRC/setup.sh"
# Hooks only matter in Claude Code. Wire them when Claude Code is on this machine; the hook
# installer backs settings.json up first and `./setup.sh --uninstall` removes them again.
if [ -z "${EAOS_NO_HOOKS:-}" ] && [ -d "${CLAUDE_HOME:-$HOME/.claude}" ] && command -v claude >/dev/null 2>&1; then
  say "Claude Code found: wiring hooks (skip with EAOS_NO_HOOKS=1)"; bash "$SRC/runtime/install-eaos-hooks.sh" >/dev/null
fi
bash "$SRC/runtime/eaos-doctor.sh" | tail -3
say "Done. Open any repository and type:  /agentic-os <your task>   (Codex: \$agentic-os <your task>)"
say "Update: re-run this command.   Uninstall: bash $SRC/setup.sh --uninstall"
