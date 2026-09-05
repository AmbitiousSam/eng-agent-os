#!/usr/bin/env bash
# test_eaos_hooks.sh — bash tests for scripts/eaos-hook.sh (M-007 hooks-as-accelerators)
# and scripts/install-eaos-hooks.sh. Feeds crafted hook-JSON on stdin against a real
# `eaos init`/`task new` in a tempdir, exactly the way Claude Code invokes the hook.
# Exit 0 = all scenarios passed, 1 = at least one failed.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EAOS="$REPO_ROOT/scripts/eaos"
HOOK="$REPO_ROOT/scripts/eaos-hook.sh"
INSTALL="$REPO_ROOT/scripts/install-eaos-hooks.sh"

pass_count=0
fail_count=0

ok() { pass_count=$((pass_count + 1)); printf "  \033[0;32mok\033[0m  - %s\n" "$*"; }
bad() { fail_count=$((fail_count + 1)); printf "  \033[0;31mFAIL\033[0m - %s\n" "$*"; }

assert_eq() {  # assert_eq <label> <expected> <actual>
  if [ "$2" = "$3" ]; then ok "$1"; else bad "$1 (expected '$2', got '$3')"; fi
}

assert_contains() {  # assert_contains <label> <haystack> <needle>
  case "$2" in
    *"$3"*) ok "$1" ;;
    *) bad "$1 (expected to find '$3' in: $2)" ;;
  esac
}

assert_empty() {  # assert_empty <label> <value>
  if [ -z "$2" ]; then ok "$1"; else bad "$1 (expected empty, got: $2)"; fi
}

# A fresh tempdir with `eaos init` already run. Isolates CLAUDE_HOME to an empty dir so
# eaos-hook.sh always falls back to THIS checkout's scripts/eaos — never a real
# ~/.claude install that happens to exist on the dev machine. Sets globals PROJ and
# (exported) CLAUDE_HOME directly rather than via command substitution — `export`
# inside a `$(...)` subshell would never reach the parent shell.
new_project() {
  PROJ="$(mktemp -d)"
  CLAUDE_HOME="$PROJ/fake-claude-home"
  export CLAUDE_HOME
  mkdir -p "$CLAUDE_HOME"
  ( cd "$PROJ" && python3 "$EAOS" init --max-spawns "${1:-2}" >/dev/null )
}

new_task() {  # new_task <project-dir> [title]
  ( cd "$1" && python3 "$EAOS" task new "${2:-Hook test task}" )
}

run_hook() {  # run_hook <mode> <json>   -> sets HOOK_RC HOOK_OUT HOOK_ERR
  local mode="$1" json="$2"
  local out err rc
  out="$(printf '%s' "$json" | CLAUDE_HOME="$CLAUDE_HOME" bash "$HOOK" "$mode" 2>/tmp/eaos_hook_test_stderr.$$)"
  rc=$?
  err="$(cat /tmp/eaos_hook_test_stderr.$$)"
  rm -f "/tmp/eaos_hook_test_stderr.$$"
  HOOK_RC="$rc"; HOOK_OUT="$out"; HOOK_ERR="$err"
}

spawns_of() {  # spawns_of <project-dir> <task-id>
  ( cd "$1" && python3 "$EAOS" status "$2" ) | sed -n 's/^Spawns: \([0-9]*\)\/.*/\1/p'
}

pretool_json() {  # pretool_json <cwd> <tool_name> <subagent_type> <tool_use_id>
  printf '{"tool_name":"%s","tool_input":{"subagent_type":"%s"},"cwd":"%s","tool_use_id":"%s"}' \
    "$2" "$3" "$1" "$4"
}

echo "=== (a) pretool with Task input -> spawn recorded, exit 0 ==="
new_project 5
TID="$(new_task "$PROJ")"
run_hook pretool "$(pretool_json "$PROJ" Task developer "tu-a")"
assert_eq "(a) exit code 0" "0" "$HOOK_RC"
assert_eq "(a) spawn recorded" "1" "$(spawns_of "$PROJ" "$TID")"
rm -rf "$PROJ"

echo "=== (b) same tool_use_id twice -> one spawn (idempotency) ==="
new_project 5
TID="$(new_task "$PROJ")"
run_hook pretool "$(pretool_json "$PROJ" Task developer "tu-b")"
assert_eq "(b) first call exit 0" "0" "$HOOK_RC"
run_hook pretool "$(pretool_json "$PROJ" Task developer "tu-b")"
assert_eq "(b) replay exit 0" "0" "$HOOK_RC"
assert_eq "(b) still one spawn" "1" "$(spawns_of "$PROJ" "$TID")"
rm -rf "$PROJ"

