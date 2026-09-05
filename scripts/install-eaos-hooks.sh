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
# Task|Agent, a PostToolUse entry matching Bash (binds the session to the task
# `eaos task new` just created — round 4 HIGH-4) and a Stop entry, all invoking
# "<eaos-hook.sh> <mode>" with the path shell-quoted. Idempotent — a second run detects
# our own entries by their exact command string and adds nothing new. Backs up
# settings.json to settings.json.bak-<ns>-<pid> (exclusive create, mode 0600) before any
# real change (no backup, no write, on a true no-op re-run) and PRESERVES the original
# file mode on the rewritten settings.json (round 4 HIGH-3: a 0600 file stays 0600).
# Refuses — leaving the file untouched — when an existing hooks/PreToolUse/PostToolUse/
# Stop value has an unexpected shape (round 4 medium-3). `--uninstall` removes only
# entries whose command references eaos-hook.sh, leaving every other hook (including a
# pre-existing unrelated one on the same event) untouched.
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
import shlex
import stat
import sys
import time

settings_path = os.environ["SETTINGS_PATH"]
hook_path = os.environ["HOOK_PATH"]
mode = os.environ["MODE"]

QUOTED = shlex.quote(hook_path)   # a CLAUDE_HOME with spaces must still exec (medium-4)
PRETOOL_CMD = f"{QUOTED} pretool"
POSTTOOL_CMD = f"{QUOTED} posttool"
STOP_CMD = f"{QUOTED} stop"
PRETOOL_MATCHER = "Task|Agent"
POSTTOOL_MATCHER = "Bash"
EVENTS = (("PreToolUse", PRETOOL_CMD, PRETOOL_MATCHER),
          ("PostToolUse", POSTTOOL_CMD, POSTTOOL_MATCHER),
          ("Stop", STOP_CMD, None))

class SchemaError(Exception):
    pass

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

def check_shape(settings):
    # Never "repair" a value we do not understand — an unexpected shape means a human
    # (or another tool) put something there; silently replacing it loses their data.
    if not isinstance(settings, dict):
        raise SchemaError("settings.json top level is not a JSON object")
    hooks = settings.get("hooks")
    if hooks is None:
        return
    if not isinstance(hooks, dict):
        raise SchemaError('"hooks" exists but is not an object')
    for event, _cmd, _m in EVENTS:
        if event in hooks and not isinstance(hooks[event], list):
            raise SchemaError(f'"hooks.{event}" exists but is not a list')

def install(settings):
    check_shape(settings)
    changed = False
    actions = []
    hooks = settings.setdefault("hooks", {})
    for event, our_cmd, matcher in EVENTS:
        lst = hooks.setdefault(event, [])
        if not any(has_our_command(e, our_cmd) for e in lst if isinstance(e, dict)):
            entry = {"hooks": [{"type": "command", "command": our_cmd}]}
            if matcher:
                entry = {"matcher": matcher, **entry}
            lst.append(entry)
            changed = True
        actions.append(f"{event} -> {our_cmd}" + (f" (matcher: {matcher})" if matcher else ""))
    return settings, changed, actions

def uninstall(settings):
    check_shape(settings)
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        return settings, False, []

    changed = False
    removed = []
    for event, our_cmd, _matcher in EVENTS:
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

try:
    if mode == "install":
        after, changed, actions = install(working)
    else:
        after, changed, actions = uninstall(working)
except SchemaError as e:
    print(f"REFUSED unexpected settings.json shape: {e} — file left untouched", file=sys.stderr)
    sys.exit(1)

if not changed:
    print("NOCHANGE")
    sys.exit(0)

# Preserve the original mode (a private 0600 settings file must stay 0600 — HIGH-3);
# backups and the replacement are created 0600 + O_EXCL so they are never world-readable
# for even an instant, and two runs inside one second cannot overwrite one backup
# (medium-2: nanosecond + pid name, exclusive create). Ownership: unchanged by design —
# the file is rewritten by the same user that owns it; chown would need root.
orig_mode = None
if os.path.isfile(settings_path):
    orig_mode = stat.S_IMODE(os.stat(settings_path).st_mode)
    with open(settings_path, "rb") as f:
        original_bytes = f.read()
    backup_path = f"{settings_path}.bak-{time.time_ns()}-{os.getpid()}"
    fd = os.open(backup_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(fd, original_bytes)
    finally:
        os.close(fd)
    print(f"BACKUP {backup_path}")

tmp_path = f"{settings_path}.tmp.{os.getpid()}"
payload = (json.dumps(after, indent=2) + "\n").encode("utf-8")
fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
try:
    os.write(fd, payload)
finally:
    os.close(fd)
if orig_mode is not None:
    os.chmod(tmp_path, orig_mode)
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
