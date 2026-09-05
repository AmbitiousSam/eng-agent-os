#!/usr/bin/env bash
# install-eaos-hooks.sh — OPT-IN installer for the EAOS hook accelerators (M-007,
# mechanisms.yaml). Different from scripts/install-hooks.sh, which enables this repo's
# own git pre-push gate — this one wires Claude Code's PreToolUse/Stop hooks (in
# ~/.claude/settings.json) to scripts/eaos-hook.sh, so `eaos spawn`/`eaos audit` happen
# without model cooperation on hosts that deliver those hook events. setup.sh installs
# the hook SCRIPT but deliberately does not run this — the hook contract asserts a real
# fail-closed budget/audit gate on the host, which is a per-user decision, not a default.
#
# Merges into settings.json (never clobbers): adds a PreToolUse entry matching
# Task|Agent and a Stop entry, both invoking "<eaos-hook.sh> <mode>". Idempotent — a
# second run detects our own entries by their exact command string and adds nothing
# new. Backs up settings.json to settings.json.bak-<epoch> before any real change (no
# backup, no write, on a true no-op re-run). `--uninstall` removes only entries whose
# command references eaos-hook.sh, leaving every other hook (including a pre-existing
# unrelated one on the same event) untouched.
#
# Usage: scripts/install-eaos-hooks.sh [--uninstall]
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="${CLAUDE_HOME:-$HOME/.claude}"
SETTINGS_PATH="$CLAUDE_DIR/settings.json"
HOOK_PATH="$CLAUDE_DIR/eaos/bin/eaos-hook.sh"

mode="install"
if [ "${1:-}" = "--uninstall" ]; then
  mode="uninstall"
elif [ $# -gt 0 ]; then
  echo "usage: $(basename "$0") [--uninstall]" >&2
  exit 2
fi

command -v python3 >/dev/null 2>&1 || { echo "python3 not found — cannot merge JSON safely." >&2; exit 1; }

if [ ! -e "$HOOK_PATH" ]; then
  echo "WARN: $HOOK_PATH not found yet — run ./setup.sh first (the hook fails open at" >&2
  echo "      runtime if it's missing, so this is safe to proceed with, but the" >&2
  echo "      accelerator won't do anything until the script is installed)." >&2
fi

mkdir -p "$CLAUDE_DIR"

RESULT="$(HOOK_PATH="$HOOK_PATH" SETTINGS_PATH="$SETTINGS_PATH" MODE="$mode" python3 - <<'PYEOF'
import json
import os
import sys
import time

settings_path = os.environ["SETTINGS_PATH"]
hook_path = os.environ["HOOK_PATH"]
mode = os.environ["MODE"]

PRETOOL_CMD = f"{hook_path} pretool"
STOP_CMD = f"{hook_path} stop"
PRETOOL_MATCHER = "Task|Agent"

def load_settings():
    if not os.path.isfile(settings_path):
        return {}
    with open(settings_path, encoding="utf-8") as f:
        text = f.read().strip()
    if not text:
        return {}
    return json.loads(text)

def entry_commands(entry):
    return [h.get("command") for h in entry.get("hooks", []) if isinstance(h, dict)]

def has_our_command(entry, cmd):
    return cmd in entry_commands(entry)

def install(settings):
    changed = False
    hooks = settings.setdefault("hooks", {})

    pre_list = hooks.setdefault("PreToolUse", [])
    if not isinstance(pre_list, list):
        pre_list = []
        hooks["PreToolUse"] = pre_list
    if not any(has_our_command(e, PRETOOL_CMD) for e in pre_list if isinstance(e, dict)):
        pre_list.append({
            "matcher": PRETOOL_MATCHER,
            "hooks": [{"type": "command", "command": PRETOOL_CMD}],
        })
        changed = True

    stop_list = hooks.setdefault("Stop", [])
    if not isinstance(stop_list, list):
        stop_list = []
        hooks["Stop"] = stop_list
    if not any(has_our_command(e, STOP_CMD) for e in stop_list if isinstance(e, dict)):
        stop_list.append({
            "hooks": [{"type": "command", "command": STOP_CMD}],
        })
        changed = True

    return settings, changed, [
        f"PreToolUse -> {PRETOOL_CMD} (matcher: {PRETOOL_MATCHER})",
        f"Stop -> {STOP_CMD}",
    ]

def uninstall(settings):
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        return settings, False, []

    changed = False
    removed = []
    for event, our_cmd in (("PreToolUse", PRETOOL_CMD), ("Stop", STOP_CMD)):
        entries = hooks.get(event)
        if not isinstance(entries, list):
            continue
        kept_entries = []
        for entry in entries:
            if not isinstance(entry, dict):
                kept_entries.append(entry)
                continue
            sub_hooks = entry.get("hooks", [])
            kept_sub = [h for h in sub_hooks
                        if not (isinstance(h, dict) and h.get("command") == our_cmd)]
            if len(kept_sub) != len(sub_hooks):
                changed = True
                removed.append(f"{event} -> {our_cmd}")
            if kept_sub:
                new_entry = dict(entry)
                new_entry["hooks"] = kept_sub
                kept_entries.append(new_entry)
            # an entry whose hooks list is now empty is dropped entirely (it was only
            # ever wrapping our own command)
        if kept_entries:
            hooks[event] = kept_entries
        elif event in hooks:
            del hooks[event]

    if not hooks and "hooks" in settings:
        del settings["hooks"]

    return settings, changed, removed

before = load_settings()
import copy
working = copy.deepcopy(before)

if mode == "install":
    after, changed, actions = install(working)
else:
    after, changed, actions = uninstall(working)

if not changed:
    print("NOCHANGE")
    sys.exit(0)

if os.path.isfile(settings_path):
    backup_path = f"{settings_path}.bak-{int(time.time())}"
    with open(settings_path, encoding="utf-8") as f:
        original_text = f.read()
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(original_text)
    print(f"BACKUP {backup_path}")

tmp_path = f"{settings_path}.tmp.{os.getpid()}"
with open(tmp_path, "w", encoding="utf-8") as f:
    json.dump(after, f, indent=2)
    f.write("\n")
os.replace(tmp_path, settings_path)

for a in actions:
    print(f"ACTION {a}")
print("CHANGED")
PYEOF
)"
rc=$?

if [ $rc -ne 0 ]; then
  echo "eaos hooks: failed to update $SETTINGS_PATH" >&2
  printf '%s\n' "$RESULT" >&2
  exit 1
fi

echo "$RESULT" | grep '^BACKUP ' | sed 's/^BACKUP /[eaos] backed up settings -> /'
echo "$RESULT" | grep '^ACTION ' | sed 's/^ACTION /[eaos] /'

if echo "$RESULT" | grep -q '^NOCHANGE$'; then
  if [ "$mode" = "install" ]; then
    echo "[eaos] hooks already installed in $SETTINGS_PATH — nothing to do."
  else
    echo "[eaos] no eaos-hook.sh entries found in $SETTINGS_PATH — nothing to do."
  fi
elif [ "$mode" = "install" ]; then
  echo "[eaos] hooks installed in $SETTINGS_PATH."
  echo "[eaos] accelerator only: eaos audit remains the backstop regardless (spec §11)."
  echo "[eaos] restart Claude Code for the new hooks to take effect."
else
  echo "[eaos] hooks removed from $SETTINGS_PATH."
fi
