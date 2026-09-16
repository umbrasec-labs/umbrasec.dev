#!/usr/bin/env bash
# Deploy umbrasec.dev to Cloudflare Pages by hand. There is no CI for this site
# on purpose - the GitHub repo that used to drive Pages' Git integration is gone,
# and Pages cannot connect to Codeberg, so every deploy is a deliberate local act.
#
# What it does:
#  - stages "git archive HEAD", so ONLY committed files can ever ship. A stray
#    file in the working tree cannot leak onto the public site.
#  - strips repo plumbing (CI config, package manifests, README) from the staging
#    copy, so the public site is site content and nothing else.
#  - uploads the staging copy to the "umbrasec" Pages project on branch master.
#
# Usage:
#   tools/local-deploy/deploy.sh              # stage, trim, deploy
#   tools/local-deploy/deploy.sh --dry-run    # stage and trim, print the tree, stop
#
# Requires Node 22+ (wrangler 4 refuses older) and a logged-in wrangler
# (`npx wrangler login`). Wrangler is pinned in package.json, so npx uses the
# local copy in node_modules rather than downloading one.

set -euo pipefail

PROJECT="umbrasec"
BRANCH="master"

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO"

DRY_RUN=0
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1

# Repo plumbing that should never be served from umbrasec.dev. Paths are
# relative to the staging root. Deleting from the staging copy leaves the real
# working tree untouched.
TRIM=(
  ".githooks"
  ".gitignore"
  "README.md"
  "package.json"
  "package-lock.json"
  "tools/local-deploy"
  "tools/local-sync"
  "tools/site-build"
)

die() { echo "deploy: $*" >&2; exit 1; }

# nvm installs Node outside the default PATH, and this script is often run from
# cron or a non-interactive shell that never sourced it. Load it on demand.
if ! command -v node >/dev/null 2>&1 || [ "$(node -v | sed 's/^v\([0-9]*\).*/\1/')" -lt 22 ]; then
  # shellcheck disable=SC1090
  [ -s "$HOME/.nvm/nvm.sh" ] && . "$HOME/.nvm/nvm.sh"
fi
command -v node >/dev/null 2>&1 || die "node not found. Install Node 22+ (nvm install 22)."
node_major="$(node -v | sed 's/^v\([0-9]*\).*/\1/')"
[ "$node_major" -ge 22 ] || die "node $(node -v) is too old; wrangler needs 22+. Try: nvm use 22"

branch="$(git rev-parse --abbrev-ref HEAD)"
[ "$branch" = "$BRANCH" ] || echo "deploy: WARNING on branch '$branch', but deploying as '$BRANCH' (production)."

# git archive only ever sees committed content, so anything uncommitted is NOT
# what goes live. Untracked files matter as much as modified ones here: a new
# page you forgot to commit is silently missing from the upload, with no error.
if [ -n "$(git status --porcelain)" ]; then
  echo "deploy: WARNING these changes are NOT in HEAD and will NOT be deployed:"
  git status --short | sed 's/^/  /'
  echo "deploy: deploying HEAD ($(git rev-parse --short HEAD)) as-is."
fi

STAGE="$(mktemp -d "${TMPDIR:-/tmp}/umbrasec-deploy.XXXXXX")"
trap 'rm -rf "$STAGE"' EXIT

git archive HEAD | tar -x -C "$STAGE"
staged=$(find "$STAGE" -type f | wc -l)

for path in "${TRIM[@]}"; do
  rm -rf "${STAGE:?}/$path"
done
deployed=$(find "$STAGE" -type f | wc -l)

echo "deploy: HEAD $(git rev-parse --short HEAD), $staged tracked -> $deployed deployed ($((staged - deployed)) trimmed)"

if [ "$DRY_RUN" -eq 1 ]; then
  echo "deploy: --dry-run, not uploading. Staging tree:"
  (cd "$STAGE" && find . -type f | sed 's#^\./#  #' | sort)
  exit 0
fi

npx wrangler pages deploy "$STAGE" \
  --project-name "$PROJECT" \
  --branch "$BRANCH" \
  --commit-dirty=true

echo "deploy: done. Verify with: curl -sI https://umbrasec.dev/"
