#!/usr/bin/env bash
# Create the GitHub repo and push this code — run from the eng-agent-os/ directory
# on YOUR machine, where `gh` is already authenticated (`gh auth login`).
#
#   cd eng-agent-os
#   ./scripts/push-to-github.sh                 # public repo named "eng-agent-os"
#   ./scripts/push-to-github.sh my-name private # custom name + visibility
set -euo pipefail

REPO_NAME="${1:-eng-agent-os}"
VISIBILITY="${2:-public}"          # public | private

say() { printf "\033[1;36m[push]\033[0m %s\n" "$*"; }
die() { printf "\033[1;31m[push] %s\033[0m\n" "$*" >&2; exit 1; }

# Run from the repo root (the dir that holds README.md + setup.sh).
cd "$(dirname "${BASH_SOURCE[0]}")/.."

command -v git >/dev/null || die "git not found."
command -v gh  >/dev/null || die "GitHub CLI 'gh' not found. Install: https://cli.github.com"
gh auth status >/dev/null 2>&1 || die "gh is not logged in. Run: gh auth login"

[ "$VISIBILITY" = "public" ] || [ "$VISIBILITY" = "private" ] || die "visibility must be public|private"

# Initialize git if needed.
if [ ! -d .git ]; then
  say "Initializing git repo..."
  git init -q
  git branch -M main
fi

say "Staging and committing..."
git add -A
git diff --cached --quiet 2>/dev/null && say "(nothing new to commit)" || \
  git commit -q -m "Engineering Agentic OS: initial commit"

# Determine the owner for a friendly message.
OWNER="$(gh api user --jq .login 2>/dev/null || echo '<you>')"

if gh repo view "$OWNER/$REPO_NAME" >/dev/null 2>&1; then
  say "Repo $OWNER/$REPO_NAME already exists — pushing to it."
  git remote get-url origin >/dev/null 2>&1 || \
    git remote add origin "https://github.com/$OWNER/$REPO_NAME.git"
  git push -u origin main
else
  say "Creating $VISIBILITY repo $OWNER/$REPO_NAME and pushing..."
  gh repo create "$REPO_NAME" "--$VISIBILITY" --source=. --remote=origin --push \
    --description "An agentic engineering OS: a collaborating AI agent team driven by /agentic-os"
fi

say "Done → https://github.com/$OWNER/$REPO_NAME"
