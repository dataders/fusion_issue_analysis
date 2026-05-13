#!/usr/bin/env bash
# Local dev server: injects MOTHERDUCK_READ_TOKEN from .env.local into live tabs,
# serves with COOP/COEP headers, and restores placeholders on exit.
set -euo pipefail

# Load .env.local
if [ -f .env.local ]; then
  export $(grep -v '^#' .env.local | grep '=' | xargs)
fi

LIVE_FILES=(
  "dashboard/duckdb-wasm/index.html"
  "dashboard/mosaic/index.html"
)

# Build Observable live page if dist doesn't exist yet
if [ ! -f "dashboard/observable/dist/live.html" ]; then
  echo "Building Observable (first run)..."
  npm run build:observable
fi
LIVE_FILES+=("dashboard/observable/dist/live.html")

# Inject token and register cleanup to restore placeholder on exit
if [ -n "${MOTHERDUCK_READ_TOKEN:-}" ]; then
  for f in "${LIVE_FILES[@]}"; do
    sed -i '' "s|__MOTHERDUCK_READ_TOKEN__|${MOTHERDUCK_READ_TOKEN}|g" "$f"
  done
  echo "Token injected into live tabs ✓"

  cleanup() {
    for f in "${LIVE_FILES[@]}"; do
      sed -i '' "s|${MOTHERDUCK_READ_TOKEN}|__MOTHERDUCK_READ_TOKEN__|g" "$f" 2>/dev/null || true
    done
    echo "Placeholder restored — safe to commit."
  }
  trap cleanup EXIT INT TERM
else
  echo "⚠️  MOTHERDUCK_READ_TOKEN not set — live tabs will show 'Token not injected'"
  echo "   Add it to .env.local: MOTHERDUCK_READ_TOKEN=your_token_here"
fi

echo "Serving at http://127.0.0.1:9321"
uv run python3 dashboard/serve_local.py
