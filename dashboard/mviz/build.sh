#!/usr/bin/env bash
# Build the mviz dashboard: generate data then render HTML.
# Usage: bash dashboard/build_mviz.sh
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> Generating data files..."
uv run python dashboard/generate_data.py

echo "==> Rendering mviz dashboard..."
npx mviz dashboard/mviz_dashboard.md -o dashboard/mviz.html

echo "==> Done: dashboard/mviz.html"
