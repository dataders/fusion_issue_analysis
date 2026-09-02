#!/usr/bin/env bash
# Build the materialized serving DB that dbt charts renders from.
#
# Why: `dct render` opens DuckDB read-only and forces enable_external_access=off,
# so it cannot follow the dev-target views that read raw parquet. We snapshot
# every model in the dev DB (which DOES read parquet, under the plain duckdb CLI)
# into base tables in a standalone file the renderer can open safely.
#
# Run from repo root. Defaults to the local db; pass --source md:fusion_issues
# (with MOTHERDUCK_TOKEN set) to snapshot production models.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
exec uv run python scripts/build_dbt_charts_db.py "$@"
