#!/usr/bin/env bash
# EAOS bootstrap — install the Engineering Agentic OS on any machine.
# Installs: agency-agents + EAOS personas, the /agentic-os slash command, and OS config.
# Idempotent: safe to re-run. Requires: git, and Claude Code (~/.claude).
set -euo pipefail

EAOS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="${CLAUDE_HOME:-$HOME/.claude}"
AGENTS_DIR="$CLAUDE_DIR/agents"
SKILLS_DIR="$CLAUDE_DIR/skills"
COMMANDS_DIR="$CLAUDE_DIR/commands"
CONFIG_DIR="$CLAUDE_DIR/eaos"                      # global OS config (read by the command)
VENDOR_DIR="$EAOS_DIR/vendor/agency-agents"
AGENCY_REPO="https://github.com/msitarzewski/agency-agents.git"
# Pinned so an upstream push can't silently change our installed agent set. Bump deliberately
# (re-run `git ls-remote "$AGENCY_REPO" HEAD` and update this value on purpose).
AGENCY_SHA="00fb28a4cf60a719363dce0de67fafc6301857ce"

say() { printf "\033[1;36m[eaos]\033[0m %s\n" "$*"; }

# Install a single file. If the destination already exists and differs from what we're about
# to install, back it up to <dest>.bak first (once) — never silently clobber a local edit.
install_file() {
  local src="$1" dst="$2"
  if [ -e "$dst" ]; then
    cmp -s "$src" "$dst" && return 0   # identical → nothing to do (no mtime churn on re-runs)
    cp -f "$dst" "$dst.bak"
    say "  backed up modified file -> $dst.bak"
  fi
  cp -f "$src" "$dst"
}

mkdir -p "$AGENTS_DIR" "$SKILLS_DIR" "$COMMANDS_DIR" \
         "$CONFIG_DIR/templates" "$CONFIG_DIR/playbooks" "$CONFIG_DIR/memory-seed" \
         "$CONFIG_DIR/bin" "$EAOS_DIR/vendor"

# 1) Clone or update agency-agents (the persona library EAOS builds on), pinned to AGENCY_SHA.
if [ -d "$VENDOR_DIR/.git" ]; then
  say "Updating agency-agents (pinned @ ${AGENCY_SHA:0:12})..."
  # Fetch only if the pinned commit isn't already local — routine re-runs stay offline-safe.
  git -C "$VENDOR_DIR" cat-file -e "$AGENCY_SHA^{commit}" 2>/dev/null || \
    git -C "$VENDOR_DIR" fetch --quiet origin "$AGENCY_SHA" 2>/dev/null || true
  git -C "$VENDOR_DIR" checkout -q "$AGENCY_SHA" 2>/dev/null || say "(skip; offline or SHA unreachable?)"
else
  say "Cloning agency-agents @ ${AGENCY_SHA:0:12}..."
  if git clone --quiet "$AGENCY_REPO" "$VENDOR_DIR" 2>/dev/null; then
    git -C "$VENDOR_DIR" checkout -q "$AGENCY_SHA" || \
      say "WARN: could not check out pinned SHA $AGENCY_SHA (using default branch tip instead)"
  else
    say "WARN: could not clone agency-agents (offline?). EAOS core still installs."
  fi
fi

# 2) Install agency-agents personas (prefixed, so they never clash with EAOS names).
if [ -d "$VENDOR_DIR" ]; then
  say "Installing agency-agents personas -> $AGENTS_DIR"
  find "$VENDOR_DIR" -name '*.md' -not -iname 'readme*' -print0 2>/dev/null | \
    while IFS= read -r -d '' f; do
      install_file "$f" "$AGENTS_DIR/agency-$(basename "$f")"
    done
fi

