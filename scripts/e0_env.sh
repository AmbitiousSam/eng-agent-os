#!/usr/bin/env bash
# e0_env.sh — an ISOLATED v3 installation for experiment E0 (v4 review 1: the baseline tag
# preserves the source, not the environment; the global ~/.claude now holds v4).
#
# Creates a git worktree of tag e0-baseline and installs it into a SEPARATE Claude Code
# config directory. Claude Code reads its config directory from $CLAUDE_CONFIG_DIR, so
# every E0 run is started as:
#     CLAUDE_CONFIG_DIR=~/.claude-e0 claude
# Verify that variable is honoured by your Claude Code version (`claude --help`) before the
# first run; if it is not, E0 cannot be run on a machine that also has v4 installed.
#
# Usage: scripts/e0_env.sh [config-dir]     (default ~/.claude-e0)
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CFG="${1:-$HOME/.claude-e0}"
WT="$REPO/.e0-worktree"
if [ ! -d "$WT" ]; then git -C "$REPO" worktree add -q "$WT" e0-baseline; fi
[ "$(git -C "$WT" describe --tags --exact-match 2>/dev/null)" = "e0-baseline" ] || { echo "worktree is not at e0-baseline" >&2; exit 1; }
mkdir -p "$CFG"
# v3's setup.sh installs the v3 command, 17 personas, skills, config and CLI into CLAUDE_HOME.
CLAUDE_HOME="$CFG" bash "$WT/setup.sh"
CLAUDE_HOME="$CFG" bash "$WT/scripts/install-eaos-hooks.sh"
echo
echo "E0 environment ready at $CFG (v3 @ e0-baseline, hooks wired)."
echo "Start every E0 session with:   CLAUDE_CONFIG_DIR=$CFG claude"
echo "Record in the run log: $(git -C "$WT" rev-parse HEAD) and the output of 'claude --version'."
