#!/usr/bin/env bash
# EAOS v4 bootstrap — install the Engineering Agentic OS on any machine, and clean up
# what earlier versions installed. Idempotent; safe to re-run. Requires: Claude Code
# (~/.claude), python3, git. Never wires hooks (opt in: runtime/install-eaos-hooks.sh).
# `./setup.sh --dry-run` prints the cleanup plan and changes nothing.
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
    # Files under eaos/ (runtime, checklists, templates, adapters) are EAOS-owned and replaced on
    # every update: backing each one up just litters the folder the agent reads from. The front
    # door and the agent definitions are the places a user might have edited, so those are kept.
    case "$dst" in
      "$CONFIG_DIR"/*) ;;
      *) cp -f "$dst" "$dst.bak"; say "  backed up modified file -> $dst.bak" ;;
    esac
  fi
  cp -f "$src" "$dst"
}

# ---------------------------------------------------------------------------------------
# 1) CLEANUP of earlier EAOS versions (v1-v3), manifest-based (v4 review 1, finding 6).
#    A file is REMOVED only if its content hash appears in runtime/legacy-manifest.sha256
#    (the exact bytes an earlier setup.sh installed). A file at a legacy path whose content
#    is not listed — customised, or never ours — is QUARANTINED (moved, with a manifest of
#    what moved where), never deleted. `setup.sh --dry-run` prints the plan and changes
#    nothing. Project-local .eaos/ directories are never touched.
# ---------------------------------------------------------------------------------------
MANIFEST="$EAOS_DIR/eaos/runtime/legacy-manifest.sha256"
DRY_RUN=0
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1
SKILL_DIR="${AGENTS_SKILLS_HOME:-$HOME/.agents/skills}/agentic-os"

QUAR="$CONFIG_DIR/quarantine/$(date +%Y%m%d-%H%M%S)"
removed=0; quarantined=0

sha_of() { shasum -a 256 "$1" 2>/dev/null | cut -d' ' -f1; }
listed() {  # listed <sha> <relative target path>
  [ -f "$MANIFEST" ] && grep -q "^$1  $2\$" "$MANIFEST"
}
dispose() {  # dispose <absolute path> <relative target path used in the manifest>
  local abs="$1" rel="$2"
  [ -e "$abs" ] || return 0
  if [ -f "$abs" ] && listed "$(sha_of "$abs")" "$rel"; then
    if [ "$DRY_RUN" = 1 ]; then echo "  would remove   $abs (unmodified EAOS file)"; else rm -f "$abs"; fi
    removed=$((removed + 1))
  elif [ -f "$abs" ] && [ "${abs%.bak}" != "$abs" ] && listed "$(sha_of "$abs")" "${rel%.bak}"; then
    # a .bak created by an earlier install_file whose content is an EAOS original
    if [ "$DRY_RUN" = 1 ]; then echo "  would remove   $abs (EAOS backup)"; else rm -f "$abs"; fi
    removed=$((removed + 1))
  else
    if [ "$DRY_RUN" = 1 ]; then echo "  would quarantine $abs (content not in manifest: customised or not ours)"; else
      mkdir -p "$QUAR/$(dirname "$rel")"; mv "$abs" "$QUAR/$rel"; echo "$rel" >> "$QUAR/MANIFEST.txt"; fi
    quarantined=$((quarantined + 1))
  fi
}
dispose_dir() {  # dispose_dir <abs dir> <rel dir>: remove only if EVERY file inside is listed
  local abs="$1" rel="$2" f all=1
  [ -d "$abs" ] || return 0
  while IFS= read -r -d '' f; do
    listed "$(sha_of "$f")" "$rel/${f#"$abs"/}" || { all=0; break; }
  done < <(find "$abs" -type f -print0)
  if [ "$all" = 1 ]; then
    if [ "$DRY_RUN" = 1 ]; then echo "  would remove   $abs/ (all files unmodified EAOS)"; else rm -rf "$abs"; fi
    removed=$((removed + 1))
  else
    if [ "$DRY_RUN" = 1 ]; then echo "  would quarantine $abs/ (contains files not in manifest)"; else
      mkdir -p "$QUAR/$(dirname "$rel")"; mv "$abs" "$QUAR/$rel"; echo "$rel/" >> "$QUAR/MANIFEST.txt"; fi
    quarantined=$((quarantined + 1))
  fi
}

[ "$DRY_RUN" = 1 ] && say "DRY RUN — cleanup plan for earlier EAOS versions:"
for f in "$AGENTS_DIR"/agency-*.md "$AGENTS_DIR"/agency-*.md.bak; do [ -e "$f" ] && dispose "$f" "agents/$(basename "$f")"; done
for a in architect ceo-strategist code-reviewer codebase-analyst developer devops-engineer \
         finance-analyst growth-lead incident-commander platform-engineer product-manager \
         qa-engineer requirements-analyst security-reviewer sre-observability tech-writer verifier; do
  dispose "$AGENTS_DIR/$a.md" "agents/$a.md"; dispose "$AGENTS_DIR/$a.md.bak" "agents/$a.md.bak"
done
for c in agent-os.md incident.md triage.md; do dispose "$COMMANDS_DIR/$c" "commands/$c"; dispose "$COMMANDS_DIR/$c.bak" "commands/$c.bak"; done
for f in protocol.md loop.md orchestrator.md; do dispose "$CONFIG_DIR/$f" "eaos/$f"; dispose "$CONFIG_DIR/$f.bak" "eaos/$f.bak"; done
dispose_dir "$CONFIG_DIR/playbooks" "eaos/playbooks"
dispose_dir "$CONFIG_DIR/memory-seed" "eaos/memory-seed"
# skill-backups only ever held copies of our own skills; quarantine rather than judge
[ -d "$CONFIG_DIR/skill-backups" ] && dispose_dir "$CONFIG_DIR/skill-backups" "eaos/skill-backups"
for s in bug-triage codebase-map deployment-guide design-review fitness-functions \
         incident-response memory-consolidation requirement-intake sensor-feedback test-plan triage; do
  dispose_dir "$SKILLS_DIR/$s" "skills/$s"
done
if [ "$DRY_RUN" = 1 ]; then
  say "Dry run: $removed removal(s), $quarantined quarantine(s). Nothing changed."; exit 0
fi
[ "$removed" -gt 0 ] && say "Removed $removed unmodified EAOS item(s) from earlier versions."
[ "$quarantined" -gt 0 ] && say "Quarantined $quarantined item(s) (not verifiably ours) -> $QUAR (see MANIFEST.txt)"

# ./setup.sh --uninstall : remove everything EAOS put on this machine, every version. The legacy
# cleanup above has already run (same manifest rule: byte-identical files deleted, anything
# customised quarantined). Project-local .eaos/ folders, the scenario store and the quarantine
# folder are yours and are left alone.
if [ "${1:-}" = "--uninstall" ]; then
  bash "$EAOS_DIR/eaos/runtime/install-eaos-hooks.sh" --uninstall >/dev/null 2>&1 || true
  rm -f "$COMMANDS_DIR/agentic-os.md" "$COMMANDS_DIR/agentic-os.md.bak" "$AGENTS_DIR"/eaos-builder.md "$AGENTS_DIR"/eaos-reader.md "$AGENTS_DIR"/eaos-checker.md "$AGENTS_DIR"/eaos-*.md.bak
  rm -rf "$CONFIG_DIR/bin" "$CONFIG_DIR/checklists" "$CONFIG_DIR/templates" "$CONFIG_DIR/adapters" "$CONFIG_DIR/routing.yaml" "$SKILL_DIR"
  say "Uninstalled. Kept: project .eaos/ folders, $CONFIG_DIR/scenarios, $CONFIG_DIR/quarantine."
  exit 0
fi

# ---------------------------------------------------------------------------------------
# 2) INSTALL v4  (directories are created only here — a --dry-run has exited above)
# ---------------------------------------------------------------------------------------
mkdir -p "$AGENTS_DIR" "$COMMANDS_DIR" "$CONFIG_DIR/templates" "$CONFIG_DIR/checklists" \
         "$CONFIG_DIR/adapters" "$CONFIG_DIR/bin"
say "Installing /agentic-os -> $COMMANDS_DIR"
install_file "$EAOS_DIR/eaos/agentic-os.md" "$COMMANDS_DIR/agentic-os.md"

# Boundary agent definitions. Under models.mode: inherit any `model:` frontmatter line is
# stripped so a spawn always runs on the session's model.
MODELS_MODE="$(awk '/^models:/{f=1} f && /^  mode:/{print $2; exit}' "$EAOS_DIR/eaos/runtime/routing.yaml")"
MODELS_MODE="${MODELS_MODE:-inherit}"
say "Installing boundary agents -> $AGENTS_DIR (models.mode=$MODELS_MODE)"
STRIP_TMP="$(mktemp -d)"
for f in "$EAOS_DIR"/eaos/agents/eaos-*.md; do
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
install_file "$EAOS_DIR/eaos/runtime/routing.yaml" "$CONFIG_DIR/routing.yaml"
for f in "$EAOS_DIR"/eaos/checklists/*.md; do [ -e "$f" ] && install_file "$f" "$CONFIG_DIR/checklists/$(basename "$f")"; done
for f in "$EAOS_DIR"/eaos/templates/*.md;  do [ -e "$f" ] && install_file "$f" "$CONFIG_DIR/templates/$(basename "$f")"; done
install_file "$EAOS_DIR/eaos/adapters/solo-mode.md" "$CONFIG_DIR/adapters/solo-mode.md"
install_file "$EAOS_DIR/eaos/adapters/AGENTS.md" "$CONFIG_DIR/adapters/AGENTS.md"
# litter from earlier installs' per-file backups inside EAOS-owned folders
find "$CONFIG_DIR/checklists" "$CONFIG_DIR/templates" "$CONFIG_DIR/adapters" "$CONFIG_DIR/bin" -maxdepth 1 -name '*.bak' -delete 2>/dev/null || true
rm -f "$CONFIG_DIR/routing.yaml.bak"
# stale checklists/templates from a previous v4 install that no longer exist upstream
for f in "$CONFIG_DIR"/checklists/*.md; do [ -e "$f" ] && [ ! -e "$EAOS_DIR/eaos/checklists/$(basename "$f")" ] && rm -f "$f"; done

# Global skill for Cursor and Codex (both load ~/.agents/skills; Cursor also shows it as
# /agentic-os). GENERATED from the one front door so there is never a second copy to drift:
# frontmatter swapped, host deltas prepended, $ARGUMENTS replaced (skills get no substitution).
say "Installing global skill for Cursor / Codex -> $SKILL_DIR"
mkdir -p "$SKILL_DIR"
SKILL_TMP="$(mktemp)"
{
  cat "$EAOS_DIR/eaos/adapters/skill-head.md"
  awk 'NR==1 && /^---/ {fm=1; next} fm && /^---/ {fm=0; next} !fm {print}' "$EAOS_DIR/eaos/agentic-os.md" \
    | sed 's/\*\*\$ARGUMENTS\*\*/**the task the user gave when invoking this skill**/'
} > "$SKILL_TMP"
install_file "$SKILL_TMP" "$SKILL_DIR/SKILL.md"; rm -f "$SKILL_TMP"

