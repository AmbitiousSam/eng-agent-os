#!/usr/bin/env bash
# e0_env.sh — an ISOLATED v3 installation for experiment E0.
#
# v4 review 2, finding 3: the tag preserves source, not environment, and v3's installed
# command names literal global paths (~/.claude/eaos/routing.yaml, ~/.claude/eaos/bin/eaos)
# that now point at v4. A separate config directory alone does not fix that. So this
# script: (1) installs v3 from a worktree at e0-baseline into a separate directory,
# (2) REWRITES every literal `~/.claude/` in the installed command to that directory and
# records the sha256 of the adapted command (the only baseline adaptation, hashed so it is
# auditable), (3) verifies no global path remains and the isolated CLI runs, and (4) prints
# the exact environment every E0 session must start with. v3's hook script resolves the
# CLI via $CLAUDE_HOME, so that variable must be set for the session too.
#
# Usage: scripts/e0_env.sh [config-dir]     (default ~/.claude-e0)
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CFG="${1:-$HOME/.claude-e0}"
WT="$REPO/.e0-worktree"
[ -d "$WT" ] || git -C "$REPO" worktree add -q "$WT" e0-baseline
[ "$(git -C "$WT" describe --tags --exact-match 2>/dev/null)" = "e0-baseline" ] || { echo "worktree is not at e0-baseline" >&2; exit 1; }
mkdir -p "$CFG"
CLAUDE_HOME="$CFG" bash "$WT/setup.sh" >/dev/null
CLAUDE_HOME="$CFG" bash "$WT/scripts/install-eaos-hooks.sh" >/dev/null

CMD="$CFG/commands/agentic-os.md"
# rewrite literal global paths in the installed command only (never the worktree)
python3 - "$CMD" "$CFG" <<'PY'
import sys, re
p, cfg = sys.argv[1], sys.argv[2]
s = open(p, encoding="utf-8").read()
s2 = s.replace("~/.claude/", cfg.rstrip("/") + "/")
open(p, "w", encoding="utf-8").write(s2)
print(f"rewrote {s.count('~/.claude/')} literal path(s) in the installed command")
PY
# the hook script must find the isolated CLI without relying on the session env alone
sed -i '' "s|\${CLAUDE_HOME:-\$HOME/.claude}|\${CLAUDE_HOME:-$CFG}|" "$CFG/eaos/bin/eaos-hook.sh"

echo "== verification =="
if grep -q '~/.claude/' "$CMD"; then echo "FAIL: global path still present in $CMD" >&2; exit 1; fi
grep -q "$CFG/eaos/bin/eaos" "$CMD" && echo "command points at $CFG/eaos/bin/eaos"
python3 "$CFG/eaos/bin/eaos" --help >/dev/null && echo "isolated CLI runs"
python3 "$CFG/eaos/bin/eaos" --help | grep -q " board" && { echo "FAIL: isolated CLI is v4, not v3" >&2; exit 1; } || echo "isolated CLI is v3 (no board verb)"
grep -q "CLAUDE_HOME:-$CFG" "$CFG/eaos/bin/eaos-hook.sh" && echo "hook defaults to the isolated CLI"
echo "adapted command sha256: $(shasum -a 256 "$CMD" | cut -d' ' -f1)"
echo "worktree commit:        $(git -C "$WT" rev-parse HEAD)"
echo
echo "Start EVERY E0 session with:"
echo "    CLAUDE_CONFIG_DIR=$CFG CLAUDE_HOME=$CFG claude"
echo "Confirm on this machine, before run 1, that Claude Code loads $CFG/commands (type /agentic-os"
echo "and check the expansion names $CFG). Record 'claude --version' and the two hashes above in the run log."
echo "Any transcript that invokes ~/.claude/eaos/bin/eaos (the global v4) invalidates that run."
