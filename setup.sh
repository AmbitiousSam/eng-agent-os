#!/usr/bin/env bash
# EAOS v4 bootstrap — install the Engineering Agentic OS on any machine, and clean up
# what earlier versions installed. Idempotent; safe to re-run. Requires: Claude Code
# (~/.claude), python3, git. Never wires hooks (opt in: scripts/install-eaos-hooks.sh).
set -euo pipefail

EAOS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="${CLAUDE_HOME:-$HOME/.claude}"
AGENTS_DIR="$CLAUDE_DIR/agents"
SKILLS_DIR="$CLAUDE_DIR/skills"
COMMANDS_DIR="$CLAUDE_DIR/commands"
CONFIG_DIR="$CLAUDE_DIR/eaos"

say() { printf "\033[1;36m[eaos]\033[0m %s\n" "$*"; }

# Install one file. An existing, differing destination is backed up once to <dest>.bak.
install_file() {
  local src="$1" dst="$2"
  if [ -e "$dst" ]; then
    cmp -s "$src" "$dst" && return 0
    cp -f "$dst" "$dst.bak"
    say "  backed up modified file -> $dst.bak"
  fi
  cp -f "$src" "$dst"
}

mkdir -p "$AGENTS_DIR" "$COMMANDS_DIR" "$CONFIG_DIR/templates" "$CONFIG_DIR/checklists" \
         "$CONFIG_DIR/adapters" "$CONFIG_DIR/bin"

# ---------------------------------------------------------------------------------------
# 1) CLEANUP of earlier EAOS versions (v1-v3). Everything removed here was installed by an
#    earlier setup.sh and is superseded by v4; nothing project-local (.eaos/) is touched.
# ---------------------------------------------------------------------------------------
removed=0
rm_if() { for p in "$@"; do if [ -e "$p" ]; then rm -rf "$p"; removed=$((removed + 1)); fi; done; }

# agency-agents persona library (280 files, every one listed on every turn of every session)
for f in "$AGENTS_DIR"/agency-*.md "$AGENTS_DIR"/agency-*.md.bak; do rm_if "$f"; done
# the 17 v3 personas
for a in architect ceo-strategist code-reviewer codebase-analyst developer devops-engineer \
         finance-analyst growth-lead incident-commander platform-engineer product-manager \
         qa-engineer requirements-analyst security-reviewer sre-observability tech-writer verifier; do
  rm_if "$AGENTS_DIR/$a.md" "$AGENTS_DIR/$a.md.bak"
done
# v1-v3 commands
for c in agent-os.md incident.md triage.md; do rm_if "$COMMANDS_DIR/$c" "$COMMANDS_DIR/$c.bak"; done
# v3 orchestration files and stores
rm_if "$CONFIG_DIR/protocol.md" "$CONFIG_DIR/loop.md" "$CONFIG_DIR/orchestrator.md" \
      "$CONFIG_DIR/playbooks" "$CONFIG_DIR/memory-seed" "$CONFIG_DIR/skill-backups" \
      "$CONFIG_DIR/protocol.md.bak" "$CONFIG_DIR/loop.md.bak" "$CONFIG_DIR/orchestrator.md.bak"
# the 11 v3 skills (role knowledge now lives in checklists/)
for s in bug-triage codebase-map deployment-guide design-review fitness-functions \
         incident-response memory-consolidation requirement-intake sensor-feedback test-plan triage; do
  rm_if "$SKILLS_DIR/$s"
done
[ "$removed" -gt 0 ] && say "Cleaned up $removed item(s) from earlier EAOS versions."

# ---------------------------------------------------------------------------------------
# 2) INSTALL v4
# ---------------------------------------------------------------------------------------
say "Installing /agentic-os -> $COMMANDS_DIR"
install_file "$EAOS_DIR/commands/agentic-os.md" "$COMMANDS_DIR/agentic-os.md"

