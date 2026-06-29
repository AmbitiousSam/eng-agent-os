#!/usr/bin/env bash
# Enable the EAOS git hooks (currently: pre-push validation gate).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "Not a git repo."; exit 1; }
chmod +x .githooks/* 2>/dev/null || true
git config core.hooksPath .githooks
echo "Hooks enabled (core.hooksPath = .githooks). 'git push' now runs validation first."
echo "Bypass in an emergency with: git push --no-verify"
