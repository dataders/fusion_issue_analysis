"""
Prefab dashboard for dbt-fusion issue analytics.
Reads from the DuckDB database populated by the dbt transform layer.
"""

import os
import duckdb
from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    Badge,
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Column,
    H2,
    H3,
    H4,
    Muted,
    Row,
    Text,
)
from prefab_ui.components.charts import AreaChart, BarChart, ChartSeries, LineChart

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Use MotherDuck if MOTHERDUCK_TOKEN is set, otherwise local DuckDB
if os.environ.get("MOTHERDUCK_TOKEN"):
    DB_PATH = "md:fusion_issues"
else:
    DB_PATH = os.path.join(PROJECT_ROOT, "data", "fusion_issues.duckdb")

def query(sql: str) -> list[dict]:
    con = duckdb.connect(DB_PATH, read_only=True)
    if not DB_PATH.startswith("md:"):
        con.execute(f"SET file_search_path = '{os.path.join(PROJECT_ROOT, 'transform')}'")
    result = con.execute(sql).fetchdf()
    con.close()
    return result.to_dict("records")


# ── Summary card data ──────────────────────────────────────────────

summary_cards = query("""
    with recent_window as (
        select
            count(case when created_at >= current_date - interval '28 days' then 1 end) as opened_4w,
            count(case when closed_at >= current_date - interval '28 days' then 1 end) as closed_4w,
            count(case when state = 'OPEN' then 1 end) as open_issues,
            count(*) as total_issues
        from fct_issues
    ),
    rolling_close as (
        select round(median(hours_to_close) / 24, 1) as rolling_median_close_days
        from fct_issues
        where closed_at >= current_date - interval '28 days'
    ),
    sla as (
        select
            round(
                count(case when hours_to_first_response <= 48 then 1 end)::float
                / nullif(count(case when hours_to_first_response is not null then 1 end), 0)
                * 100, 0
            ) as pct_responded_48h
        from fct_issues
        where created_at >= current_date - interval '28 days'
    ),
    stale as (
        select count(*) as stale_count
        from fct_issues
        where state = 'OPEN' and updated_at < current_date - interval '30 days'
    )
    select * from recent_window cross join rolling_close cross join sla cross join stale
""")[0]

net_flow = summary_cards["closed_4w"] - summary_cards["opened_4w"]
net_flow_sign = "+" if net_flow > 0 else ""
net_flow_color = "success" if net_flow > 0 else "destructive"

# ── Cumulative issue flow ──────────────────────────────────────────

cumulative_flow = query("""
    with weeks as (
        select
            date_trunc('week', created_at)::date as week,
            count(*) as opened
        from fct_issues
        group by 1
    ),
    closed_weeks as (
        select
            date_trunc('week', closed_at)::date as week,
            count(*) as closed
        from fct_issues where closed_at is not null
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
""")

# ── Issue age distribution (open issues) ───────────────────────────

age_dist = query("""
    select
        case
            when datediff('day', created_at, current_date) <= 7 then '0-7d'
            when datediff('day', created_at, current_date) <= 30 then '8-30d'
            when datediff('day', created_at, current_date) <= 90 then '31-90d'
            when datediff('day', created_at, current_date) <= 180 then '91-180d'
            else '180d+'
        end as age_bucket,
        count(*) as issue_count
    from fct_issues
    where state = 'OPEN'
    group by 1
    order by case age_bucket
        when '0-7d' then 1 when '8-30d' then 2 when '31-90d' then 3
        when '91-180d' then 4 else 5 end
""")

# ── Response time percentile bands ─────────────────────────────────

response_pctiles = query("""
    select
        strftime(date_trunc('week', created_at), '%Y-%m-%d') as week,
        round(quantile_cont(hours_to_first_response, 0.25), 1) as p25,
        round(quantile_cont(hours_to_first_response, 0.50), 1) as p50,
        round(quantile_cont(hours_to_first_response, 0.75), 1) as p75
    from fct_issues
    where hours_to_first_response is not null
    group by date_trunc('week', created_at)
    having count(*) >= 3
    order by week
""")

# ── Bug fix velocity percentile bands ──────────────────────────────

