#!/usr/bin/env bash
# capture-run.sh — sanitize a real .eaos task folder into examples/runs/ (evidence capture).
# Usage: scripts/capture-run.sh <task-id> [--src <project-root>] [--out <dir>]
# Copies warroom + state + artifacts, rewrites home paths, flags likely secrets for manual
# review. NEVER publishes anything by itself — output is a local folder you review first.
set -euo pipefail

TASK="${1:?usage: capture-run.sh <task-id> [--src <project-root>] [--out <dir>]}"; shift || true
SRC="$(pwd)"; OUT=""
while [ $# -gt 0 ]; do case "$1" in
  --src) SRC="$2"; shift 2;;
  --out) OUT="$2"; shift 2;;
  *) echo "unknown arg: $1" >&2; exit 2;;
esac; done
EAOS_REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${OUT:-$EAOS_REPO/examples/runs/$(date +%Y-%m-%d)-$TASK}"
SRC_TASK="$SRC/.eaos/$TASK"
[ -d "$SRC_TASK" ] || { echo "not found: $SRC_TASK" >&2; exit 1; }

mkdir -p "$OUT"
cp -R "$SRC_TASK/." "$OUT/"
# Include the episode line if present.
if [ -f "$SRC/.eaos/runs.jsonl" ]; then
  grep "\"task\": \"$TASK\"" "$SRC/.eaos/runs.jsonl" > "$OUT/episode.jsonl" || true
fi

# Sanitize: home paths -> ~, common env-style secrets flagged (not auto-removed — a human
# must look; silent scrubbing breeds false confidence).
find "$OUT" -type f \( -name '*.md' -o -name '*.json' -o -name '*.jsonl' -o -name '*.yaml' \) | while IFS= read -r f; do
  sed -i '' "s|/Users/[a-zA-Z0-9_.-]*|~|g" "$f" 2>/dev/null || sed -i "s|/Users/[a-zA-Z0-9_.-]*|~|g" "$f"
done
echo "== manual review required — potential sensitive matches =="
grep -rniE 'api[_-]?key|secret|token|password|Bearer |sk-[a-zA-Z0-9]|postgres://|mysql://' "$OUT" \
  | grep -v 'no secrets' | head -20 || echo "(none matched the patterns — still skim before publishing)"

cat > "$OUT/README.md" << RME
# Captured run: $TASK ($(date +%Y-%m-%d))
Source project: (fill in — name only, no paths)
Task: (one line — what was asked)
Outcome: (verified / partial / unverified — from episode.jsonl)
Notable: (defects caught, loop-backs, anything the run proved)
Sanitization: home paths rewritten; secrets grep reviewed by: (your name, date)
RME
echo "captured -> $OUT   (review README.md TODOs + the grep output above before any publish)"