echo "=== (c) cap exceeded -> exit 2, stderr has BUDGET EXCEEDED ==="
new_project 1
TID="$(new_task "$PROJ")"
run_hook pretool "$(pretool_json "$PROJ" Task developer "tu-c1")"
assert_eq "(c) first spawn under cap exits 0" "0" "$HOOK_RC"
run_hook pretool "$(pretool_json "$PROJ" Task qa "tu-c2")"
assert_eq "(c) over-cap spawn exits 2" "2" "$HOOK_RC"
assert_contains "(c) stderr mentions BUDGET EXCEEDED" "$HOOK_ERR" "BUDGET EXCEEDED"
assert_eq "(c) rejected spawn not recorded" "1" "$(spawns_of "$PROJ" "$TID")"
rm -rf "$PROJ"

echo "=== (d) no CURRENT -> exit 0, silent ==="
new_project 5
# no task new -> .eaos/CURRENT never created
run_hook pretool "$(pretool_json "$PROJ" Task developer "tu-d")"
assert_eq "(d) exit code 0" "0" "$HOOK_RC"
assert_empty "(d) stdout silent" "$HOOK_OUT"
assert_empty "(d) stderr silent" "$HOOK_ERR"
rm -rf "$PROJ"

echo "=== (e) non-Task tool -> exit 0, no spawn ==="
new_project 5
TID="$(new_task "$PROJ")"
run_hook pretool "$(printf '{"tool_name":"Bash","tool_input":{"command":"ls"},"cwd":"%s","tool_use_id":"tu-e"}' "$PROJ")"
assert_eq "(e) exit code 0" "0" "$HOOK_RC"
assert_empty "(e) stdout silent" "$HOOK_OUT"
assert_empty "(e) stderr silent" "$HOOK_ERR"
assert_eq "(e) no spawn recorded" "0" "$(spawns_of "$PROJ" "$TID")"
rm -rf "$PROJ"

echo "=== (f) stop with drift (edited state) -> exit 2, audit text ==="
new_project 5
TID="$(new_task "$PROJ")"
run_hook pretool "$(pretool_json "$PROJ" Task developer "tu-f")"
assert_eq "(f) setup spawn exits 0" "0" "$HOOK_RC"
# Introduce drift the way the spec asks: hand-edit state.json so recorded spawns no
# longer match the warroom log eaos itself wrote — a real bookkeeping bypass, not a
# contrived audit-internal fixture.
python3 - "$PROJ/.eaos/$TID/state.json" <<'PYEOF'
import json, sys
p = sys.argv[1]
with open(p) as f:
    s = json.load(f)
s["spawns"]["count"] = 9
with open(p, "w") as f:
    json.dump(s, f)
PYEOF
run_hook stop "$(printf '{"cwd":"%s"}' "$PROJ")"
assert_eq "(f) stop exit code 2" "2" "$HOOK_RC"
assert_contains "(f) stderr names the task" "$HOOK_ERR" "$TID"
assert_contains "(f) stderr says reconcile" "$HOOK_ERR" "reconcile before finishing"
assert_contains "(f) stderr includes audit detail" "$HOOK_ERR" "spawns_vs_warroom"
DRIFT_PROJ="$PROJ"; DRIFT_TID="$TID"   # reused by (g), cleaned up after

echo "=== (g) stop with stop_hook_active=true -> exit 0 (loop guard wins over drift) ==="
run_hook stop "$(printf '{"cwd":"%s","stop_hook_active":true}' "$DRIFT_PROJ")"
assert_eq "(g) exit code 0 despite drift" "0" "$HOOK_RC"
assert_empty "(g) stdout silent" "$HOOK_OUT"
assert_empty "(g) stderr silent" "$HOOK_ERR"
rm -rf "$DRIFT_PROJ"

