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

say() { printf "\033[1;36m[eaos]\033[0m %s\n" "$*"; }

mkdir -p "$AGENTS_DIR" "$SKILLS_DIR" "$COMMANDS_DIR" \
         "$CONFIG_DIR/templates" "$EAOS_DIR/vendor"

# 1) Clone or update agency-agents (the persona library EAOS builds on).
if [ -d "$VENDOR_DIR/.git" ]; then
  say "Updating agency-agents..."
  git -C "$VENDOR_DIR" pull --ff-only || say "(skip update; offline?)"
else
  say "Cloning agency-agents..."
  git clone --depth 1 "$AGENCY_REPO" "$VENDOR_DIR" || \
    say "WARN: could not clone agency-agents (offline?). EAOS core still installs."
fi

# 2) Install agency-agents personas (prefixed, so they never clash with EAOS names).
if [ -d "$VENDOR_DIR" ]; then
  say "Installing agency-agents personas -> $AGENTS_DIR"
  find "$VENDOR_DIR" -name '*.md' -not -iname 'readme*' -print0 2>/dev/null | \
    while IFS= read -r -d '' f; do
      cp -f "$f" "$AGENTS_DIR/agency-$(basename "$f")"
    done
fi

# 3) Install EAOS engineering personas (the collaborating team).
say "Installing EAOS engineering agents -> $AGENTS_DIR"
cp -f "$EAOS_DIR/agents/"*.md "$AGENTS_DIR/" 2>/dev/null || true
rm -f "$AGENTS_DIR/README.md" 2>/dev/null || true   # don't install the folder readme as an agent

# 4) Install the /agentic-os slash command (the autonomous orchestrator driver).
say "Installing /agentic-os command -> $COMMANDS_DIR"
cp -f "$EAOS_DIR/commands/agentic-os.md" "$COMMANDS_DIR/"

# 5) Install global OS config the command reads at runtime.
say "Installing OS config -> $CONFIG_DIR"
cp -f "$EAOS_DIR/orchestrator/routing.yaml"   "$CONFIG_DIR/"
cp -f "$EAOS_DIR/orchestrator/protocol.md"    "$CONFIG_DIR/"
cp -f "$EAOS_DIR/orchestrator/loop.md"        "$CONFIG_DIR/"
cp -f "$EAOS_DIR/orchestrator/orchestrator.md" "$CONFIG_DIR/"
cp -f "$EAOS_DIR/templates/"*.md              "$CONFIG_DIR/templates/"

# 6) Install EAOS skills.
say "Installing EAOS skills -> $SKILLS_DIR"
for d in "$EAOS_DIR/skills/"*/; do [ -d "$d" ] && cp -rf "$d" "$SKILLS_DIR/"; done

say ""
say "Installed. Runtime state is PROJECT-LOCAL: each run creates ./.eaos/<task-id>/ where you"
say "invoke it (war room, artifacts) plus ./.eaos/memory/ (decisions, patterns, lessons)."
say ""
say "Usage — from inside any project, in Claude Code:"
say "    /agentic-os Add per-API-key rate limiting to the public REST API"
