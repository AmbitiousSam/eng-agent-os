#!/usr/bin/env bash
# Install a CODE-CHECK pre-push hook into YOUR project (the resume builder, etc.).
# It blocks `git push` unless the project's own test / build / lint pass.
# Run this from inside the project you want to protect:
#     ~/Downloads/eng-agent-os/scripts/install-project-checks.sh
#
# Check resolution order:
#   1) .eaos/checks.sh           (your explicit checks — preferred; edit it to taste)
#   2) auto-detected per stack    (npm / pnpm / yarn, pytest, make, cargo, go)
set -euo pipefail

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "Not inside a git repo."; exit 1; }
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
mkdir -p .git/hooks .eaos

# Seed an editable checks script if none exists, with a detected default.
if [ ! -f .eaos/checks.sh ]; then
  detect=""
  if [ -f package.json ]; then
    pm="npm"; [ -f pnpm-lock.yaml ] && pm="pnpm"; [ -f yarn.lock ] && pm="yarn"
    grep -q '"test"'  package.json && detect+="$pm run test --if-present || $pm test || exit 1\n"
    grep -q '"lint"'  package.json && detect+="$pm run lint --if-present\n"
    grep -q '"build"' package.json && detect+="$pm run build --if-present\n"
  elif [ -f pyproject.toml ] || [ -f setup.cfg ] || ls tests test 2>/dev/null | grep -q .; then
    detect+="pytest -q\n"; command -v ruff >/dev/null 2>&1 && detect+="ruff check .\n"
  elif [ -f Makefile ]; then
    grep -qE '^test:'  Makefile && detect+="make test\n"
    grep -qE '^lint:'  Makefile && detect+="make lint\n"
    grep -qE '^build:' Makefile && detect+="make build\n"
  elif [ -f Cargo.toml ]; then
    detect+="cargo test\ncargo clippy -- -D warnings\n"
  elif ls go.mod >/dev/null 2>&1; then
    detect+="go test ./...\ngo vet ./...\n"
  fi
  [ -z "$detect" ] && detect="echo 'No checks detected — edit .eaos/checks.sh to add your test/build/lint.'\n"
  {
    echo "#!/usr/bin/env bash"
    echo "# Project code checks run before every push. Edit freely. Non-zero exit blocks the push."
    echo "set -e"
    printf "%b" "$detect"
  } > .eaos/checks.sh
  chmod +x .eaos/checks.sh
  echo "Created .eaos/checks.sh (review/edit it):"
  sed 's/^/    /' .eaos/checks.sh
fi

cat > .git/hooks/pre-push <<'HOOK'
#!/usr/bin/env bash
# EAOS code-check gate — push only after the project's checks pass.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
printf "\033[1;36m[code-check]\033[0m running project checks before push...\n"
if [ -x .eaos/checks.sh ] || [ -f .eaos/checks.sh ]; then
  if bash .eaos/checks.sh; then
    printf "\033[0;32m[code-check] passed — pushing.\033[0m\n"; exit 0
  else
    printf "\033[1;31m[code-check] FAILED — push aborted.\033[0m Fix the code, then push again.\n"
    printf "            (Emergency bypass: git push --no-verify)\n"; exit 1
  fi
else
  printf "\033[1;33m[code-check]\033[0m no .eaos/checks.sh — skipping (run install-project-checks.sh).\n"; exit 0
fi
HOOK
chmod +x .git/hooks/pre-push

echo
echo "Installed code-check pre-push hook in: $ROOT/.git/hooks/pre-push"
echo "Every 'git push' now runs .eaos/checks.sh first and blocks on failure."
echo "Tip: add '.eaos/' to this project's .gitignore."
