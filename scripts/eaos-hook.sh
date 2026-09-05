#!/usr/bin/env bash
# eaos-hook.sh — Claude Code hook accelerator for EAOS (mechanism M-007:
# hooks-as-accelerators, mechanisms.yaml).
#
# ACCELERATOR, NOT AUTHORITY (spec §11 "Enforcement chain"): the eaos runtime/adapter
# wrapper is the authoritative mutation path. This script only makes `eaos spawn` and
# `eaos audit` happen without model cooperation, on a host that reliably delivers these
# hook events — it never becomes a second source of truth, and `eaos audit` remains the
# final reconciliation backstop regardless of whether this script ran at all.
#
# FAIL OPEN by default: any infrastructure problem (no .eaos/CURRENT, no eaos binary,
# unparseable stdin, an eaos usage/exit-2 error) exits 0 silently. An accelerator that
# turns into a wall on its own bugs is worse than no accelerator. There are exactly two
# INTENTIONAL fail-closed cases, both driven by a real eaos exit code, never by this
# script's own logic:
#   pretool: eaos spawn <CURRENT> exits 1 (BUDGET EXCEEDED or task BLOCKED) -> exit 2,
#            which blocks the tool call — the ceiling is binding.
#   stop:    eaos audit <CURRENT> exits 1 (bookkeeping drift found) -> exit 2, which
#            tells the MODEL to reconcile and continues the turn (not a human wall).
#
# Hook JSON contract confirmed against https://docs.claude.com/en/docs/claude-code/hooks
# (redirects to https://code.claude.com/docs/en/hooks) 2026-09-05: PreToolUse stdin
# carries tool_name/tool_input/tool_use_id/cwd/session_id; Stop stdin carries
# stop_hook_active/cwd/session_id; exit 0 = allow, exit 2 = block with stderr shown to
# the model, any other non-zero = non-blocking (stderr goes to the debug log only).
#
# Usage: eaos-hook.sh <pretool|stop>   (hook JSON arrives on stdin; nothing is written
# to stdout on the fail-open or exit-0 paths, so a healthy run is silent).
set -u

mode="${1:-}"
case "$mode" in
  pretool|stop) ;;
  *) exit 0 ;;   # unknown/missing mode: never wedge an unrecognized invocation
esac

command -v python3 >/dev/null 2>&1 || exit 0

stdin_json="$(cat)" || exit 0

# ---- resolve the eaos binary: installed copy first, then this repo's own scripts/eaos
# (relative to this script) so the same hook works against a dev checkout in tests.
CLAUDE_HOME_DIR="${CLAUDE_HOME:-$HOME/.claude}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
EAOS_BIN=""
if [ -f "$CLAUDE_HOME_DIR/eaos/bin/eaos" ]; then
  EAOS_BIN="$CLAUDE_HOME_DIR/eaos/bin/eaos"
elif [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/eaos" ]; then
  EAOS_BIN="$SCRIPT_DIR/eaos"
fi
[ -n "$EAOS_BIN" ] || exit 0

# ---- one python3 call parses the whole hook payload and hands back shell-safe
# KEY='quoted value' assignments (shlex.quote — safe under eval even if a value came
# from untrusted tool_input text). Keeping this to a single process is what makes the
# hook fast enough to sit on every PreToolUse/Stop without being felt.
parsed="$(python3 -c '
import json, sys, shlex, hashlib

raw = sys.stdin.read()
try:
    d = json.loads(raw)
    ok = isinstance(d, dict)
except Exception:
    d, ok = {}, False

tool_name = str(d.get("tool_name") or "")
cwd = str(d.get("cwd") or "")
tool_use_id = str(d.get("tool_use_id") or "")
stop_hook_active = bool(d.get("stop_hook_active"))

tool_input = d.get("tool_input") or {}
if not isinstance(tool_input, dict):
    tool_input = {}
agent_name = tool_input.get("subagent_type") or tool_input.get("description") or "unnamed"
agent_name = str(agent_name).strip()[:40] or "unnamed"

# Idempotency key material: the tool_use_id when present (stable across a hook retry
# for the SAME tool call), else a hash of the raw input (best-effort — still collapses
# byte-identical retries of an otherwise unidentified call).
key_src = tool_use_id if tool_use_id else raw
idem_key = "hook:" + hashlib.sha256(key_src.encode("utf-8", "surrogatepass")).hexdigest()

fields = {
    "PARSE_OK": "true" if ok else "false",
    "TOOL_NAME": tool_name,
    "CWD": cwd,
    "AGENT_NAME": agent_name,
    "STOP_HOOK_ACTIVE": "true" if stop_hook_active else "false",
    "IDEM_KEY": idem_key,
}
for k, v in fields.items():
    print(f"{k}={shlex.quote(v)}")
' <<<"$stdin_json" 2>/dev/null)" || exit 0

eval "$parsed" || exit 0
[ "${PARSE_OK:-false}" = "true" ] || exit 0

cwd="${CWD:-}"
[ -n "$cwd" ] || cwd="$PWD"

current_file="$cwd/.eaos/CURRENT"
[ -f "$current_file" ] || exit 0
current_task="$(tr -d '[:space:]' < "$current_file")"
[ -n "$current_task" ] || exit 0

case "$mode" in
pretool)
  # Case-insensitive match on the agent-launching tool. This is a second, independent
  # check on top of whatever matcher settings.json used to fire this hook in the first
  # place (belt-and-suspenders: harmless if settings.json already narrowed it).
  lname="$(printf '%s' "${TOOL_NAME:-}" | tr '[:upper:]' '[:lower:]')"
  case "$lname" in
    task|agent) ;;
    *) exit 0 ;;
  esac

  out="$(cd "$cwd" 2>/dev/null && python3 "$EAOS_BIN" spawn "$current_task" \
         --agent "${AGENT_NAME:-unnamed}" --idempotency-key "${IDEM_KEY}" 2>&1)"
  rc=$?
  if [ "$rc" -eq 1 ]; then
    printf '%s\n' "$out" >&2
    exit 2
  fi
  exit 0   # rc==0 recorded fine; any other rc is an infra/usage error -> fail open
  ;;
stop)
  [ "${STOP_HOOK_ACTIVE:-false}" = "true" ] && exit 0  # prevent a block/retry loop

  out="$(cd "$cwd" 2>/dev/null && python3 "$EAOS_BIN" audit "$current_task" 2>&1)"
  rc=$?
  if [ "$rc" -eq 1 ]; then
    {
      printf 'EAOS audit found bookkeeping drift on %s — reconcile before finishing:\n' \
             "$current_task"
      printf '%s\n' "$out"
    } >&2
    exit 2
  fi
  exit 0
  ;;
esac
