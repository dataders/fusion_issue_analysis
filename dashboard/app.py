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
    Muted,
    Row,
    Text,
)
from prefab_ui.components.charts import BarChart, ChartSeries, LineChart

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "fusion_issues.duckdb")

def query(sql: str) -> list[dict]:
    # Connect from the transform dir so relative parquet paths in views resolve
    con = duckdb.connect(DB_PATH, read_only=True)
    con.execute(f"SET file_search_path = '{os.path.join(PROJECT_ROOT, 'transform')}'")
    result = con.execute(sql).fetchdf()
    con.close()
    return result.to_dict("records")


# --- Load data ---
summary = query("SELECT * FROM issue_summary LIMIT 1")[0]

bug_velocity = query("""
    SELECT
        strftime(week_closed, '%Y-%m-%d') as week,
        bugs_closed,
        median_hours_to_close,
        avg_hours_to_close
    FROM bug_fix_velocity
    ORDER BY week_closed
""")

response_trends = query("""
    SELECT
        strftime(week_created, '%Y-%m-%d') as week,
        issues_opened,
        median_hours_to_first_response,
        pct_responded
    FROM response_time_trends
    WHERE issues_opened >= 3
    ORDER BY week_created
""")

# Get active milestones for burndown
milestones = query("""
    SELECT DISTINCT milestone_title
    FROM milestone_burndown
    WHERE milestone_title IS NOT NULL
    ORDER BY milestone_title
""")

# Get burndown for the most recent/active milestones (sample weekly for performance)
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

# Get per-milestone data as separate series
open_milestone_titles = list({r["milestone_title"] for r in burndown_data})

label_dist = query("""
    SELECT
        label_name,
        count(*) as issue_count
    FROM fct_issue_labels
    GROUP BY label_name
    ORDER BY issue_count DESC
    LIMIT 15
""")

weekly_open_close = query("""
    SELECT
        strftime(date_trunc('week', created_at), '%Y-%m-%d') as week,
        count(*) as opened
    FROM fct_issues
    GROUP BY date_trunc('week', created_at)
    ORDER BY week
""")

weekly_closed = query("""
    SELECT
        strftime(date_trunc('week', closed_at), '%Y-%m-%d') as week,
        count(*) as closed
    FROM fct_issues
    WHERE closed_at IS NOT NULL
    GROUP BY date_trunc('week', closed_at)
    ORDER BY week
""")

# Merge opened and closed into one dataset
open_close_map = {}
for r in weekly_open_close:
    open_close_map[r["week"]] = {"week": r["week"], "opened": r["opened"], "closed": 0}
for r in weekly_closed:
    if r["week"] in open_close_map:
        open_close_map[r["week"]]["closed"] = r["closed"]
    else:
        open_close_map[r["week"]] = {"week": r["week"], "opened": 0, "closed": r["closed"]}
open_close_data = sorted(open_close_map.values(), key=lambda x: x["week"])


# --- Build Dashboard ---
with PrefabApp(css_class="max-w-7xl mx-auto p-6") as app:
    H2("dbt-fusion Issue Analytics")
    Muted("Data from dbt-labs/dbt-fusion GitHub issues")

    # Summary cards
    with Row(gap=4, css_class="mt-6"):
        with Card(css_class="flex-1"):
            with CardHeader():
                CardTitle("Total Issues")
            with CardContent():
                H3(str(summary["total_issues"]))

        with Card(css_class="flex-1"):
            with CardHeader():
                CardTitle("Open Issues")
            with CardContent():
                H3(str(summary["open_issues"]))
                Muted(f"{round(summary['open_issues'] / summary['total_issues'] * 100, 1)}% of total")

        with Card(css_class="flex-1"):
            with CardHeader():
                CardTitle("Median Time to Close")
            with CardContent():
                H3(f"{round(summary['median_hours_to_close'] / 24, 1)} days")

        with Card(css_class="flex-1"):
            with CardHeader():
                CardTitle("Median First Response")
            with CardContent():
                H3(f"{round(summary['median_hours_to_first_response'] / 24, 1)} days")

    # Issue velocity chart
    with Card(css_class="mt-6"):
        with CardHeader():
            CardTitle("Issues Opened vs Closed per Week")
        with CardContent():
            BarChart(
                data=open_close_data,
                series=[
                    ChartSeries(data_key="opened", label="Opened", color="hsl(0, 70%, 60%)"),
                    ChartSeries(data_key="closed", label="Closed", color="hsl(140, 70%, 45%)"),
                ],
                x_axis="week",
                show_legend=True,
                height=350,
            )

    with Row(gap=4, css_class="mt-6"):
        # Bug fix velocity
        with Card(css_class="flex-1"):
            with CardHeader():
                CardTitle("Bug Fix Velocity (Median Hours to Close)")
            with CardContent():
                LineChart(
                    data=bug_velocity,
                    series=[
                        ChartSeries(data_key="median_hours_to_close", label="Median Hours", color="hsl(25, 90%, 55%)"),
                    ],
                    x_axis="week",
                    show_legend=True,
                    curve="smooth",
                    height=300,
                )

        # Response time trend
        with Card(css_class="flex-1"):
            with CardHeader():
                CardTitle("Time to First Response (Median Hours)")
            with CardContent():
                LineChart(
                    data=response_trends,
                    series=[
                        ChartSeries(data_key="median_hours_to_first_response", label="Median Hours", color="hsl(200, 80%, 50%)"),
                    ],
                    x_axis="week",
                    show_legend=True,
                    curve="smooth",
                    height=300,
                )

    # Milestone burndown
    if burndown_data:
        with Card(css_class="mt-6"):
            with CardHeader():
                CardTitle("Milestone Burndown (Open Issues)")
            with CardContent():
                # Create per-milestone burndown data merged by date
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

    # Label distribution
    with Card(css_class="mt-6"):
        with CardHeader():
            CardTitle("Top 15 Labels by Issue Count")
        with CardContent():
            BarChart(
                data=label_dist,
                series=[
                    ChartSeries(data_key="issue_count", label="Issues"),
                ],
                x_axis="label_name",
                show_legend=False,
                horizontal=True,
                height=400,
            )
