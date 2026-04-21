#!/bin/bash
# Resolve repo root: this file lives at <repo>/dashboard/observable/src/data/
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"

uv --directory "$REPO_ROOT" run python3 - <<'PYEOF'
import sys, json, duckdb, os
REPO_ROOT = os.environ['REPO_ROOT']

if os.environ.get("MOTHERDUCK_TOKEN"):
    DB_PATH = "md:fusion_issues"
else:
    DB_PATH = f'{REPO_ROOT}/data/fusion_issues.duckdb'

con = duckdb.connect(DB_PATH, read_only=True)
if not DB_PATH.startswith("md:"):
    con.execute(f"SET file_search_path = '{REPO_ROOT}/transform'")

summary = con.execute("SELECT * FROM summary_kpis").fetchdf().to_dict('records')[0]
flow    = con.execute("SELECT * FROM weekly_flow").fetchdf().to_dict('records')
velocity = con.execute("SELECT * FROM velocity").fetchdf().to_dict('records')
triage  = con.execute("SELECT * FROM triage_health").fetchdf().to_dict('records')[0]
top_issues = con.execute("SELECT * FROM community_priorities").fetchdf().to_dict('records')

json.dump({"summary": summary, "flow": flow, "velocity": velocity, "triage": triage, "top_issues": top_issues}, sys.stdout)
PYEOF
