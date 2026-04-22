"""
Generate JSON data files for the Observable Framework dashboard.
Writes to src/data/ — Observable Framework serves these as FileAttachments.

Usage:
    uv run dashboard/observable/generate_data.py
"""

import json
import os

import duckdb

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
HERE = os.path.dirname(__file__)
DATA_DIR = os.path.join(HERE, "src", "data")
QUERIES_DIR = os.path.join(HERE, "queries")

if os.environ.get("MOTHERDUCK_TOKEN"):
    DB_PATH = "md:fusion_issues"
else:
    DB_PATH = os.path.join(PROJECT_ROOT, "data", "fusion_issues.duckdb")


def get_connection():
    con = duckdb.connect(DB_PATH, read_only=True)
    if not DB_PATH.startswith("md:"):
        con.execute(f"SET file_search_path = '{os.path.join(PROJECT_ROOT, 'transform')}'")
    return con


def load_sql(name: str) -> str:
    with open(os.path.join(QUERIES_DIR, f"{name}.sql")) as f:
        return f.read()


def query(con, sql: str) -> list[dict]:
    return json.loads(con.execute(sql).fetchdf().to_json(orient="records"))


def write_json(filename: str, data):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w") as f:
        json.dump(data, f)
    count = len(data) if isinstance(data, list) else 1
    print(f"  wrote {path} ({count} records)")


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    con = get_connection()

    # -- Summary KPIs --
    summary = query(con, load_sql("summary"))[0]
    write_json("summary.json", summary)

    # -- Cumulative flow --
    write_json("cumulative_flow.json", query(con, load_sql("cumulative_flow")))

    # -- Bug + enhancement velocity (merged into wide format) --
    bug_v = query(con, load_sql("bug_velocity"))
    enh_v = query(con, load_sql("enh_velocity"))
    vel_map = {}
    for r in bug_v:
        vel_map[r["week"]] = {"week": r["week"], "bugs": r["median_days"], "enhancements": None}
    for r in enh_v:
        if r["week"] in vel_map:
            vel_map[r["week"]]["enhancements"] = r["median_days"]
        else:
            vel_map[r["week"]] = {"week": r["week"], "bugs": None, "enhancements": r["median_days"]}
    write_json("velocity.json", sorted(vel_map.values(), key=lambda x: x["week"]))

    # -- Response time percentiles --
    write_json("response_pctiles.json", query(con, load_sql("response_pctiles")))

    # -- Issue age distribution (pivoted) --
    age_dist = query(con, load_sql("age_distribution"))
    age_buckets = ["0-7d", "8-30d", "31-90d", "91-180d", "180d+"]
    age_chart_data = []
    for bucket in age_buckets:
        row = {"age_bucket": bucket}
        for cat in ["bug", "enhancement", "other"]:
            row[cat] = sum(
                r["issue_count"] for r in age_dist
                if r["age_bucket"] == bucket and r["issue_category"] == cat
            )
        age_chart_data.append(row)
    write_json("age_distribution.json", age_chart_data)

    # -- Median close by label --
    write_json("close_by_label.json", query(con, load_sql("close_by_label")))

    # -- Triage health --
    write_json("triage.json", query(con, load_sql("triage"))[0])

    # -- Assignee workload --
    write_json("assignee_workload.json", query(con, load_sql("assignee_workload")))

    # -- Community priorities --
    write_json("community_priorities.json", query(con, load_sql("community_priorities")))

    con.close()
    print("\nDone. All data files written to observable/src/data/")


if __name__ == "__main__":
    main()
