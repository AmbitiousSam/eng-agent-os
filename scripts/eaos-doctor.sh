#!/usr/bin/env bash
# eaos-doctor.sh — verify EAOS v4 is installed and the current project is ready.
# Exit 0 = healthy, 1 = problems. Safe to run anytime.
set -uo pipefail

CLAUDE_DIR="${CLAUDE_HOME:-$HOME/.claude}"
EAOS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail=0
pass() { printf "  \033[0;32m✓\033[0m %s\n" "$*"; }
bad()  { printf "  \033[0;31m✗\033[0m %s\n" "$*"; fail=1; }
note() { printf "  \033[0;33m!\033[0m %s\n" "$*"; }

echo "EAOS doctor (v4)"
echo "========================================"

echo "Installation (~/.claude):"
for f in commands/agentic-os.md eaos/routing.yaml eaos/bin/eaos eaos/bin/eaos-hook.sh \
         eaos/adapters/solo-mode.md agents/eaos-builder.md agents/eaos-reader.md agents/eaos-checker.md; do
  [ -e "$CLAUDE_DIR/$f" ] && pass "~/.claude/$f" || bad "~/.claude/$f missing — run ./setup.sh"
done
if python3 "$CLAUDE_DIR/eaos/bin/eaos" --help >/dev/null 2>&1; then pass "eaos CLI runs"; else bad "eaos CLI present but failed to run — run ./setup.sh"; fi
if python3 "$CLAUDE_DIR/eaos/bin/eaos" --help 2>/dev/null | grep -q "board"; then pass "eaos CLI is v4 (board/unit/check verbs)"; else bad "eaos CLI predates v4 — run ./setup.sh"; fi

# checklists derived from the repo so this list never drifts
need_cl="$(cd "$EAOS_DIR/checklists" 2>/dev/null && ls *.md 2>/dev/null | sed 's/\.md$//')"
if [ -z "$need_cl" ]; then bad "could not derive the checklist list from $EAOS_DIR/checklists — run the doctor from a full checkout"; else
  miss=""; n=0
  for c in $need_cl; do n=$((n + 1)); [ -e "$CLAUDE_DIR/eaos/checklists/$c.md" ] || miss="$miss $c"; done
  [ -z "$miss" ] && pass "all $n checklists installed" || bad "missing checklists:$miss — run ./setup.sh"
fi

# front door budget and model pin
if [ -e "$CLAUDE_DIR/commands/agentic-os.md" ]; then
  est=$(( $(wc -c < "$CLAUDE_DIR/commands/agentic-os.md") / 4 ))
  [ "$est" -le 2000 ] && pass "front door ~$est tokens (budget 2000)" || bad "front door ~$est tokens exceeds the 2000-token bootstrap budget"
  grep -q "^model:" "$CLAUDE_DIR/commands/agentic-os.md" && bad "front door pins a model — run ./setup.sh" || pass "front door pins no model"
fi

# models.mode=inherit: installed boundary agents must not pin a model
mm="$(awk '/^models:/{f=1} f && /^  mode:/{print $2; exit}' "$EAOS_DIR/orchestrator/routing.yaml" 2>/dev/null)"
if [ "${mm:-inherit}" = "inherit" ]; then
  pinned=""
  for a in eaos-builder eaos-reader eaos-checker; do grep -q "^model:" "$CLAUDE_DIR/agents/$a.md" 2>/dev/null && pinned="$pinned $a"; done
  [ -z "$pinned" ] && pass "models.mode=inherit: no agent pins a model" || bad "agents pin a model under inherit:$pinned — run ./setup.sh"
fi

echo "Leftovers from earlier versions:"
left=0
n_agency="$(ls "$CLAUDE_DIR"/agents/agency-*.md 2>/dev/null | wc -l | tr -d ' ')"
[ "$n_agency" = 0 ] && pass "no agency-agents personas installed" || { bad "$n_agency agency-agents personas still installed (listed on every turn) — run ./setup.sh"; left=1; }
for a in architect developer verifier requirements-analyst security-reviewer; do
  [ -e "$CLAUDE_DIR/agents/$a.md" ] && { bad "v3 persona still installed: agents/$a.md — run ./setup.sh"; left=1; }
done
for f in eaos/protocol.md eaos/loop.md eaos/orchestrator.md eaos/playbooks; do
  [ -e "$CLAUDE_DIR/$f" ] && { bad "v3 file still installed: ~/.claude/$f — run ./setup.sh"; left=1; }
done
[ "$left" = 0 ] && pass "no v3 orchestration files remain"

echo "Hook accelerators (M-007, optional):"
if [ -f "$CLAUDE_DIR/settings.json" ] && grep -q "eaos-hook.sh" "$CLAUDE_DIR/settings.json" 2>/dev/null; then
  pass "hooks wired into settings.json — spawn/audit/context run without model cooperation"
  grep -q "eaos-hook.sh.* posttool" "$CLAUDE_DIR/settings.json" 2>/dev/null || \
    note "no PostToolUse entry — re-run ./scripts/install-eaos-hooks.sh so each session binds to ITS task"
else
  note "hooks not wired (optional) — opt in with: ./scripts/install-eaos-hooks.sh"
fi

echo "Project readiness (cwd):"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  pass "inside a git repo ($(git rev-parse --show-toplevel 2>/dev/null)) — snapshots and check evidence work"
  if git check-ignore .eaos >/dev/null 2>&1; then pass ".eaos/ is gitignored"; else
    note ".eaos/ not gitignored — add '.eaos/' to .gitignore so runtime state isn't committed"; fi
else
  note "not a git repo — snapshots fall back to hashing the tree; check evidence still binds"
fi

echo "Repo self-check:"
if command -v python3 >/dev/null 2>&1; then
  if python3 "$EAOS_DIR/scripts/validate-eaos.py" >/dev/null 2>&1; then pass "validate-eaos.py: repo internally consistent"; else
    bad "validate-eaos.py reported errors — run: python3 scripts/validate-eaos.py"; fi
else
  note "python3 not found — skipping structural validation"
fi

echo "========================================"
if [ "$fail" = 0 ]; then echo -e "\033[0;32mHealthy.\033[0m  Try:  /agentic-os <task>"; else
  echo -e "\033[0;31mIssues found.\033[0m  Fix the ✗ items above (usually: ./setup.sh)."; fi
exit $fail
