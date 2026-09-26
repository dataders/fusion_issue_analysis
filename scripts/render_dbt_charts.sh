#!/usr/bin/env bash
# Render the dbt Charts dashboard in light and dark variants.
#
#   scripts/render_dbt_charts.sh [output_dir]   (default: dashboard/dbt-charts)
#
# dct output is always one fixed theme and never follows prefers-color-scheme,
# so we render both themes and let dashboard/dbt-charts/fusion-issue-health.html
# (a checked-in switcher) pick one. Each render declares its color scheme so a
# browser's forced-dark mode doesn't repaint it (dark SVG text on a darkened
# background is unreadable). Reads the snapshot at data/serve/fusion_issues.duckdb
# (scripts/snapshot_dashboard_db.sh).
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUT=$(cd "$ROOT" && mkdir -p "${1:-dashboard/dbt-charts}" && cd "${1:-dashboard/dbt-charts}" && pwd)

cd "$ROOT/transform"
uv run dct validate charts/fusion-issue-health.yml --strict
uv run dct validate charts/fusion-issue-health-dark.yml --strict

render() {  # <board> <output file> <color-scheme>
  uv run dct render "charts/$1" --format html --output "$OUT/$2"
  sed -i.bak "s|<head>|<head><meta name=\"color-scheme\" content=\"$3\">|" "$OUT/$2"
  rm -f "$OUT/$2.bak"
}
render fusion-issue-health.yml fusion-issue-health-light.html "only light"
render fusion-issue-health-dark.yml fusion-issue-health-dark.html "only dark"

# The switcher lives next to the renders; copy it when rendering elsewhere (PR previews).
if [ "$OUT" != "$ROOT/dashboard/dbt-charts" ]; then
  cp "$ROOT/dashboard/dbt-charts/fusion-issue-health.html" "$OUT/"
fi
