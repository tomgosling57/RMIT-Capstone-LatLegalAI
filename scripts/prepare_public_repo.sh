#!/usr/bin/env bash
# Rebuild this repo as a single clean git commit for publishing.
# Run from the repo root, with no need for a venv.
#
# What it does:
#   1. Tars the current .git to a timestamped backup outside the repo.
#   2. Replaces .git with a brand-new repository.
#   3. Commits the working tree once with a neutral identity and date.
#   4. Points origin at the new repo and verifies nothing sensitive survived.
#      Patterns come from .private/publish-blocklist.txt (git-ignored, never committed).
set -euo pipefail

cd "$(dirname "$0")/.."
REPO_ROOT="$(pwd)"
STAMP="$(date +%Y%m%d-%H%M%S)"
NEW_ORIGIN="${NEW_ORIGIN:-https://github.com/YOUR-ORG/RMIT-Capstone-LatMatrix.git}"

if [[ ! -d .git ]]; then
    echo "error: no .git directory here ($REPO_ROOT)" >&2
    exit 1
fi

# Prefer a backup outside the repo; fall back to inside it if the sandbox blocks $HOME.
BACKUP="${HOME}/RMIT-Capstone-LatMatrix.git-backup-${STAMP}.tar.gz"
if ! tar -czf "$BACKUP" .git 2>/dev/null; then
    BACKUP=".git-backup-${STAMP}.tar.gz"
    tar -czf "$BACKUP" .git
fi
echo "==> backed up .git to $BACKUP"

if [[ -n "$(git status --porcelain --untracked-files=normal)" ]]; then
    echo "note: there are uncommitted changes; they will be captured in the new initial commit."
fi

echo "==> rebuilding .git"
rm -rf .git
git init -q -b main
git config user.name "LatLegal Team"
git config user.email "latilegal-team@users.noreply.github.com"
git config commit.gpgsign false
git add -A
git -c user.name="LatLegal Team" \
    -c user.email="latilegal-team@users.noreply.github.com" \
    commit -q -m "Initial public release of LatLegal AI (RMIT capstone project)" \
    --date="2026-11-25T12:00:00+1100"

git remote add origin "$NEW_ORIGIN"

echo "==> verifying"
git log --format='%h %an <%ae> %ad %s' --date=short
echo "commits: $(git rev-list --count HEAD)"
echo "tracked files: $(git ls-files | wc -l)"
echo "HEAD signature: $(git cat-file -p HEAD | head -3 | tr '\n' ' ')"

PATTERN_FILE=".private/publish-blocklist.txt"
if [[ ! -f "$PATTERN_FILE" ]]; then
    echo "warning: $PATTERN_FILE missing; skipping content verification." >&2
    exit 0
fi
forbidden="$(grep -vE '^\s*(#|$)' "$PATTERN_FILE" | paste -sd'|' -)"

leftovers="$(git grep -IEn "$forbidden" -- . || true)"
if [[ -n "$leftovers" ]]; then
    echo "WARNING: forbidden patterns still present:" >&2
    echo "$leftovers" >&2
else
    echo "no forbidden patterns in the new history."
fi

echo "checking all blobs (this can take a few seconds)..."
git rev-list --objects --all | awk '{print $1}' | git cat-file --batch-check='%(objecttype) %(objectname)' \
    | awk '$1=="blob"{print $2}' | git cat-file --batch \
    | grep -aoE "$forbidden" | sort -u | sed 's/^/  still present: /' || true

echo
echo "Done. Backup of the old history: $BACKUP"
echo "Review 'git status' and 'git log', then push with:"
echo "  git push -u origin main"