# 3) Install EAOS engineering personas (the collaborating team).
say "Installing EAOS engineering agents -> $AGENTS_DIR"
for f in "$EAOS_DIR"/agents/*.md; do
  [ -e "$f" ] || continue
  base="$(basename "$f")"
  [ "$base" = "README.md" ] && continue   # don't install the folder readme as an agent
  install_file "$f" "$AGENTS_DIR/$base"
done

# 4) Install THE slash command. One front door: /agentic-os fast-triages every shape of task
#    (feature, bug, incident, question, product, venture, release, triage) to its playbook.
say "Installing /agentic-os -> $COMMANDS_DIR"
install_file "$EAOS_DIR/commands/agentic-os.md" "$COMMANDS_DIR/agentic-os.md"
# Remove commands earlier EAOS versions installed (now folded into the front door).
for stale in agent-os.md incident.md triage.md; do
  if [ -e "$COMMANDS_DIR/$stale" ]; then
    rm -f "$COMMANDS_DIR/$stale" "$COMMANDS_DIR/$stale.bak"
    say "  removed legacy command -> $COMMANDS_DIR/$stale (use /agentic-os)"
  fi
done

# 5) Install global OS config the command reads at runtime.
say "Installing OS config -> $CONFIG_DIR"
install_file "$EAOS_DIR/orchestrator/routing.yaml"    "$CONFIG_DIR/routing.yaml"
install_file "$EAOS_DIR/orchestrator/protocol.md"     "$CONFIG_DIR/protocol.md"
install_file "$EAOS_DIR/orchestrator/loop.md"         "$CONFIG_DIR/loop.md"
install_file "$EAOS_DIR/orchestrator/orchestrator.md" "$CONFIG_DIR/orchestrator.md"
for f in "$EAOS_DIR"/templates/*.md; do
  [ -e "$f" ] || continue
  install_file "$f" "$CONFIG_DIR/templates/$(basename "$f")"
done
for f in "$EAOS_DIR"/playbooks/*.md; do
  [ -e "$f" ] || continue
  install_file "$f" "$CONFIG_DIR/playbooks/$(basename "$f")"
done

# 5a) Install the eaos runtime CLI (mechanical bookkeeping — task ids, war-room appends, loop
#     ceilings, spawn budget, gates, DoD verification; see docs/reviews/2026-07-13-eaos-cli-spec.md).
say "Installing eaos runtime CLI -> $CONFIG_DIR/bin"
install_file "$EAOS_DIR/scripts/eaos" "$CONFIG_DIR/bin/eaos"
chmod +x "$CONFIG_DIR/bin/eaos"

# 5b) Seed the memory index so a fresh project has something to copy on its first run
#     (memory/README.md: index.md is "always loaded" — the command's Step 0 seeds from here).
say "Seeding memory index -> $CONFIG_DIR/memory-seed"
install_file "$EAOS_DIR/memory/index.md"  "$CONFIG_DIR/memory-seed/index.md"
install_file "$EAOS_DIR/memory/README.md" "$CONFIG_DIR/memory-seed/README.md"

# 5c) Install the degraded-mode procedure the installed protocol/verifier reference at
#     runtime (protocol.md and agents/verifier.md point to adapters/solo-mode.md, resolved
#     relative to $CONFIG_DIR).
say "Installing solo-mode fallback -> $CONFIG_DIR/adapters"
mkdir -p "$CONFIG_DIR/adapters"
install_file "$EAOS_DIR/adapters/solo-mode.md" "$CONFIG_DIR/adapters/solo-mode.md"

# 6) Install EAOS skills.
# Backups go OUTSIDE $SKILLS_DIR: Claude Code discovers every directory under skills/ as a
# skill, so a foo.bak/ dir there would register a duplicate phantom skill.
SKILL_BACKUPS="$CONFIG_DIR/skill-backups"
say "Installing EAOS skills -> $SKILLS_DIR"
for d in "$EAOS_DIR/skills/"*/; do
  [ -d "$d" ] || continue
  name="$(basename "$d")"
  dst="$SKILLS_DIR/$name"
  if [ -d "$dst" ] && ! diff -rq "$d" "$dst" >/dev/null 2>&1; then
    mkdir -p "$SKILL_BACKUPS"
    rm -rf "$SKILL_BACKUPS/$name"
    cp -Rf "$dst" "$SKILL_BACKUPS/$name"
    say "  backed up modified skill -> $SKILL_BACKUPS/$name"
  fi
  # Remove-then-copy so files deleted upstream don't linger in the installed skill.
  # ${d%/} strips the glob's trailing slash — with it, BSD cp would splat the CONTENTS
  # of every skill into $SKILLS_DIR instead of copying the directory itself.
  rm -rf "$dst"
  cp -Rf "${d%/}" "$SKILLS_DIR/"
done

say ""
say "Verifying install:"
for f in commands/agentic-os.md \
         eaos/orchestrator.md eaos/routing.yaml eaos/memory-seed/index.md; do
  if [ -e "$CLAUDE_DIR/$f" ]; then printf "  \033[0;32m✓\033[0m %s\n" "~/.claude/$f"; else printf "  \033[0;31m✗ MISSING\033[0m %s\n" "~/.claude/$f"; fi
done
# Agents: derive the required set from every agents/*.md basename (except README) — the same
# list scripts/eaos-doctor.sh uses, so the two health checks can never drift apart.
need_agents="$(cd "$EAOS_DIR/agents" && ls *.md 2>/dev/null | sed 's/\.md$//' | grep -v '^README$')"
miss=""
for a in $need_agents; do [ -e "$AGENTS_DIR/$a.md" ] || miss="$miss $a"; done
if [ -z "$miss" ]; then
  printf "  \033[0;32m✓\033[0m all EAOS worker personas installed\n"
else
  printf "  \033[0;31m✗ MISSING agents:\033[0m%s\n" "$miss"
fi
say ""
say "Installed. Runtime state is PROJECT-LOCAL: each run creates ./.eaos/<task-id>/ where you"
say "invoke it (war room, artifacts) plus ./.eaos/memory/ (decisions, patterns, lessons)."
say ""
say "Usage — from inside any project, in Claude Code (RESTART Claude Code after first install):"
say "    /agentic-os <task>      (the one command — features, bugs, incidents, questions, triage)"
