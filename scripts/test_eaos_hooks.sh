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

# install + (no-op re-install) + uninstall + (no-op) = exactly TWO real changes, so
# exactly two backups — a one-second-resolution name would have collapsed them (medium-2).
n_backups="$(ls "$HDIR"/settings.json.bak-* 2>/dev/null | wc -l | tr -d ' ')"
assert_eq "(h) one backup per real change, none collide" "2" "$n_backups"

rm -f /tmp/eaos_install_test.$$ /tmp/eaos_install_test2.$$ /tmp/eaos_uninstall_test.$$ /tmp/eaos_uninstall_test2.$$
rm -rf "$HDIR"

echo "=== (i) hostile tool_input never reaches a shell (round 4 medium-5) ==="
new_project 5
TID="$(new_task "$PROJ")"
CANARY="$PROJ/canary-was-executed"
hostile="\$(touch $CANARY); \`touch $CANARY\`; x'; touch $CANARY; 'y"
hostile_json="$(python3 -c '
import json, sys
print(json.dumps({"tool_name": "Task", "tool_input": {"subagent_type": sys.argv[1]},
                  "cwd": sys.argv[2], "tool_use_id": "tu-i"}))
' "$hostile" "$PROJ")"
run_hook pretool "$hostile_json"
assert_eq "(i) exit code 0" "0" "$HOOK_RC"
if [ -e "$CANARY" ]; then bad "(i) canary file was created — injection executed"; \
else ok "(i) canary not created — hostile text never executed"; fi
assert_eq "(i) spawn still recorded" "1" "$(spawns_of "$PROJ" "$TID")"
stored="$(grep -c 'touch' "$PROJ/.eaos/$TID/warroom.md")"
if [ "$stored" -ge 1 ]; then ok "(i) hostile text stored literally in warroom"; \
else bad "(i) hostile agent name missing from warroom"; fi
rm -rf "$PROJ"

echo "=== (j) lock contention is infrastructure -> both modes fail OPEN (round 4 HIGH-2) ==="
new_project 5
TID="$(new_task "$PROJ")"
echo 999999 > "$PROJ/.eaos/.lock"          # fresh lock held by "another process"
run_hook pretool "$(pretool_json "$PROJ" Task developer "tu-j")"
assert_eq "(j) pretool exit 0 under held lock" "0" "$HOOK_RC"
assert_empty "(j) pretool stderr silent" "$HOOK_ERR"
run_hook stop "$(printf '{"cwd":"%s","session_id":"sj"}' "$PROJ")"
assert_eq "(j) stop exit 0 under held lock (incomplete audit is not drift)" "0" "$HOOK_RC"
assert_empty "(j) stop stderr silent" "$HOOK_ERR"
rm -f "$PROJ/.eaos/.lock"
assert_eq "(j) nothing recorded while locked" "0" "$(spawns_of "$PROJ" "$TID")"
rm -rf "$PROJ"

echo "=== (k) two sessions, one checkout -> each hook fire lands on ITS task (round 4 HIGH-4) ==="
new_project 5
T1="$(cd "$PROJ" && python3 "$EAOS" task new "alpha migration" --session s1)"
T2="$(cd "$PROJ" && python3 "$EAOS" task new "beta dashboard" --session s2 | tail -1)"
assert_eq "(k) global CURRENT points at the latest task" "$T2" "$(cat "$PROJ/.eaos/CURRENT")"
( cd "$PROJ" && python3 "$EAOS" phase "$T1" DESIGN >/dev/null && python3 "$EAOS" phase "$T2" DESIGN >/dev/null )
run_hook pretool "$(printf '{"tool_name":"Task","tool_input":{"subagent_type":"developer"},"cwd":"%s","tool_use_id":"tu-k1","session_id":"s1"}' "$PROJ")"
assert_eq "(k) session one hook exit 0" "0" "$HOOK_RC"
assert_eq "(k) session one spawn on T1" "1" "$(spawns_of "$PROJ" "$T1")"
assert_eq "(k) nothing on T2" "0" "$(spawns_of "$PROJ" "$T2")"
run_hook pretool "$(printf '{"tool_name":"Task","tool_input":{"subagent_type":"qa"},"cwd":"%s","tool_use_id":"tu-k2","session_id":"s2"}' "$PROJ")"
assert_eq "(k) session two spawn on T2" "1" "$(spawns_of "$PROJ" "$T2")"
# a THIRD session with no mapping and two active tasks: ambiguous -> fail open, no guess
run_hook pretool "$(printf '{"tool_name":"Task","tool_input":{"subagent_type":"dev"},"cwd":"%s","tool_use_id":"tu-k3","session_id":"s3"}' "$PROJ")"
assert_eq "(k) unmapped session exit 0" "0" "$HOOK_RC"
assert_eq "(k) unmapped session recorded nothing on T1" "1" "$(spawns_of "$PROJ" "$T1")"
assert_eq "(k) unmapped session recorded nothing on T2" "1" "$(spawns_of "$PROJ" "$T2")"
# stop for s1 audits T1 (drift injected on T1 only), stop for s2 stays clean
python3 - "$PROJ/.eaos/$T1/state.json" <<'PYEND'
import json, sys
p = sys.argv[1]
s = json.load(open(p)); s["spawns"]["count"] = 9
json.dump(s, open(p, "w"))
PYEND
run_hook stop "$(printf '{"cwd":"%s","session_id":"s2"}' "$PROJ")"
assert_eq "(k) stop for s2 clean (its task is fine)" "0" "$HOOK_RC"
run_hook stop "$(printf '{"cwd":"%s","session_id":"s1"}' "$PROJ")"
assert_eq "(k) stop for s1 blocks on T1 drift" "2" "$HOOK_RC"
assert_contains "(k) stop for s1 names T1" "$HOOK_ERR" "$T1"
rm -rf "$PROJ"

