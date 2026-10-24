#!/usr/bin/env bash
# Deploy umbrasec.dev to Cloudflare Pages by hand. The repo lives at
# github.com/umbrasec-labs/umbrasec.dev. Pages' Git integration builds every
# push to master with tools/local-deploy/stage.sh; this script is the by-hand
# fallback for that build.
#
# What it does:
#  - runs stage.sh, which stages "git archive HEAD" (so ONLY committed files can
#    ever ship) and strips repo plumbing (CI config, package manifests, README),
#    so the public site is site content and nothing else.
#  - uploads the staging copy to the "umbrasec-dev" Pages project on branch master.
#  - ships functions/ (Cloudflare Pages Functions, e.g. /api/kev) from that same
#    staging copy, so a function, like a page, only goes live once committed.
#
# Local preview with the function running:  npx wrangler pages dev .
#
# Usage:
#   tools/local-deploy/deploy.sh              # stage, trim, deploy
#   tools/local-deploy/deploy.sh --dry-run    # stage and trim, print the tree, stop
#
# Requires Node 22+ (wrangler 4 refuses older) and a logged-in wrangler
# (`npx wrangler login`). Wrangler is pinned in package.json, so npx uses the
# local copy in node_modules rather than downloading one.
#
# Needs outbound access to api.cloudflare.com. Telemetry and the log path are
# pinned below so the script runs clean from cron or a restricted shell.

set -euo pipefail

PROJECT="umbrasec-dev"
BRANCH="master"

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO"

DRY_RUN=0
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1

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

# wrangler writes a log file per run, defaulting to ~/.config/.wrangler/logs.
# That path is not writable everywhere this runs - a locked-down cron user or a
# sandboxed shell - and wrangler treats the failed write as a fatal error, so a
# perfectly good deploy dies on a log file nobody reads. Send logs somewhere
# writable instead. Respect the caller's choice if they already set one.
export WRANGLER_LOG_PATH="${WRANGLER_LOG_PATH:-${TMPDIR:-/tmp}/wrangler-logs/}"

# No telemetry from an unattended deploy: it dials sparrow.cloudflare.com, which
# is one more host to allow through a firewall and one more thing to hang on.
export WRANGLER_SEND_METRICS="${WRANGLER_SEND_METRICS:-false}"

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

bash "$REPO/tools/local-deploy/stage.sh" "$STAGE"

if [ "$DRY_RUN" -eq 1 ]; then
  echo "deploy: --dry-run, not uploading. Staging tree:"
  (cd "$STAGE" && find . -type f | sed 's#^\./#  #' | sort)
  exit 0
fi

# wrangler compiles Pages Functions from "<cwd>/functions", NOT from the deploy
# directory, so it must run from inside the staging copy. Run from the repo root
# it would ship the working-tree functions/ (uncommitted edits included) with a
# committed set of pages. The local binary is addressed by path because npx
# resolves from cwd and would not find node_modules from inside the temp dir.
# Git metadata is passed explicitly for the same reason: the staging copy is not
# a repository, so wrangler cannot read it there. The equals form matters: a
# commit subject that starts with "-" would otherwise be parsed as flags and
# abort the deploy.
WRANGLER="$REPO/node_modules/.bin/wrangler"
[ -x "$WRANGLER" ] || die "wrangler not installed in node_modules; run: npm ci"
head_sha="$(git rev-parse HEAD)"
head_msg="$(git log -1 --format=%s)"
(
  cd "$STAGE"
  "$WRANGLER" pages deploy . \
    --project-name "$PROJECT" \
    --branch "$BRANCH" \
    --commit-hash="$head_sha" \
    --commit-message="$head_msg" \
    --commit-dirty=false
)

echo "deploy: done. Verify with: curl -sI https://umbrasec.dev/  and  curl -sI https://umbrasec.dev/api/kev"
