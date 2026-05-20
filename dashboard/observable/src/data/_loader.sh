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
import sys, json, duckdb, math, os
REPO_ROOT = "$REPO_ROOT"
QUERY_NAME = "$QUERY_NAME"
FIRST_ROW = "$FIRST_ROW" == "--first-row"

if os.environ.get("FUSION_DB"):
    DB_PATH = os.environ["FUSION_DB"]
    con = duckdb.connect(DB_PATH, read_only=True)
elif os.environ.get("MOTHERDUCK_TOKEN"):
    DB_PATH = "md:fusion_issues"
    con = duckdb.connect(DB_PATH)
else:
    DB_PATH = f"{REPO_ROOT}/data/fusion_issues.duckdb"
    con = duckdb.connect(DB_PATH, read_only=True)
if not DB_PATH.startswith("md:"):
    file_search_root = os.environ.get("FUSION_PROJECT_ROOT", REPO_ROOT)
    con.execute(f"SET file_search_path = '{file_search_root}/transform'")

SQL_BY_NAME = {
    "summary": "SELECT * FROM summary_kpis",
    "triage": "SELECT * FROM triage_health",
    "triage_health": "SELECT * FROM issue_triage_health",
    "oldest_untriaged": "SELECT * FROM oldest_untriaged",
    "cumulative_flow": "SELECT * FROM cumulative_flow ORDER BY week",
    "response_pctiles": "SELECT * FROM response_pctiles ORDER BY week",
    "close_by_label": "SELECT * FROM close_by_label ORDER BY median_days_to_close DESC",
    "assignee_workload": "SELECT * FROM assignee_workload ORDER BY open_issues DESC",
    "community_priorities": "SELECT * FROM community_priorities ORDER BY reactions_total_count DESC",
    "velocity": """
        SELECT
            week,
            max(CASE WHEN issue_category = 'bug' THEN median_days END) AS bugs,
            max(CASE WHEN issue_category = 'enhancement' THEN median_days END) AS enhancements
        FROM velocity
        GROUP BY week
        ORDER BY week
    """,
    "age_distribution": """
        SELECT
            age_bucket,
            sum(CASE WHEN issue_category = 'bug' THEN issue_count ELSE 0 END) AS bug,
            sum(CASE WHEN issue_category = 'enhancement' THEN issue_count ELSE 0 END) AS enhancement,
            sum(CASE WHEN issue_category = 'other' THEN issue_count ELSE 0 END) AS other
        FROM age_distribution
        GROUP BY age_bucket
        ORDER BY CASE age_bucket
            WHEN '0-7d' THEN 1
            WHEN '8-30d' THEN 2
            WHEN '31-90d' THEN 3
            WHEN '91-180d' THEN 4
            ELSE 5
        END
    """,
}
sql = SQL_BY_NAME[QUERY_NAME]
rows = con.execute(sql).fetchdf().to_dict("records")

def clean(value):
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value

rows = [{key: clean(value) for key, value in row.items()} for row in rows]
json.dump(rows[0] if FIRST_ROW else rows, sys.stdout, allow_nan=False)
PYEOF
