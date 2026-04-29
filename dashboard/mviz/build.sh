#!/usr/bin/env bash
# Build the mviz dashboard: generate data then render HTML.
# Usage: bash dashboard/mviz/build.sh
set -euo pipefail

cd "$(dirname "$0")/../.."

echo "==> Generating data files..."
uv run python3 dashboard/mviz/generate_data.py

echo "==> Rendering mviz dashboard..."
npx --yes mviz@1.6.7 dashboard/mviz/dashboard.md -o dashboard/mviz/index.html

echo "==> Done: dashboard/mviz/index.html"