bug_velocity_pctiles = query("""
    select
        strftime(date_trunc('week', f.closed_at), '%Y-%m-%d') as week,
        count(*) as bugs_closed,
        round(quantile_cont(f.hours_to_close, 0.25), 1) as p25,
        round(quantile_cont(f.hours_to_close, 0.50), 1) as p50,
        round(quantile_cont(f.hours_to_close, 0.75), 1) as p75
    from fct_issues f
    inner join fct_issue_labels l on f.issue_dlt_id = l.issue_dlt_id
    where l.label_name = 'bug' and f.closed_at is not null
    group by date_trunc('week', f.closed_at)
    having count(*) >= 3
    order by week
""")

# ── Close time by label ────────────────────────────────────────────

close_by_label = query("""
    select
        l.label_name,
        round(median(f.hours_to_close) / 24, 1) as median_days_to_close,
        count(*) as closed_count
    from fct_issues f
    inner join fct_issue_labels l on f.issue_dlt_id = l.issue_dlt_id
    where f.closed_at is not null
    group by l.label_name
    having count(*) >= 10
    order by median_days_to_close desc
    limit 15
""")

# ── Assignee workload ──────────────────────────────────────────────

assignee_workload = query("""
    select
        a.assignee_login,
        count(*) as open_issues
    from stg_issue_assignees a
    inner join fct_issues f on a.issue_dlt_id = f.issue_dlt_id
    where f.state = 'OPEN'
    group by a.assignee_login
    order by open_issues desc
    limit 15
""")

# ── Community priorities (top-reacted open issues) ─────────────────

community_priorities = query("""
    select
        issue_number,
        title,
        reactions_total_count,
        comments_total_count,
        round(datediff('day', created_at, current_date), 0) as age_days,
        milestone_title
    from fct_issues
    where state = 'OPEN' and reactions_total_count > 0
    order by reactions_total_count desc
    limit 10
""")

# ── Milestone burndown ─────────────────────────────────────────────

burndown_data = query("""
    SELECT
        strftime(date_day, '%Y-%m-%d') as date_day,
        milestone_title,
        open_at_date,
        cumulative_opened,
        cumulative_closed
    FROM milestone_burndown
    WHERE date_day::date = date_trunc('week', date_day::date)
      AND milestone_title IN (
          SELECT DISTINCT milestone_title
          FROM dim_milestones
          WHERE milestone_state = 'OPEN'
      )
    ORDER BY milestone_title, date_day
""")
open_milestone_titles = sorted({r["milestone_title"] for r in burndown_data})


# ── Build Dashboard ────────────────────────────────────────────────

