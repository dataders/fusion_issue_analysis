"""
Generate JSON data files for the mviz dashboard.
Connects to DuckDB (local or MotherDuck) and exports query results.
"""

import json
import os

import duckdb

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

if os.environ.get("MOTHERDUCK_TOKEN"):
    DB_PATH = "md:fusion_issues"
else:
    DB_PATH = os.path.join(PROJECT_ROOT, "data", "fusion_issues.duckdb")

CORE_FILTER = "issue_category != 'epic'"


def get_connection():
    con = duckdb.connect(DB_PATH, read_only=True)
    if not DB_PATH.startswith("md:"):
        con.execute(
            f"SET file_search_path = '{os.path.join(PROJECT_ROOT, 'transform')}'"
        )
    return con


def query(con, sql: str) -> list[dict]:
    result = con.execute(sql).fetchdf()
    return json.loads(result.to_json(orient="records"))


def write_json(filename: str, data):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w") as f:
        json.dump(data, f)
    print(f"  wrote {path} ({len(data) if isinstance(data, list) else 1} records)")


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    con = get_connection()

    # -- Summary stats --
    summary = query(
        con,
        f"""
        with recent_window as (
            select
                count(case when created_at >= current_date - interval '28 days' then 1 end) as opened_4w,
                count(case when closed_at >= current_date - interval '28 days' then 1 end) as closed_4w,
                count(case when state = 'OPEN' then 1 end) as open_issues,
                count(*) as total_issues
            from fct_issues where {CORE_FILTER}
        ),
        rolling_close as (
            select round(median(hours_to_close) / 24, 1) as rolling_median_close_days
            from fct_issues
            where closed_at >= current_date - interval '28 days' and {CORE_FILTER}
        ),
        sla as (
            select
                round(
                    count(case when hours_to_first_response <= 48 then 1 end)::float
                    / nullif(count(case when hours_to_first_response is not null then 1 end), 0)
                    * 100, 0
                ) as pct_responded_48h
            from fct_issues
            where created_at >= current_date - interval '28 days' and {CORE_FILTER}
        ),
        stale as (
            select count(*) as stale_count
            from fct_issues
            where state = 'OPEN' and updated_at < current_date - interval '30 days' and {CORE_FILTER}
        )
        select * from recent_window cross join rolling_close cross join sla cross join stale
    """,
    )[0]

    net_flow = summary["closed_4w"] - summary["opened_4w"]
    median_close = summary["rolling_median_close_days"]
    sla_pct = summary["pct_responded_48h"]

    write_json("kpi_net_flow.json", {
        "value": net_flow, "label": "Net Flow (4wk)",
    })
    write_json("kpi_open_issues.json", {
        "value": summary["open_issues"], "label": "Open Issues",
    })
    write_json("kpi_median_close.json", {
        "value": float(median_close) if median_close else 0,
        "label": "Median Close (4wk, days)",
    })
    write_json("kpi_sla.json", {
        "value": round(sla_pct / 100, 2) if sla_pct else 0,
        "label": "48h Response SLA",
        "format": "pct0",
    })
    write_json("kpi_stale.json", {
        "value": summary["stale_count"], "label": "Stale Issues (30d+)",
    })

    # -- Cumulative flow --
    cumulative_flow = query(
        con,
        f"""
        with weeks as (
            select
                date_trunc('week', created_at)::date as week,
                count(*) as opened
            from fct_issues where {CORE_FILTER}
            group by 1
        ),
        closed_weeks as (
            select
                date_trunc('week', closed_at)::date as week,
                count(*) as closed
            from fct_issues where closed_at is not null and {CORE_FILTER}
            group by 1
        ),
        combined as (
            select
                coalesce(w.week, c.week) as week,
                coalesce(w.opened, 0) as opened,
                coalesce(c.closed, 0) as closed
            from weeks w
            full outer join closed_weeks c on w.week = c.week
        )
        select
            strftime(week, '%Y-%m-%d') as week,
            sum(opened) over (order by week) as cumulative_opened,
            sum(closed) over (order by week) as cumulative_closed
        from combined
        order by week
    """,
    )
    write_json("cumulative_flow.json", cumulative_flow)

    # -- Bug fix velocity --
    bug_velocity = query(
        con,
        """
        select
            strftime(date_trunc('week', closed_at), '%Y-%m-%d') as week,
            round(median(hours_to_close) / 24, 1) as median_days
        from fct_issues
        where issue_category = 'bug' and closed_at is not null
        group by date_trunc('week', closed_at)
        having count(*) >= 3
        order by week
    """,
    )
    enh_velocity = query(
        con,
        """
        select
            strftime(date_trunc('week', closed_at), '%Y-%m-%d') as week,
            round(median(hours_to_close) / 24, 1) as median_days
        from fct_issues
        where issue_category = 'enhancement' and closed_at is not null
        group by date_trunc('week', closed_at)
        having count(*) >= 2
        order by week
    """,
    )
    velocity_map = {}
    for r in bug_velocity:
        velocity_map[r["week"]] = {
            "week": r["week"],
            "bugs": r["median_days"],
            "enhancements": None,
        }
    for r in enh_velocity:
        if r["week"] in velocity_map:
            velocity_map[r["week"]]["enhancements"] = r["median_days"]
        else:
            velocity_map[r["week"]] = {
                "week": r["week"],
                "bugs": None,
                "enhancements": r["median_days"],
            }
    velocity_data = sorted(velocity_map.values(), key=lambda x: x["week"])
    write_json("velocity.json", velocity_data)

    # -- Response time percentiles --
    response_pctiles = query(
        con,
        f"""
        select
            strftime(date_trunc('week', created_at), '%Y-%m-%d') as week,
            round(quantile_cont(hours_to_first_response, 0.25), 1) as p25,
            round(quantile_cont(hours_to_first_response, 0.50), 1) as p50,
            round(quantile_cont(hours_to_first_response, 0.75), 1) as p75
        from fct_issues
        where hours_to_first_response is not null and {CORE_FILTER}
        group by date_trunc('week', created_at)
        having count(*) >= 3
        order by week
    """,
    )
    write_json("response_pctiles.json", response_pctiles)

    # -- Issue age distribution --
    age_dist = query(
        con,
        f"""
        select
            issue_category,
            case
                when datediff('day', created_at, current_date) <= 7 then '0-7d'
                when datediff('day', created_at, current_date) <= 30 then '8-30d'
                when datediff('day', created_at, current_date) <= 90 then '31-90d'
                when datediff('day', created_at, current_date) <= 180 then '91-180d'
                else '180d+'
            end as age_bucket,
            count(*) as issue_count
        from fct_issues
        where state = 'OPEN' and {CORE_FILTER}
        group by 1, 2
    """,
    )
    age_buckets = ["0-7d", "8-30d", "31-90d", "91-180d", "180d+"]
    age_chart_data = []
    for bucket in age_buckets:
        row = {"age_bucket": bucket}
        for cat in ["bug", "enhancement", "other"]:
            row[cat] = sum(
                r["issue_count"]
                for r in age_dist
                if r["age_bucket"] == bucket and r["issue_category"] == cat
            )
        age_chart_data.append(row)
    write_json("age_distribution.json", age_chart_data)

    # -- Close time by label --
    close_by_label = query(
        con,
        f"""
        select
            l.label_name,
            round(median(f.hours_to_close) / 24, 1) as median_days_to_close,
            count(*) as closed_count
        from fct_issues f
        inner join fct_issue_labels l on f.issue_dlt_id = l.issue_dlt_id
        where f.closed_at is not null and f.{CORE_FILTER}
        group by l.label_name
        having count(*) >= 10
        order by median_days_to_close desc
        limit 15
    """,
    )
    write_json("close_by_label.json", close_by_label)

    # -- Assignee workload --
    assignee_workload = query(
        con,
        f"""
        select
            a.assignee_login,
            count(*) as open_issues,
            count(case when f.issue_category = 'bug' then 1 end) as bugs,
            count(case when f.issue_category = 'enhancement' then 1 end) as enhancements
        from stg_issue_assignees a
        inner join fct_issues f on a.issue_dlt_id = f.issue_dlt_id
        where f.state = 'OPEN' and f.{CORE_FILTER}
        group by a.assignee_login
        order by open_issues desc
        limit 15
    """,
    )
    write_json("assignee_workload.json", assignee_workload)

    # -- Top reacted open issues --
    community_priorities = query(
        con,
        f"""
        select
            issue_number,
            title,
            issue_category,
            reactions_total_count as reactions,
            comments_total_count as comments,
            round(datediff('day', created_at, current_date), 0) as age_days
        from fct_issues
        where state = 'OPEN' and reactions_total_count > 0 and {CORE_FILTER}
        order by reactions_total_count desc
        limit 10
    """,
    )
    write_json("community_priorities.json", community_priorities)

    con.close()
    print("\nDone. All data files written to dashboard/data/")


if __name__ == "__main__":
    main()
