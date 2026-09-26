#!/usr/bin/env bash
# Block until no "Extract GitHub Issues" run is in flight. Its dbt build
# rebuilds the MotherDuck tables, and a dashboard build that reads them
# mid-swap fails with "table does not exist". Needs GH_TOKEN with actions:read.
set -euo pipefail

timeout_s="${1:-1800}"
waited=0
while :; do
  running=$(gh run list --repo "$GITHUB_REPOSITORY" --workflow extract.yml --limit 20 \
    --json status --jq '[.[] | select(.status == "in_progress" or .status == "queued")] | length')
  if [ "$running" = "0" ]; then
    exit 0
  fi
  if [ "$waited" -ge "$timeout_s" ]; then
    echo "::warning::Extract still running after ${timeout_s}s; building anyway."
    exit 0
  fi
  echo "Extract run in progress; waiting for MotherDuck tables to settle (${waited}s)..."
  sleep 30
  waited=$((waited + 30))
done
