#!/usr/bin/env bash
# Stage the public site into a directory: committed files only, repo plumbing
# removed. This is the single source of truth for what umbrasec.dev serves.
#
# Used two ways:
#  - by tools/local-deploy/deploy.sh, which stages into a temp dir and uploads it
#  - as the Cloudflare Pages build command (Git integration), staging into dist/:
#      bash tools/local-deploy/stage.sh dist
#
# "git archive HEAD" means only committed content can ship. A stray file in the
# working tree (or node_modules in the Pages build clone) never reaches the site.
#
# functions/ is kept in the staged copy so deploy.sh can compile it from there.
# The Pages Git build compiles functions/ from the repo root instead, so the
# copy in dist/ is simply ignored there.
#
# Usage:
#   tools/local-deploy/stage.sh <out-dir>    # out-dir must be empty or absent

set -euo pipefail

# Repo plumbing that should never be served from umbrasec.dev. Paths are
# relative to the staging root. Deleting from the staging copy leaves the real
# working tree untouched.
TRIM=(
  ".githooks"
  ".github"
  ".gitignore"
  ".gitleaks.toml"
  "CLAUDE.md"
  "README.md"
  "package.json"
  "package-lock.json"
  "tools/local-deploy"
  "tools/local-sync"
  "tools/site-build"
  "research/articles.json"
)

die() { echo "stage: $*" >&2; exit 1; }

OUT="${1:-}"
[ -n "$OUT" ] || die "usage: stage.sh <out-dir>"

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
mkdir -p "$OUT"
OUT="$(cd "$OUT" && pwd)"
[ -z "$(ls -A "$OUT")" ] || die "$OUT is not empty"

git -C "$REPO" archive HEAD | tar -x -C "$OUT"
staged=$(find "$OUT" -type f | wc -l)

for path in "${TRIM[@]}"; do
  rm -rf "${OUT:?}/$path"
done
deployed=$(find "$OUT" -type f | wc -l)

echo "stage: HEAD $(git -C "$REPO" rev-parse --short HEAD), $staged tracked -> $deployed staged ($((staged - deployed)) trimmed) in $OUT"
