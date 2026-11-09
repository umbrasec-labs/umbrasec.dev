#!/usr/bin/env bash
# Build assets/tailwind.css, the site's only Tailwind output (no Play CDN, no
# build step on Cloudflare Pages: the committed file is what ships).
#
#   build.sh                   rebuild it from the working tree
#   build.sh --check           fail if it is stale against the working tree (CI)
#   build.sh --check --staged  fail if it is stale against what is staged (pre-commit)
#
# Needs the pinned CLI from package.json: npm ci (or npm install) first.
# A page or script that gains a new class needs a rebuild in the same commit,
# or that class ships with no styles. Content paths: tailwind.config.cjs.

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TW="$REPO/node_modules/.bin/tailwindcss"
CFG=tools/site-build/tailwind/tailwind.config.cjs
IN=tools/site-build/tailwind/input.css
OUT=assets/tailwind.css

check=0 staged=0
for arg in "$@"; do
  case "$arg" in
    --check) check=1 ;;
    --staged) staged=1 ;;
    *) echo "build.sh: unknown argument $arg" >&2; exit 2 ;;
  esac
done

[ -x "$TW" ] || { echo "build.sh: $TW missing; run npm ci first" >&2; exit 2; }

build() { # $1 = source root, $2 = output file
  (cd "$1" && "$TW" -c "$CFG" -i "$IN" -o "$2" --minify 2>/dev/null)
}

if [ "$check" = 0 ]; then
  build "$REPO" "$REPO/$OUT"
  echo "build.sh: wrote $OUT ($(wc -c < "$REPO/$OUT") bytes)"
  exit 0
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
src="$REPO"
if [ "$staged" = 1 ]; then
  # Copy the staged versions of every file the build reads, so unstaged edits
  # can neither hide a stale CSS file nor fail a commit that is fine.
  src="$tmp/src"
  mkdir -p "$src"
  git -C "$REPO" ls-files -z -- '*.html' 'assets/*.js' 'functions/*' 'tools/site-build/tailwind/*' "$OUT" \
    | git -C "$REPO" checkout-index -z --stdin --prefix="$src/"
fi
build "$src" "$tmp/fresh.css"
if ! cmp -s "$tmp/fresh.css" "$src/$OUT"; then
  echo "build.sh: $OUT is stale: a class was added or removed in the pages or scripts." >&2
  echo "build.sh: run npm run build:css and commit $OUT with the change." >&2
  exit 1
fi
echo "build.sh: $OUT is up to date"