say "Installing eaos runtime CLI + hook accelerator -> $CONFIG_DIR/bin"
install_file "$EAOS_DIR/eaos/runtime/eaos" "$CONFIG_DIR/bin/eaos"
install_file "$EAOS_DIR/eaos/runtime/eaos-hook.sh" "$CONFIG_DIR/bin/eaos-hook.sh"
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
chk "$CONFIG_DIR/routing.yaml"; chk "$CONFIG_DIR/bin/eaos"; chk "$CONFIG_DIR/bin/eaos-hook.sh"; chk "$SKILL_DIR/SKILL.md"
for c in "$EAOS_DIR"/eaos/checklists/*.md; do chk "$CONFIG_DIR/checklists/$(basename "$c")"; done
leftover="$(find "$AGENTS_DIR" -maxdepth 1 -name 'agency-*.md' 2>/dev/null | wc -l | tr -d ' ')"
printf "  \033[0;32m✓\033[0m %s files present; legacy agency-agents remaining: %s\n" "$okc" "$leftover"
[ "$bad" -eq 0 ] || { say "Install incomplete."; exit 1; }
say ""
say "Installed. Runtime state is PROJECT-LOCAL (./.eaos/ in the project you run it in)."
say "Hooks are opt-in:   ./runtime/install-eaos-hooks.sh"
say "Usage in Claude Code (restart it after first install):   /agentic-os <task>"
say "Usage in Cursor:        /agentic-os <task>      (global skill, any repo)"
say "Usage in Codex:         \$agentic-os <task>     (global skill, any repo)"
say "Follow-ups are plain messages. Fresh context on an existing task: eaos status --packet"