echo "=== (l) posttool binds the session the moment 'eaos task new' runs ==="
new_project 5
TL="$(new_task "$PROJ")"                    # created WITHOUT --session (as the model does)
post_json="$(python3 -c '
import json, sys
print(json.dumps({"tool_name": "Bash", "session_id": "sl", "cwd": sys.argv[1],
  "tool_use_id": "tu-l", "tool_input": {"command": "python3 ~/.claude/eaos/bin/eaos task new \"x\" --kind feature"},
  "tool_response": {"stdout": sys.argv[2] + "\n", "stderr": "", "exit_code": 0}}))
' "$PROJ" "$TL")"
run_hook posttool "$post_json"
assert_eq "(l) posttool exit 0" "0" "$HOOK_RC"
assert_eq "(l) session mapped to the new task" "$TL" "$(cat "$PROJ/.eaos/sessions/sl" 2>/dev/null)"
# an unrelated Bash call binds nothing
run_hook posttool "$(printf '{"tool_name":"Bash","session_id":"sm","cwd":"%s","tool_use_id":"tu-l2","tool_input":{"command":"ls"},"tool_response":{"stdout":"T-999\\n"}}' "$PROJ")"
assert_eq "(l) non-task-new Bash exit 0" "0" "$HOOK_RC"
if [ -e "$PROJ/.eaos/sessions/sm" ]; then bad "(l) unrelated Bash call created a mapping"; \
else ok "(l) unrelated Bash call binds nothing"; fi
rm -rf "$PROJ"

echo "=== (m) installer: preserves 0600, refuses malformed hooks, quotes paths with spaces ==="
HDIR="$(mktemp -d)"
export CLAUDE_HOME="$HDIR"
mkdir -p "$CLAUDE_HOME/eaos/bin"; cp "$HOOK" "$CLAUDE_HOME/eaos/bin/eaos-hook.sh"
printf '{"env":{"SECRET":"1"}}\n' > "$CLAUDE_HOME/settings.json"; chmod 600 "$CLAUDE_HOME/settings.json"
bash "$INSTALL" >/dev/null 2>&1
assert_eq "(m) install exit 0" "0" "$?"
mode_of() { stat -f '%Lp' "$1" 2>/dev/null || stat -c '%a' "$1"; }
assert_eq "(m) settings.json stays 0600" "600" "$(mode_of "$CLAUDE_HOME/settings.json")"
bk="$(ls "$HDIR"/settings.json.bak-* | head -1)"
assert_eq "(m) backup is 0600" "600" "$(mode_of "$bk")"
n_post="$(python3 -c "
import json
d = json.load(open('$CLAUDE_HOME/settings.json'))
print(sum(1 for e in d['hooks'].get('PostToolUse', []) for h in e.get('hooks', [])
          if 'eaos-hook.sh posttool' in h.get('command', '') and e.get('matcher') == 'Bash'))
")"
assert_eq "(m) PostToolUse Bash entry installed" "1" "$n_post"
# malformed: PreToolUse is an object, not a list -> refuse, leave untouched
printf '{"hooks":{"PreToolUse":{"keep":"me"}}}\n' > "$CLAUDE_HOME/settings.json"
bash "$INSTALL" >/dev/null 2>/tmp/eaos_m_err.$$
assert_eq "(m) malformed shape -> exit 1" "1" "$?"
assert_contains "(m) refusal names the field" "$(cat /tmp/eaos_m_err.$$)" "hooks.PreToolUse"
assert_eq "(m) file left untouched" '{"hooks":{"PreToolUse":{"keep":"me"}}}' "$(cat "$CLAUDE_HOME/settings.json")"
rm -f /tmp/eaos_m_err.$$
rm -rf "$HDIR"
# path with a space: the generated command must still exec
HDIR="$(mktemp -d)/home with space"
mkdir -p "$HDIR/eaos/bin"; export CLAUDE_HOME="$HDIR"
printf '#!/bin/sh\nexit 0\n' > "$HDIR/eaos/bin/eaos-hook.sh"; chmod +x "$HDIR/eaos/bin/eaos-hook.sh"
bash "$INSTALL" >/dev/null 2>&1
cmd="$(python3 -c "
import json
d = json.load(open('$HDIR/settings.json'))
print(d['hooks']['Stop'][0]['hooks'][0]['command'])
")"
sh -c "$cmd" </dev/null >/dev/null 2>&1
assert_eq "(m) quoted hook command execs from a path with spaces" "0" "$?"
rm -rf "$(dirname "$HDIR")"

echo ""
echo "========================================"
echo "$pass_count passed, $fail_count failed"
if [ "$fail_count" -gt 0 ]; then
  exit 1
fi
exit 0
