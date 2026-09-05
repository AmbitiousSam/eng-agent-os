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
# WHICH TASK (review round 4 HIGH-4): the task is resolved per SESSION through
# `eaos session resolve --session <session_id>` (.eaos/sessions/<session-id>), never
# through the global .eaos/CURRENT alone — two Claude sessions in one checkout must not
# attribute each other's spawns/audits. The mapping is created mechanically by the
# `posttool` mode below the moment `eaos task new` runs (PostToolUse on Bash: the task id
# is in the tool's stdout), or by `task new --session` / $EAOS_SESSION_ID. Resolution
# rules live in the CLI (one place, unit-tested); the short version: a mapped active task
# wins; with no mapping and exactly one active task the session is bound to it; anything
# ambiguous fails OPEN.
#
# FAIL OPEN by default: any infrastructure problem (no .eaos dir, no eaos binary,
# unparseable stdin, no resolvable task, an eaos usage/exit-2 error, and — round 4
# HIGH-2 — eaos exit 4 = LOCK CONTENTION) exits 0 silently. An accelerator that turns
# into a wall on its own bugs, or on another process holding a lock for 2 seconds, is
# worse than no accelerator. There are exactly two INTENTIONAL fail-closed cases, both
# driven by a real eaos POLICY verdict, never by this script's own logic:
#   pretool: eaos spawn exits 1 AND names the reason (BUDGET EXCEEDED or task BLOCKED)
#            -> exit 2, which blocks the tool call — the ceiling is binding.
#   stop:    eaos audit COMPLETED and exits 1 (bookkeeping drift found) -> exit 2, which
#            tells the MODEL to reconcile and continues the turn (not a human wall).
#
# Hook JSON contract confirmed against https://code.claude.com/docs/en/hooks 2026-09-05:
# every event carries session_id/cwd; PreToolUse/PostToolUse carry tool_name/tool_input/
# tool_use_id (PostToolUse adds tool_response — for Bash an object with stdout/stderr);
# Stop carries stop_hook_active. Exit 0 = allow, exit 2 = block with stderr shown to the
# model (PostToolUse cannot block), any other non-zero = non-blocking.
#
# Usage: eaos-hook.sh <pretool|posttool|stop>   (hook JSON arrives on stdin; nothing is
# written to stdout on the fail-open or exit-0 paths, so a healthy run is silent).
set -u

mode="${1:-}"
case "$mode" in
  pretool|posttool|stop) ;;
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
# from untrusted tool_input text; scenario (i) in test_eaos_hooks.sh proves it). Keeping
# this to a single process is what makes the hook fast enough to sit on every
# PreToolUse/PostToolUse/Stop without being felt.
parsed="$(python3 -c '
import json, sys, shlex, hashlib, re

raw = sys.stdin.read()
try:
    d = json.loads(raw)
    ok = isinstance(d, dict)
except Exception:
    d, ok = {}, False