# Boundary agent definitions. Under models.mode: inherit any `model:` frontmatter line is
# stripped so a spawn always runs on the session's model.
MODELS_MODE="$(awk '/^models:/{f=1} f && /^  mode:/{print $2; exit}' "$EAOS_DIR/orchestrator/routing.yaml")"
MODELS_MODE="${MODELS_MODE:-inherit}"
say "Installing boundary agents -> $AGENTS_DIR (models.mode=$MODELS_MODE)"
STRIP_TMP="$(mktemp -d)"
for f in "$EAOS_DIR"/agents/eaos-*.md; do
  [ -e "$f" ] || continue
  base="$(basename "$f")"
  if [ "$MODELS_MODE" = "inherit" ]; then
    awk 'NR==1 && /^---/ {fm=1; print; next} fm && /^---/ {fm=0} fm && /^model:/ {next} {print}' \
      "$f" > "$STRIP_TMP/$base"
    install_file "$STRIP_TMP/$base" "$AGENTS_DIR/$base"
  else
    install_file "$f" "$AGENTS_DIR/$base"
  fi
done
rm -rf "$STRIP_TMP"

say "Installing config, checklists, templates, adapters -> $CONFIG_DIR"
install_file "$EAOS_DIR/orchestrator/routing.yaml" "$CONFIG_DIR/routing.yaml"
for f in "$EAOS_DIR"/checklists/*.md; do [ -e "$f" ] && install_file "$f" "$CONFIG_DIR/checklists/$(basename "$f")"; done
for f in "$EAOS_DIR"/templates/*.md;  do [ -e "$f" ] && install_file "$f" "$CONFIG_DIR/templates/$(basename "$f")"; done
install_file "$EAOS_DIR/adapters/solo-mode.md" "$CONFIG_DIR/adapters/solo-mode.md"
# stale checklists/templates from a previous v4 install that no longer exist upstream
for f in "$CONFIG_DIR"/checklists/*.md; do [ -e "$f" ] && [ ! -e "$EAOS_DIR/checklists/$(basename "$f")" ] && rm -f "$f"; done

say "Installing eaos runtime CLI + hook accelerator -> $CONFIG_DIR/bin"
install_file "$EAOS_DIR/scripts/eaos" "$CONFIG_DIR/bin/eaos"
install_file "$EAOS_DIR/scripts/eaos-hook.sh" "$CONFIG_DIR/bin/eaos-hook.sh"
chmod +x "$CONFIG_DIR/bin/eaos" "$CONFIG_DIR/bin/eaos-hook.sh"

# ---------------------------------------------------------------------------------------
# 3) VERIFY
# ---------------------------------------------------------------------------------------
say ""
say "Verifying install:"
okc=0; bad=0
chk() { if [ -e "$1" ]; then okc=$((okc + 1)); else printf "  \033[0;31m✗ MISSING\033[0m %s\n" "$1"; bad=$((bad + 1)); fi; }
chk "$COMMANDS_DIR/agentic-os.md"
for a in eaos-builder eaos-reader eaos-checker; do chk "$AGENTS_DIR/$a.md"; done
chk "$CONFIG_DIR/routing.yaml"; chk "$CONFIG_DIR/bin/eaos"; chk "$CONFIG_DIR/bin/eaos-hook.sh"
for c in "$EAOS_DIR"/checklists/*.md; do chk "$CONFIG_DIR/checklists/$(basename "$c")"; done
leftover="$(find "$AGENTS_DIR" -maxdepth 1 -name 'agency-*.md' 2>/dev/null | wc -l | tr -d ' ')"
printf "  \033[0;32m✓\033[0m %s files present; legacy agency-agents remaining: %s\n" "$okc" "$leftover"
[ "$bad" -eq 0 ] || { say "Install incomplete."; exit 1; }
say ""
say "Installed. Runtime state is PROJECT-LOCAL (./.eaos/ in the project you run it in)."
say "Hooks are opt-in:   ./scripts/install-eaos-hooks.sh"
say "Usage in Claude Code (restart it after first install):   /agentic-os <task>"
say "Follow-ups are plain messages. Fresh context on an existing task: eaos status --packet"
