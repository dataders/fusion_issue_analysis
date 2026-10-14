#!/usr/bin/env bash
# Snapshot every dashboard model into data/serve/fusion_issues.duckdb.
# Defaults to the local dev DB; pass --source md:fusion_issues (with
# MOTHERDUCK_TOKEN set) to snapshot production. See snapshot_dashboard_db.py.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
exec uv run python scripts/snapshot_dashboard_db.py "$@"
