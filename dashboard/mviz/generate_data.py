"""
Generate JSON data files for the mviz dashboard.
Connects to DuckDB (local or MotherDuck) and exports query results.
"""

import json
import os

import duckdb

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
HERE = os.path.dirname(__file__)
DATA_DIR = os.path.join(HERE, "data")

if os.environ.get("MOTHERDUCK_TOKEN"):
    DB_PATH = "md:fusion_issues"
else:
    DB_PATH = os.path.join(PROJECT_ROOT, "data", "fusion_issues.duckdb")


def get_connection():
    con = duckdb.connect(DB_PATH, read_only=True)
    if not DB_PATH.startswith("md:"):
        con.execute(f"SET file_search_path = '{os.path.join(PROJECT_ROOT, 'transform')}'")
    return con


def query(con, sql: str) -> list[dict]:
    return json.loads(con.execute(sql).fetchdf().to_json(orient="records"))


def write_json(filename: str, data):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w") as f:
        json.dump(data, f)
    print(f"  wrote {path} ({len(data) if isinstance(data, list) else 1} records)")


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    con = get_connection()

    # -- Summary stats --
    summary = query(con, "SELECT * FROM summary_kpis")[0]
    net_flow = summary["closed_4w"] - summary["opened_4w"]
    median_close = summary["rolling_median_close_days"]
    sla_pct = summary["pct_responded_48h"]

    write_json("kpi_net_flow.json", {"value": net_flow, "label": "Net Flow (4wk)"})
    write_json("kpi_open_issues.json", {"value": summary["open_issues"], "label": "Open Issues"})
    write_json("kpi_median_close.json", {
        "value": float(median_close) if median_close else 0,
        "label": "Median Close (4wk, days)",
    })
    write_json("kpi_sla.json", {
        "value": round(sla_pct / 100, 2) if sla_pct else 0,
        "label": "48h Response SLA",
        "format": "pct0",
    })
    write_json("kpi_stale.json", {"value": summary["stale_count"], "label": "Stale Issues (30d+)"})

    # -- Cumulative flow --
    write_json("cumulative_flow.json", query(con, "SELECT * FROM cumulative_flow"))

    # -- Bug + enhancement velocity (merged) --
    bug_velocity = query(con, "SELECT * FROM bug_velocity")
    enh_velocity = query(con, "SELECT * FROM enh_velocity")
    velocity_map = {}
    for r in bug_velocity:
        velocity_map[r["week"]] = {"week": r["week"], "bugs": r["median_days"], "enhancements": None}
    for r in enh_velocity:
        if r["week"] in velocity_map:
            velocity_map[r["week"]]["enhancements"] = r["median_days"]
        else:
            velocity_map[r["week"]] = {"week": r["week"], "bugs": None, "enhancements": r["median_days"]}
    write_json("velocity.json", sorted(velocity_map.values(), key=lambda x: x["week"]))

    # -- Response time percentiles --
    write_json("response_pctiles.json", query(con, "SELECT * FROM response_pctiles"))

    # -- Issue age distribution (pivoted) --
    age_dist = query(con, "SELECT * FROM age_distribution")
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

    # -- Close time by label --
    write_json("close_by_label.json", query(con, "SELECT * FROM close_by_label"))

    # -- Assignee workload --
    write_json("assignee_workload.json", query(con, "SELECT * FROM assignee_workload"))

    # -- Community priorities --
    write_json("community_priorities.json", query(con, "SELECT * FROM community_priorities"))

    con.close()
    print("\nDone. All data files written to mviz/data/")


if __name__ == "__main__":
    main()