tool_name = str(d.get("tool_name") or "")
cwd = str(d.get("cwd") or "")
tool_use_id = str(d.get("tool_use_id") or "")
session_id = str(d.get("session_id") or "")
# only a CLI-valid session id is forwarded; anything else = "no session id" (fallback rules)
if not re.match(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$", session_id):
    session_id = ""
stop_hook_active = bool(d.get("stop_hook_active"))

tool_input = d.get("tool_input") or {}
if not isinstance(tool_input, dict):
    tool_input = {}
agent_name = tool_input.get("subagent_type") or tool_input.get("description") or "unnamed"
agent_name = str(agent_name).strip()[:40] or "unnamed"

# posttool: did this Bash call run `eaos task new`, and which id did it print?
command = str(tool_input.get("command") or "")
is_task_new = bool(re.search(r"\beaos\s+task\s+new\b", command))
new_task_id = ""
if is_task_new:
    resp = d.get("tool_response")
    text = resp.get("stdout", "") if isinstance(resp, dict) else resp
    text = text if isinstance(text, str) else json.dumps(resp)
    ids = re.findall(r"^(T-\d+)\s*$", text, re.M)
    if len(ids) == 1:          # exactly one id line, else we do not guess
        new_task_id = ids[0]

# Idempotency key material: the tool_use_id when present (stable across a hook retry
# for the SAME tool call), else a hash of the raw input (best-effort — still collapses
# byte-identical retries of an otherwise unidentified call).
key_src = tool_use_id if tool_use_id else raw
idem_key = "hook:" + hashlib.sha256(key_src.encode("utf-8", "surrogatepass")).hexdigest()

fields = {
    "PARSE_OK": "true" if ok else "false",
    "TOOL_NAME": tool_name,
    "CWD": cwd,
    "SESSION_ID": session_id,
    "AGENT_NAME": agent_name,
    "STOP_HOOK_ACTIVE": "true" if stop_hook_active else "false",
    "IDEM_KEY": idem_key,
    "NEW_TASK_ID": new_task_id,
}
for k, v in fields.items():
    print(f"{k}={shlex.quote(v)}")
' <<<"$stdin_json" 2>/dev/null)" || exit 0

eval "$parsed" || exit 0
[ "${PARSE_OK:-false}" = "true" ] || exit 0

cwd="${CWD:-}"
[ -n "$cwd" ] || cwd="$PWD"
[ -d "$cwd/.eaos" ] || exit 0   # not an EAOS project: nothing to accelerate

lname="$(printf '%s' "${TOOL_NAME:-}" | tr '[:upper:]' '[:lower:]')"

# Session-scoped task resolution (rules: `eaos session resolve`, see header). Any
# non-zero result — no task, ambiguity, lock contention, usage error — means fail open.
resolve_task() {
  if [ -n "${SESSION_ID:-}" ]; then
    (cd "$cwd" 2>/dev/null && python3 "$EAOS_BIN" session resolve --session "$SESSION_ID" 2>/dev/null)
  else
    (cd "$cwd" 2>/dev/null && python3 "$EAOS_BIN" session resolve 2>/dev/null)
  fi
}

case "$mode" in
posttool)
  # Bind this session to the task `eaos task new` just created. PostToolUse can never
  # block, and a failed bind only means the fallback rules apply later.
  [ "$lname" = "bash" ] || exit 0
  [ -n "${NEW_TASK_ID:-}" ] || exit 0
  [ -n "${SESSION_ID:-}" ] || exit 0
  (cd "$cwd" 2>/dev/null && python3 "$EAOS_BIN" session bind "$NEW_TASK_ID" \
     --session "$SESSION_ID" >/dev/null 2>&1)
  exit 0
  ;;
pretool)
  # Case-insensitive match on the agent-launching tool. This is a second, independent
  # check on top of whatever matcher settings.json used to fire this hook in the first
  # place (belt-and-suspenders: harmless if settings.json already narrowed it).
  case "$lname" in
    task|agent) ;;
    *) exit 0 ;;
  esac
  current_task="$(resolve_task)" || exit 0
  [ -n "$current_task" ] || exit 0

  out="$(cd "$cwd" 2>/dev/null && python3 "$EAOS_BIN" spawn "$current_task" \
         --agent "${AGENT_NAME:-unnamed}" --idempotency-key "${IDEM_KEY}" 2>&1)"
  rc=$?
  # Block ONLY on a named policy verdict. rc 4 (lock busy), rc 2 (usage), or an rc 1
  # that does not carry one of the two policy markers all fail open.
  if [ "$rc" -eq 1 ]; then
    case "$out" in
      *"BUDGET EXCEEDED"*|*BLOCKED*)
        printf '%s\n' "$out" >&2
        exit 2 ;;
    esac
  fi
  exit 0
  ;;
stop)
  [ "${STOP_HOOK_ACTIVE:-false}" = "true" ] && exit 0  # prevent a block/retry loop
  current_task="$(resolve_task)" || exit 0
  [ -n "$current_task" ] || exit 0

  out="$(cd "$cwd" 2>/dev/null && python3 "$EAOS_BIN" audit "$current_task" 2>&1)"
  rc=$?
  # rc 1 = the audit COMPLETED and found discrepancies. rc 4 = it could not take its
  # snapshot (lock held elsewhere) — an incomplete audit is not evidence of drift.
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
