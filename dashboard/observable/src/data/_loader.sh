#!/usr/bin/env bash
# Shared helper: run a named query against DuckDB/MotherDuck and emit JSON.
# Usage: _loader.sh <query_name> [--first-row]
#   --first-row  emit first row as a JSON object instead of an array
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
QUERY_NAME="$1"
FIRST_ROW="${2:-}"

uv --directory "$REPO_ROOT" run python3 - <<PYEOF
import sys, json, duckdb, os
REPO_ROOT = "$REPO_ROOT"
QUERY_NAME = "$QUERY_NAME"
FIRST_ROW = "$FIRST_ROW" == "--first-row"

if os.environ.get("MOTHERDUCK_TOKEN"):
    DB_PATH = "md:fusion_issues"
    con = duckdb.connect(DB_PATH)
else:
    DB_PATH = f"{REPO_ROOT}/data/fusion_issues.duckdb"
    con = duckdb.connect(DB_PATH, read_only=True)
    con.execute(f"SET file_search_path = '{REPO_ROOT}/transform'")

sql = open(f"{REPO_ROOT}/dashboard/observable/queries/{QUERY_NAME}.sql").read()
rows = con.execute(sql).fetchdf().to_dict("records")
json.dump(rows[0] if FIRST_ROW else rows, sys.stdout)
PYEOF
