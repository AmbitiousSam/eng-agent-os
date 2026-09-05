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
for f in commands/agentic-os.md \
         eaos/routing.yaml eaos/protocol.md eaos/loop.md eaos/orchestrator.md \
         eaos/memory-seed/index.md eaos/adapters/solo-mode.md eaos/bin/eaos; do
  [ -e "$CLAUDE_DIR/$f" ] && pass "~/.claude/$f" || bad "~/.claude/$f missing — run ./setup.sh"
done
# eaos runtime CLI: functional smoke check (mechanical bookkeeping degrades to prompt-only
# enforcement without it — see commands/agentic-os.md > Runtime CLI).
if [ -e "$CLAUDE_DIR/eaos/bin/eaos" ]; then
  if python3 "$CLAUDE_DIR/eaos/bin/eaos" --help >/dev/null 2>&1; then
    pass "eaos CLI runs (~/.claude/eaos/bin/eaos --help)"
  else
    bad "eaos CLI present but failed to run — run ./setup.sh"
  fi
fi
# required agents installed
# orchestrator is NOT a spawnable agent — it's the role /agentic-os adopts on the main
# session; its spec lives at ~/.claude/eaos/orchestrator.md (checked above).
# Derived from the repo's agents/*.md basenames (excluding README) so this list can never
# drift out of sync with setup.sh's own verify step — both compute the same set, live.
need_agents="$(cd "$EAOS_DIR/agents" 2>/dev/null && ls *.md 2>/dev/null | sed 's/\.md$//' | grep -v '^README$')"
if [ -z "$need_agents" ]; then
  bad "could not derive the agent list from $EAOS_DIR/agents — run the doctor from a full eng-agent-os checkout"
else
  miss=""
  count=0
  for a in $need_agents; do
    count=$((count + 1))
    [ -e "$CLAUDE_DIR/agents/$a.md" ] || miss="$miss $a"
  done
  [ -z "$miss" ] && pass "all $count EAOS worker personas installed" || bad "missing agents:$miss — run ./setup.sh"
fi
# skills
# Derived from the repo's skills/ dirs so this list can never drift (same pattern as agents).
need_skills="$(cd "$EAOS_DIR/skills" 2>/dev/null && ls -d */ 2>/dev/null | sed 's:/$::')"
if [ -z "$need_skills" ]; then
  bad "could not derive the skill list from $EAOS_DIR/skills — run the doctor from a full eng-agent-os checkout"
else
  sk_ok=1; for s in $need_skills; do
    [ -e "$CLAUDE_DIR/skills/$s/SKILL.md" ] || sk_ok=0; done
  [ "$sk_ok" = 1 ] && pass "EAOS skills installed" || bad "some skills missing — run ./setup.sh"
fi
# Optional ecosystem integrations (never failures — EAOS runs bare)
echo "Optional integrations:"
if ls "$CLAUDE_DIR"/agents/agency-*.md >/dev/null 2>&1; then
  pass "agency-agents personas (delegate pool)"
else
  note "agency-agents not installed (optional) — EAOS works standalone"
fi
if command -v codegraph >/dev/null 2>&1; then
  pass "codegraph CLI on PATH (GROUND uses it where .codegraph/ exists)"
else
  note "codegraph not installed (optional) — GROUND falls back to grep. Install (any OS, needs node): npx @colbymchenry/codegraph"
fi
if command -v rtk >/dev/null 2>&1; then
  pass "rtk on PATH (command-output compression; run 'rtk init -g' once if not hooked)"
else
  case "$(uname -s 2>/dev/null)" in
    MINGW*|MSYS*|CYGWIN*) note "rtk not installed (optional) — Windows: use WSL for full hook support, or the release zip (filters only): github.com/rtk-ai/rtk/releases" ;;
    *) note "rtk not installed (optional) — curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh   (then: rtk init -g)" ;;
  esac
fi
if ls "$CLAUDE_DIR"/plugins 2>/dev/null | grep -qi ponytail || [ -d "$HOME/.config/ponytail" ]; then
  pass "ponytail detected (minimal-code discipline reinforced at host level)"
else
  note "ponytail not detected (optional) — the ladder is baked into the developer persona anyway. /plugin install ponytail@ponytail"
fi

echo "Hook accelerators (M-007, optional):"
if [ -e "$CLAUDE_DIR/eaos/bin/eaos-hook.sh" ]; then
  pass "eaos-hook.sh installed (~/.claude/eaos/bin/eaos-hook.sh)"
else
  note "eaos-hook.sh not installed — run ./setup.sh"
fi
if [ -f "$CLAUDE_DIR/settings.json" ] && grep -q "eaos-hook.sh" "$CLAUDE_DIR/settings.json" 2>/dev/null; then
  pass "hooks wired into settings.json — spawn/audit run without model cooperation"
else
  note "hooks not wired into settings.json (optional) — prompt+audit only until you" \
       "opt in with: ./scripts/install-eaos-hooks.sh"
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
if [ "$fail" = 0 ]; then echo -e "\033[0;32mHealthy.\033[0m  Try:  /agentic-os <task>"; else
  echo -e "\033[0;31mIssues found.\033[0m  Fix the ✗ items above (usually: ./setup.sh)."; fi
exit $fail
