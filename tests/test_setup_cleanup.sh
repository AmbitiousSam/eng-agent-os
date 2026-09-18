#!/usr/bin/env bash
# test_setup_cleanup.sh — the installer's manifest-based cleanup (v4 review 1, finding 6)
# against a throwaway CLAUDE_HOME: an unmodified legacy file is removed, a customised one
# at a legacy path is quarantined with a manifest, an unknown file is quarantined,
# --dry-run changes nothing, and v4 files land. Exit 0 = pass.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
pass_count=0; fail_count=0
ok()  { pass_count=$((pass_count + 1)); printf "  \033[0;32mok\033[0m  - %s\n" "$*"; }
bad() { fail_count=$((fail_count + 1)); printf "  \033[0;31mFAIL\033[0m - %s\n" "$*"; }
assert_eq() { if [ "$2" = "$3" ]; then ok "$1"; else bad "$1 (expected '$2', got '$3')"; fi; }

HOME_T="$(mktemp -d)"; export CLAUDE_HOME="$HOME_T"
mkdir -p "$HOME_T/agents" "$HOME_T/commands" "$HOME_T/eaos" "$HOME_T/skills/design-review"
# 1. an unmodified v3 persona, exactly as e0-baseline shipped it
git -C "$REPO" show e0-baseline:agents/developer.md > "$HOME_T/agents/developer.md"
# 2. a customised persona at a legacy path
{ git -C "$REPO" show e0-baseline:agents/architect.md; echo "# my local tweak"; } > "$HOME_T/agents/architect.md"
# 3. a file that was never ours, at a name the cleanup targets
echo "custom triage command" > "$HOME_T/commands/triage.md"
# 4. an unmodified skill dir
git -C "$REPO" show e0-baseline:skills/design-review/SKILL.md > "$HOME_T/skills/design-review/SKILL.md"
# 5. an agency persona not in the manifest (content differs)
echo "not the pinned content" > "$HOME_T/agents/agency-foo.md"

echo "=== dry run changes nothing ==="
plan="$(bash "$REPO/setup.sh" --dry-run 2>&1)"; rc=$?
assert_eq "dry run exits 0" "0" "$rc"
case "$plan" in *"would remove"*"developer.md"*) ok "dry run plans removal of the unmodified persona" ;; *) bad "dry run did not plan developer.md removal: $plan" ;; esac
case "$plan" in *"would quarantine"*"architect.md"*) ok "dry run plans quarantine of the customised persona" ;; *) bad "dry run did not plan architect.md quarantine" ;; esac
[ -e "$HOME_T/agents/developer.md" ] && ok "dry run left developer.md in place" || bad "dry run removed a file"
FRESH="$(mktemp -d)"; rmdir "$FRESH"
CLAUDE_HOME="$FRESH" bash "$REPO/setup.sh" --dry-run >/dev/null 2>&1
[ -e "$FRESH" ] && bad "dry run created directories in a fresh CLAUDE_HOME" || ok "dry run creates nothing in a fresh CLAUDE_HOME"
export CLAUDE_HOME="$HOME_T"

echo "=== real run ==="
bash "$REPO/setup.sh" >/tmp/eaos_setup_test.$$ 2>&1; rc=$?
assert_eq "setup exits 0" "0" "$rc"
[ -e "$HOME_T/agents/developer.md" ] && bad "unmodified persona still present" || ok "unmodified persona removed"
[ -e "$HOME_T/skills/design-review" ] && bad "unmodified skill dir still present" || ok "unmodified skill dir removed"
q="$(ls -d "$HOME_T"/eaos/quarantine/* 2>/dev/null | head -1)"
[ -n "$q" ] && ok "quarantine directory created: $(basename "$q")" || bad "no quarantine directory"
[ -f "$q/agents/architect.md" ] && grep -q "my local tweak" "$q/agents/architect.md" && ok "customised persona quarantined intact" || bad "customised persona not quarantined intact"
[ -f "$q/commands/triage.md" ] && ok "unknown file quarantined, not deleted" || bad "unknown triage.md was not quarantined"
[ -f "$q/agents/agency-foo.md" ] && ok "unlisted agency file quarantined" || bad "unlisted agency file not quarantined"
grep -q "agents/architect.md" "$q/MANIFEST.txt" 2>/dev/null && ok "quarantine MANIFEST lists moved files" || bad "quarantine MANIFEST missing entries"
[ -e "$HOME_T/agents/architect.md" ] && bad "customised persona still at legacy path" || ok "legacy path cleared"
for f in commands/agentic-os.md agents/eaos-builder.md agents/eaos-checker.md agents/eaos-reader.md eaos/bin/eaos eaos/routing.yaml; do
  [ -e "$HOME_T/$f" ] && ok "installed: $f" || bad "missing after install: $f"
done
n_cl="$(ls "$HOME_T/eaos/checklists"/*.md 2>/dev/null | wc -l | tr -d ' ')"
assert_eq "11 checklists installed" "11" "$n_cl"
echo "=== second run is a no-op ==="
before="$(find "$HOME_T" -type f | wc -l | tr -d ' ')"
bash "$REPO/setup.sh" >/dev/null 2>&1
after="$(find "$HOME_T" -type f | wc -l | tr -d ' ')"
assert_eq "re-run adds or removes nothing" "$before" "$after"

rm -rf "$HOME_T" /tmp/eaos_setup_test.$$
echo "$pass_count passed, $fail_count failed"
[ "$fail_count" -eq 0 ]
