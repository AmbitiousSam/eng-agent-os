#!/usr/bin/env bash
# The whole local gate. The pre-push hook runs exactly this.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
fail=0
while IFS= read -r -d '' s; do bash -n "$s" || { echo "syntax error: $s"; fail=1; }; done \
  < <(find . -type f \( -name '*.sh' -o -path './.githooks/*' \) -not -path './.git/*' -not -path './.e0-worktree/*' -print0)
python3 tests/validate-eaos.py | tail -1 || fail=1
python3 tests/test_eaos.py 2>&1 | tail -1; [ "${PIPESTATUS[0]}" -eq 0 ] || fail=1
bash tests/test_eaos_hooks.sh | tail -1;  [ "${PIPESTATUS[0]}" -eq 0 ] || fail=1
bash tests/test_setup_cleanup.sh | tail -1; [ "${PIPESTATUS[0]}" -eq 0 ] || fail=1
[ "$fail" -eq 0 ] && echo "ALL GATES PASSED" || { echo "GATES FAILED"; exit 1; }