echo "=== (h) install-eaos-hooks.sh merge is idempotent; --uninstall removes only ours ==="
HDIR="$(mktemp -d)"
export CLAUDE_HOME="$HDIR"
mkdir -p "$CLAUDE_HOME/eaos/bin"
cp "$HOOK" "$CLAUDE_HOME/eaos/bin/eaos-hook.sh"
cat > "$CLAUDE_HOME/settings.json" <<'EOF'
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "/usr/local/bin/pre-existing-hook.sh"}]
      }
    ]
  },
  "unrelatedTopLevelKey": true
}
EOF
bash "$INSTALL" >/tmp/eaos_install_test.$$ 2>&1
install_rc1=$?
assert_eq "(h) first install exits 0" "0" "$install_rc1"
n_pretool="$(python3 -c "
import json
d = json.load(open('$CLAUDE_HOME/settings.json'))
print(sum(1 for e in d['hooks']['PreToolUse'] for h in e.get('hooks', [])
          if 'eaos-hook.sh' in h.get('command', '')))
")"
assert_eq "(h) one PreToolUse eaos-hook.sh entry after install" "1" "$n_pretool"
n_stop="$(python3 -c "
import json
d = json.load(open('$CLAUDE_HOME/settings.json'))
print(sum(1 for e in d['hooks'].get('Stop', []) for h in e.get('hooks', [])
          if 'eaos-hook.sh' in h.get('command', '')))
")"
assert_eq "(h) one Stop eaos-hook.sh entry after install" "1" "$n_stop"
pre_existing_intact="$(python3 -c "
import json
d = json.load(open('$CLAUDE_HOME/settings.json'))
cmds = [h.get('command') for e in d['hooks']['PreToolUse'] for h in e.get('hooks', [])]
print('yes' if '/usr/local/bin/pre-existing-hook.sh' in cmds else 'no')
")"
assert_eq "(h) pre-existing unrelated hook untouched" "yes" "$pre_existing_intact"
assert_eq "(h) unrelated top-level key untouched" "true" "$(python3 -c "
import json; print(str(json.load(open('$CLAUDE_HOME/settings.json'))['unrelatedTopLevelKey']).lower())
")"

# Re-run: must NOT duplicate.
bash "$INSTALL" >/tmp/eaos_install_test2.$$ 2>&1
n_pretool_again="$(python3 -c "
import json
d = json.load(open('$CLAUDE_HOME/settings.json'))
print(sum(1 for e in d['hooks']['PreToolUse'] for h in e.get('hooks', [])
          if 'eaos-hook.sh' in h.get('command', '')))
")"
assert_eq "(h) re-install does not duplicate PreToolUse entry" "1" "$n_pretool_again"

# --uninstall: removes only ours.
bash "$INSTALL" --uninstall >/tmp/eaos_uninstall_test.$$ 2>&1
uninstall_rc=$?
assert_eq "(h) uninstall exits 0" "0" "$uninstall_rc"
still_has_ours="$(python3 -c "
import json
d = json.load(open('$CLAUDE_HOME/settings.json'))
hooks = d.get('hooks', {})
cmds = [h.get('command') for e in hooks.get('PreToolUse', []) for h in e.get('hooks', [])]
cmds += [h.get('command') for e in hooks.get('Stop', []) for h in e.get('hooks', [])]
print('yes' if any('eaos-hook.sh' in (c or '') for c in cmds) else 'no')
")"
assert_eq "(h) our entries gone after uninstall" "no" "$still_has_ours"
pre_existing_after_uninstall="$(python3 -c "
import json
d = json.load(open('$CLAUDE_HOME/settings.json'))
cmds = [h.get('command') for e in d['hooks']['PreToolUse'] for h in e.get('hooks', [])]
print('yes' if '/usr/local/bin/pre-existing-hook.sh' in cmds else 'no')
")"
assert_eq "(h) pre-existing unrelated hook survives uninstall" "yes" "$pre_existing_after_uninstall"

# Re-uninstall: idempotent no-op, still exits 0.
bash "$INSTALL" --uninstall >/tmp/eaos_uninstall_test2.$$ 2>&1
assert_eq "(h) repeat uninstall exits 0 (no-op)" "0" "$?"

n_backups="$(ls "$HDIR"/settings.json.bak-* 2>/dev/null | wc -l | tr -d ' ')"
if [ "${n_backups:-0}" -ge 1 ]; then ok "(h) at least one settings.json backup created"; \
else bad "(h) expected a settings.json.bak-<ts> backup file"; fi

rm -f /tmp/eaos_install_test.$$ /tmp/eaos_install_test2.$$ /tmp/eaos_uninstall_test.$$ /tmp/eaos_uninstall_test2.$$
rm -rf "$HDIR"

echo ""
echo "========================================"
echo "$pass_count passed, $fail_count failed"
if [ "$fail_count" -gt 0 ]; then
  exit 1
fi
exit 0