with PrefabApp(css_class="max-w-7xl mx-auto p-6") as app:
    H2("dbt-fusion Issue Health")
    Muted("Actionable metrics for dbt-labs/dbt-fusion — updated on deploy")

    # ── Summary cards ──────────────────────────────────────────────
    with Row(gap=3, css_class="mt-6"):
        with Card(css_class="flex-1"):
            with CardHeader():
                CardTitle("Net Flow (4 weeks)")
            with CardContent():
                H3(f"{net_flow_sign}{net_flow}")
                Muted(f"{summary_cards['opened_4w']} opened / {summary_cards['closed_4w']} closed")

        with Card(css_class="flex-1"):
            with CardHeader():
                CardTitle("Open Issues")
            with CardContent():
                H3(str(summary_cards["open_issues"]))

        with Card(css_class="flex-1"):
            with CardHeader():
                CardTitle("Median Close (4 wk)")
            with CardContent():
                val = summary_cards["rolling_median_close_days"]
                H3(f"{val} days" if val else "N/A")

        with Card(css_class="flex-1"):
            with CardHeader():
                CardTitle("48h Response SLA")
            with CardContent():
                pct = summary_cards["pct_responded_48h"]
                H3(f"{int(pct)}%" if pct else "N/A")

        with Card(css_class="flex-1"):
            with CardHeader():
                CardTitle("Stale Issues")
            with CardContent():
                H3(str(summary_cards["stale_count"]))
                Muted("No activity in 30+ days")

    # ── Cumulative Issue Flow (the #1 chart) ───────────────────────
    with Card(css_class="mt-6"):
        with CardHeader():
            CardTitle("Cumulative Issue Flow")
            Muted("Gap between lines = issue debt")
        with CardContent():
            AreaChart(
                data=cumulative_flow,
                series=[
                    ChartSeries(data_key="cumulative_opened", label="Opened", color="hsl(0, 70%, 60%)"),
                    ChartSeries(data_key="cumulative_closed", label="Closed", color="hsl(140, 70%, 45%)"),
                ],
                x_axis="week",
                show_legend=True,
                height=350,
            )

    with Row(gap=4, css_class="mt-6"):
        # ── Issue Age Distribution ─────────────────────────────────
        with Card(css_class="flex-1"):
            with CardHeader():
                CardTitle("Open Issue Age Distribution")
            with CardContent():
                BarChart(
                    data=age_dist,
                    series=[ChartSeries(data_key="issue_count", label="Issues")],
                    x_axis="age_bucket",
                    show_legend=False,
                    height=300,
                )

        # ── Close Time by Label ────────────────────────────────────
        with Card(css_class="flex-1"):
            with CardHeader():
                CardTitle("Median Days to Close by Label")
                Muted("Labels with 10+ closed issues")
            with CardContent():
                BarChart(
                    data=close_by_label,
                    series=[ChartSeries(data_key="median_days_to_close", label="Median Days")],
                    x_axis="label_name",
                    show_legend=False,
                    horizontal=True,
                    height=400,
                )

    # ── Percentile band charts ─────────────────────────────────────
    with Row(gap=4, css_class="mt-6"):
        with Card(css_class="flex-1"):
            with CardHeader():
                CardTitle("Time to First Response (hours)")
                Muted("p25 / p50 / p75 bands by week")
            with CardContent():
                LineChart(
                    data=response_pctiles,
                    series=[
                        ChartSeries(data_key="p75", label="p75", color="hsl(0, 60%, 70%)"),
                        ChartSeries(data_key="p50", label="Median", color="hsl(200, 80%, 50%)"),
                        ChartSeries(data_key="p25", label="p25", color="hsl(140, 60%, 60%)"),
                    ],
                    x_axis="week",
                    show_legend=True,
                    curve="smooth",
                    height=300,
                )

        with Card(css_class="flex-1"):
            with CardHeader():
                CardTitle("Bug Fix Velocity (hours to close)")
                Muted("p25 / p50 / p75 bands by week")
            with CardContent():
                LineChart(
                    data=bug_velocity_pctiles,
                    series=[
                        ChartSeries(data_key="p75", label="p75", color="hsl(0, 60%, 70%)"),
                        ChartSeries(data_key="p50", label="Median", color="hsl(25, 90%, 55%)"),
                        ChartSeries(data_key="p25", label="p25", color="hsl(140, 60%, 60%)"),
                    ],
                    x_axis="week",
                    show_legend=True,
                    curve="smooth",
                    height=300,
                )

    # ── Milestone Burndown ─────────────────────────────────────────
    if burndown_data:
        with Card(css_class="mt-6"):
            with CardHeader():
                CardTitle("Milestone Burndown (Open Issues)")
            with CardContent():
                burndown_by_date: dict[str, dict] = {}
                for r in burndown_data:
                    d = r["date_day"]
                    if d not in burndown_by_date:
                        burndown_by_date[d] = {"date": d}
                    burndown_by_date[d][r["milestone_title"]] = r["open_at_date"]
                merged_burndown = sorted(burndown_by_date.values(), key=lambda x: x["date"])

                LineChart(
                    data=merged_burndown,
                    series=[
                        ChartSeries(data_key=title, label=title)
                        for title in open_milestone_titles
                    ],
                    x_axis="date",
                    show_legend=True,
                    height=350,
                )

    with Row(gap=4, css_class="mt-6"):
        # ── Assignee Workload ──────────────────────────────────────
        with Card(css_class="flex-1"):
            with CardHeader():
                CardTitle("Open Issues by Assignee")
                Muted("Bus factor / workload distribution")
            with CardContent():
                BarChart(
                    data=assignee_workload,
                    series=[ChartSeries(data_key="open_issues", label="Open Issues")],
                    x_axis="assignee_login",
                    show_legend=False,
                    horizontal=True,
                    height=400,
                )

        # ── Community Priorities ───────────────────────────────────
        with Card(css_class="flex-1"):
            with CardHeader():
                CardTitle("Community Priorities")
                Muted("Most-reacted open issues")
            with CardContent():
                for issue in community_priorities[:10]:
                    with Row(gap=2, css_class="py-1 border-b"):
                        Badge(f"#{issue['issue_number']}", variant="outline")
                        Text(
                            issue["title"][:60] + ("..." if len(issue["title"]) > 60 else ""),
                            css_class="flex-1 text-sm",
                        )
                        Badge(f"{issue['reactions_total_count']} reactions", variant="secondary")
