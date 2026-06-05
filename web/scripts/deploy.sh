#!/usr/bin/env bash
# Manual deploy to production. Always run this instead of bare `vercel deploy`.
# Ensures NEXT_PUBLIC_BASE_PATH is set so CSS/JS assets load correctly.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEB_DIR="$(dirname "$SCRIPT_DIR")"

echo "Building... (from $WEB_DIR)"
cd "$WEB_DIR"  # vercel build must run from the directory with .vercel/project.json
NEXT_PUBLIC_BASE_PATH=/digest \
  NEXT_PUBLIC_ASSET_PREFIX=https://cz-psp-videoarchive-michalskops-projects.vercel.app \
  vercel build --prod

echo "Deploying..."
vercel deploy --prebuilt --prod --archive=tgz

echo "Running smoke test..."
bash "$SCRIPT_DIR/smoke-test.sh"
