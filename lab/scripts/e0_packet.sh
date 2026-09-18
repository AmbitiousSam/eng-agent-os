#!/usr/bin/env bash
# e0_packet.sh — the bounded continuation packet for experiment E0.
#
# Produced at EVERY unit boundary in ALL four cells, by this script and nothing else, so
# the packet is identical in form across cells. Reset cells paste it as the first thing in
# a new session; persistent cells save it and do not consume it. It carries state, never a
# transcript: no worker output, no reasoning, no war-room prose.
#
# Usage (from the participant workspace): e0_packet.sh <task-id> <next-unit-number>
# Output is capped (head limits below) so the packet stays bounded however long the run.
set -uo pipefail

TASK="${1:?usage: e0_packet.sh <task-id> <next-unit-number>}"
NEXT="${2:?usage: e0_packet.sh <task-id> <next-unit-number>}"
EAOS="${EAOS_BIN:-$HOME/.claude/eaos/bin/eaos}"

echo "=== E0 CONTINUATION PACKET ==="
echo "You are continuing an existing task in this repository. Prior sessions are closed;"
echo "everything you need is below and in the repository itself."
echo
echo "## Code state"
echo "branch: $(git branch --show-current 2>/dev/null)   HEAD: $(git rev-parse --short HEAD 2>/dev/null)"
echo "uncommitted: $(git status --short 2>/dev/null | wc -l | tr -d ' ') path(s)"
git status --short 2>/dev/null | head -10
echo "recent commits:"
git log --oneline -8 2>/dev/null
echo
echo "## Task state (eaos status $TASK, bounded)"
python3 "$EAOS" status "$TASK" 2>/dev/null | head -40
echo
echo "## Standing constraints (unchanged since unit 1)"
echo "1. No new third-party dependencies."
echo "2. The existing test suite keeps passing."
echo "3. Routes that change or reveal user-owned data use the existing login_required."
echo "4. Schema changes go in schema.sql."
echo
echo "## Next"
echo "Unit $NEXT follows in the next message."
echo "=== END PACKET ==="
