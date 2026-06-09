"""
Generate CSV files for the MDV dashboard.

MDV does not query databases directly, so this script keeps warehouse access in
the build step and lets the .mdv file stay Markdown-native.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
FILE_SEARCH_ROOT = Path(os.environ.get("FUSION_PROJECT_ROOT", PROJECT_ROOT))

if os.environ.get("FUSION_DB"):
    DB_PATH = os.environ["FUSION_DB"]
elif os.environ.get("MOTHERDUCK_TOKEN"):
    DB_PATH = "md:fusion_issues"
else:
    DB_PATH = str(PROJECT_ROOT / "data" / "fusion_issues.duckdb")


def get_connection():
    con = duckdb.connect(DB_PATH, read_only=True)
    if not DB_PATH.startswith("md:"):
        con.execute(f"SET file_search_path = '{FILE_SEARCH_ROOT / 'transform'}'")
    return con


def query(con, sql: str) -> list[dict[str, Any]]:
    return json.loads(con.execute(sql).fetchdf().to_json(orient="records"))


def fmt_int(value: Any) -> str:
    return f"{int(value):,}" if value is not None else "0"


def fmt_days(value: Any) -> str:
    return f"{float(value):.1f}d" if value is not None else "0.0d"


def fmt_pct(value: Any) -> str:
    return f"{float(value):.0f}%" if value is not None else "0%"


def build_stats(summary: dict[str, Any]) -> list[dict[str, str]]:
    net_flow = int(summary["net_flow_4w"])
    return [
        {"label": "Open issues", "value": fmt_int(summary["open_issues"]), "delta": ""},
        {"label": "Net flow (4wk)", "value": f"{net_flow:+,}", "delta": ""},
        {"label": "Median close (4wk)", "value": fmt_days(summary["rolling_median_close_days"]), "delta": ""},
        {"label": "48h response SLA", "value": fmt_pct(summary["pct_responded_48h"]), "delta": ""},
        {"label": "Stale issues", "value": fmt_int(summary["stale_count"]), "delta": ""},
    ]


def write_csv(filename: str, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / filename
    columns = fieldnames or list(rows[0].keys() if rows else [])
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  wrote {path} ({len(rows)} records)")


def build_triage_stats(triage: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"label": "Slipped through (bugs)", "value": fmt_int(triage["slipped_through_count"]), "delta": ""},
        {"label": "In triage queue", "value": fmt_int(triage["triage_queue_count"]), "delta": ""},
        {"label": "Hard blockers", "value": fmt_int(triage["hard_blocker_count"]), "delta": ""},
        {"label": "Needs repro", "value": fmt_int(triage["needs_repro_count"]), "delta": ""},
        {"label": "Repro verified", "value": fmt_int(triage["repro_verified_count"]), "delta": ""},
        {"label": "Stale", "value": fmt_int(triage["stale_count"]), "delta": ""},
    ]


def build_triage_pct_stats(th: dict[str, Any]) -> list[dict[str, str]]:
    """Canon tiles 18-21: triage quality percentages from triage_health."""
    return [
        {"label": "% Labeled", "value": fmt_pct(th["pct_labeled"]), "delta": ""},
        {"label": "% Typed", "value": fmt_pct(th["pct_typed"]), "delta": ""},
        {"label": "% Assigned", "value": fmt_pct(th["pct_assigned"]), "delta": ""},
        {"label": "% Milestoned", "value": fmt_pct(th["pct_milestoned"]), "delta": ""},
    ]


def main() -> None:
    con = get_connection()

    summary = query(con, "SELECT * FROM summary_kpis")[0]
    write_csv("stats.csv", build_stats(summary), ["label", "value", "delta"])

    triage = query(con, "SELECT * FROM issue_triage_health")[0]
    write_csv("triage_health.csv", build_triage_stats(triage), ["label", "value", "delta"])

    th = query(con, "SELECT pct_labeled, pct_typed, pct_assigned, pct_milestoned FROM triage_health")[0]
    write_csv("triage_pct_health.csv", build_triage_pct_stats(th), ["label", "value", "delta"])

    write_csv(
        "oldest_untriaged.csv",
        query(
            con,
            """
            select
                issue_number,
                title,
                age_days,
                issue_url
            from oldest_untriaged
            order by age_days desc
            """,
        ),
    )

    write_csv(
        "cumulative_flow.csv",
        query(
            con,
            """
            select week, 'Opened' as series, cumulative_opened as issues from cumulative_flow
            union all
            select week, 'Closed' as series, cumulative_closed as issues from cumulative_flow
            order by week, series
            """,
        ),
    )

    write_csv(
        "velocity.csv",
        query(
            con,
            """
            select
                week,
                case issue_category
                    when 'bug' then 'Bugs'
                    when 'enhancement' then 'Enhancements'
                    else upper(left(issue_category, 1)) || lower(substr(issue_category, 2))
                end as type,
                median_days as days
            from velocity
            order by week, type
            """,
        ),
    )

    write_csv(
        "response.csv",
        query(
            con,
            """
            select week, 'p25' as percentile, p25 as hours from response_pctiles
            union all
            select week, 'p50' as percentile, p50 as hours from response_pctiles
            union all
            select week, 'p75' as percentile, p75 as hours from response_pctiles
            order by week, percentile
            """,
        ),
    )

    write_csv(
        "age_distribution.csv",
        query(
            con,
            """
            SELECT age_bucket, issue_category, issue_count
            FROM age_distribution
            ORDER BY bucket_sort_order, issue_category
            """,
        ),
    )
    write_csv(
        "close_by_label.csv",
        query(con, "SELECT label_name, median_days_to_close FROM close_by_label ORDER BY median_days_to_close DESC LIMIT 12"),
    )
    write_csv(
        "assignee_workload.csv",
        query(
            con,
            """
            select assignee_login, 'Bugs' as type, bugs as open_issues from assignee_workload
            union all
            select assignee_login, 'Enhancements' as type, enhancements as open_issues from assignee_workload
            order by assignee_login, type
            """,
        ),
    )
    write_csv(
        "community_priorities.csv",
        query(
            con,
            """
            select
                issue_number as number,
                title,
                issue_category as type,
                reactions_total_count as reactions,
                comments_total_count as comments,
                age_days,
                issue_url
            from community_priorities
            order by reactions desc, comments desc
            """,
        ),
    )

    con.close()
    print("\nDone. All data files written to mdv/data/")


if __name__ == "__main__":
    main()
