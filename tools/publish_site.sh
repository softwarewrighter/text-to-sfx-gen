#!/usr/bin/env bash
# Publish site/ to the gh-pages branch (run tools/build_site.sh first).
# GitHub Pages must be set to deploy from the gh-pages branch, root folder.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
[ -f site/index.html ] || { echo "Run tools/build_site.sh first"; exit 1; }
if find site -name '*_ref.wav' | grep -q .; then
  echo "ERROR: reference audio in site/; refusing to publish"; exit 1
fi

WORKTREE="$(mktemp -d)"
trap 'git worktree remove --force "$WORKTREE" 2>/dev/null || true' EXIT
if git ls-remote --exit-code --heads origin gh-pages > /dev/null; then
  git fetch origin gh-pages
  git worktree add "$WORKTREE" origin/gh-pages --detach
else
  git worktree add --detach "$WORKTREE"
  git -C "$WORKTREE" checkout --orphan gh-pages-new
  git -C "$WORKTREE" rm -rf --quiet .
fi
find "$WORKTREE" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
cp -R site/. "$WORKTREE/"
git -C "$WORKTREE" add -A
git -C "$WORKTREE" commit -m "Publish demo site from $(git rev-parse --short HEAD)"
git -C "$WORKTREE" push origin HEAD:gh-pages
echo "Pushed. Site: https://softwarewrighter.github.io/text-to-sfx-gen/"
