#!/bin/bash
# Genera ed aggiorna la snake animation per il profilo GitHub @ciroautuori
# SENZA dipendere da GitHub Actions cloud.

set -e

USERNAME="${1:-ciroautuori}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

echo "🐍 Generazione Snake Animation per @$USERNAME via Docker..."

mkdir -p dist

# Generate light SVG
docker run --rm \
  -v "$REPO_DIR":/github/workspace \
  -e GITHUB_WORKSPACE=/github/workspace \
  -e INPUT_GITHUB_USER_NAME="$USERNAME" \
  -e "INPUT_SVG_OUT_PATH=/github/workspace/dist/github-contribution-grid-snake.svg" \
  platane/snk

# Generate dark SVG
docker run --rm \
  -v "$REPO_DIR":/github/workspace \
  -e GITHUB_WORKSPACE=/github/workspace \
  -e INPUT_GITHUB_USER_NAME="$USERNAME" \
  -e "INPUT_PALETTE=github-dark" \
  -e "INPUT_SVG_OUT_PATH=/github/workspace/dist/github-contribution-grid-snake-dark.svg" \
  platane/snk

echo "✅ File SVG generati in dist/"

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Clean up stale output branch if exists locally
git checkout -B output
git rm -rf . > /dev/null 2>&1 || true
cp dist/github-contribution-grid-snake*.svg .
git add github-contribution-grid-snake*.svg
git commit -m "chore(snake): update contribution snake animation"
git push origin output --force

# Restore original branch
git checkout "$CURRENT_BRANCH"

echo "🎉 Snake animation aggiornata con successo sul branch 'output'!"
