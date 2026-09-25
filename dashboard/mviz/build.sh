#!/usr/bin/env bash
# Build the mviz dashboard: generate specs + palette theme, then render HTML.
# Usage: bash dashboard/mviz/build.sh   (same steps as `npm run build:mviz`)
set -euo pipefail

cd "$(dirname "$0")/../.."

echo "==> Generating data files..."
uv run python dashboard/mviz/generate_data.py

echo "==> Rendering mviz dashboard..."
npx --yes --prefer-offline mviz@1.6.7 --theme dashboard/mviz/data/theme.yaml dashboard/mviz/dashboard.md -o dashboard/mviz/index.html

echo "==> Done: dashboard/mviz/index.html"
