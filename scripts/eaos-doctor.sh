#!/usr/bin/env bash
# eaos-doctor.sh — verify EAOS is installed and the current project is ready to run /agentic-os.
# Exit 0 = healthy, 1 = problems. Safe to run anytime.
set -uo pipefail

CLAUDE_DIR="${CLAUDE_HOME:-$HOME/.claude}"
EAOS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail=0
pass() { printf "  \033[0;32m✓\033[0m %s\n" "$*"; }
bad()  { printf "  \033[0;31m✗\033[0m %s\n" "$*"; fail=1; }
note() { printf "  \033[0;33m!\033[0m %s\n" "$*"; }

echo "EAOS doctor"
echo "========================================"

echo "Installation (~/.claude):"
[ -d "$CLAUDE_DIR" ] && pass "$CLAUDE_DIR exists" || bad "$CLAUDE_DIR missing — run ./setup.sh"
for f in commands/agentic-os.md commands/agent-os.md eaos/routing.yaml eaos/protocol.md eaos/loop.md; do
  [ -e "$CLAUDE_DIR/$f" ] && pass "~/.claude/$f" || bad "~/.claude/$f missing — run ./setup.sh"
done
# required agents installed
need_agents="orchestrator requirements codebase-analyst architect developer code-reviewer qa-engineer security-reviewer devops-engineer platform-engineer sre-observability tech-writer"
miss=""
for a in $need_agents; do [ -e "$CLAUDE_DIR/agents/$a.md" ] || miss="$miss $a"; done
[ -z "$miss" ] && pass "all 12 EAOS agents installed" || bad "missing agents:$miss — run ./setup.sh"
# skills
sk_ok=1; for s in requirement-intake test-plan deployment-guide codebase-map bug-triage; do
  [ -e "$CLAUDE_DIR/skills/$s/SKILL.md" ] || sk_ok=0; done
[ "$sk_ok" = 1 ] && pass "EAOS skills installed" || bad "some skills missing — run ./setup.sh"
# agency-agents (optional)
if ls "$CLAUDE_DIR"/agents/agency-*.md >/dev/null 2>&1; then
  pass "agency-agents personas present (optional delegate pool)"
else
  note "agency-agents not installed — EAOS works standalone; clone failed or skipped (optional)"
fi

echo "Project readiness (cwd):"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  pass "inside a git repo ($(git rev-parse --show-toplevel 2>/dev/null))"
  if git check-ignore .eaos >/dev/null 2>&1; then pass ".eaos/ is gitignored"; else
    note ".eaos/ not gitignored — add '.eaos/' to .gitignore so runtime state isn't committed"; fi
else
  note "not a git repo — GROUND can still map, but git history/blame won't be available"
fi

echo "Repo self-check:"
if command -v python3 >/dev/null 2>&1; then
  if python3 "$EAOS_DIR/scripts/validate-eaos.py" >/dev/null 2>&1; then
    pass "validate-eaos.py: repo internally consistent"
  else
    bad "validate-eaos.py reported errors — run: python3 scripts/validate-eaos.py"
  fi
else
  note "python3 not found — skipping structural validation"
fi

echo "========================================"
if [ "$fail" = 0 ]; then echo -e "\033[0;32mHealthy.\033[0m  Try:  /agentic-os <task>   (alias: /agent-os)"; else
  echo -e "\033[0;31mIssues found.\033[0m  Fix the ✗ items above (usually: ./setup.sh)."; fi
exit $fail
