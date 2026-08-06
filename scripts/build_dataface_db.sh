#!/usr/bin/env bash
# Build the materialized serving DB that dataface renders from.
#
# Why: `dft render` opens DuckDB read-only and forces enable_external_access=off,
# so it cannot follow the dev-target views that read raw parquet. We snapshot
# every model in the dev DB (which DOES read parquet, under the plain duckdb CLI)
# into base tables in a standalone file the renderer can open safely.
#
# Run from repo root. Requires data/fusion_issues.duckdb + data/raw parquet.
set -euo pipefail
cd "$(dirname "$0")/../transform"

# The face qualifies tables as `fusion_issues.main.<table>`. DuckDB derives the
# catalog name from the file stem, so the serving DB must be named
# `fusion_issues.duckdb` (in its own dir, to avoid clashing with the dev DB).
SRC=../data/fusion_issues.duckdb
OUT=../data/serve/fusion_issues.duckdb

mkdir -p ../data/serve
[ -f "$OUT" ] && trash "$OUT"

# Open the dev DB as the PRIMARY connection so its views resolve normally
# (against parquet, with internal `main.<model>` refs pointing at each other).
# Attach the empty output DB and copy each model in as a base table.
CTAS=$(duckdb "$SRC" -list \
  "select 'CREATE TABLE serve.main.'||table_name||' AS SELECT * FROM main.'||table_name||';'
     from information_schema.tables where table_schema='main' order by table_name" \
  | tail -n +2)

{
  echo "ATTACH '$OUT' AS serve;"
  echo "CREATE SCHEMA IF NOT EXISTS serve.main;"
  echo "$CTAS"
} | duckdb "$SRC"

echo "Built $OUT with $(duckdb "$OUT" -list -noheader \
  "select count(*) from information_schema.tables where table_schema='main'") tables."
