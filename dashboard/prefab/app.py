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
    DataTable,
    DataTableColumn,
    H2,
    H3,
    H4,
    Muted,
    Row,
    Separator,
    Text,
)
from prefab_ui.components.charts import AreaChart, BarChart, ChartSeries, LineChart

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

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


# ── Summary cards ──────────────────────────────────────────────────

summary_cards = query("SELECT * FROM summary_kpis")[0]

net_flow = summary_cards["closed_4w"] - summary_cards["opened_4w"]
net_flow_sign = "+" if net_flow > 0 else ""

# ── Cumulative flow: bugs vs enhancements ──────────────────────────

cumulative_flow = query("SELECT * FROM cumulative_flow")

# ── Issue age distribution ─────────────────────────────────────────

age_dist = query("SELECT * FROM age_distribution")

# Pivot into chart format
age_buckets = ['0-7d', '8-30d', '31-90d', '91-180d', '180d+']
age_chart_data = []
for bucket in age_buckets:
    row = {"age_bucket": bucket}
    for cat in ['bug', 'enhancement', 'other']:
        row[cat] = sum(r["issue_count"] for r in age_dist if r["age_bucket"] == bucket and r["issue_category"] == cat)
    age_chart_data.append(row)

# ── Response time percentile bands ─────────────────────────────────

response_pctiles = query("SELECT * FROM response_pctiles")

# ── Bug vs Enhancement velocity ───────────────────────────────────

bug_velocity = query("SELECT * FROM bug_velocity")

enh_velocity = query("SELECT * FROM enh_velocity")

# Merge bug/enhancement velocity into one dataset
velocity_map = {}
for r in bug_velocity:
    velocity_map[r["week"]] = {"week": r["week"], "bugs": r["median_days"], "enhancements": None}
for r in enh_velocity:
    if r["week"] in velocity_map:
        velocity_map[r["week"]]["enhancements"] = r["median_days"]
    else:
        velocity_map[r["week"]] = {"week": r["week"], "bugs": None, "enhancements": r["median_days"]}
velocity_data = sorted(velocity_map.values(), key=lambda x: x["week"])

# ── Close time by label ────────────────────────────────────────────

close_by_label = query("SELECT * FROM close_by_label")

# ── Triage health ─────────────────────────────────────────────────

triage = query("SELECT * FROM triage_health")[0]

# ── EPIC burndown ──────────────────────────────────────────────────

epic_list = query("SELECT * FROM epic_list")

# ── Assignee workload ──────────────────────────────────────────────

assignee_workload = query("SELECT * FROM assignee_workload")

# ── Community priorities ───────────────────────────────────────────

community_priorities = query("SELECT * FROM community_priorities")

# ── Milestone burndown ─────────────────────────────────────────────

burndown_data = query("SELECT * FROM milestone_burndown_weekly")
open_milestone_titles = sorted({r["milestone_title"] for r in burndown_data})

# ── Open issues table ──────────────────────────────────────────────

open_issues_table = query("SELECT * FROM open_issues_table")

# ── Contributor leaderboard ────────────────────────────────────────

leaderboard = query("SELECT * FROM leaderboard")


# ══════════════════════════════════════════════════════════════════
#  BUILD DASHBOARD
# ══════════════════════════════════════════════════════════════════

with PrefabApp(css_class="max-w-7xl mx-auto p-6") as app:
    H2("dbt-fusion Issue Health")
    Muted("Actionable metrics for dbt-labs/dbt-fusion (excludes EPICs)")

    # ── Summary cards ──────────────────────────────────────────────
    with Row(gap=3, css_class="mt-6"):
        with Card(css_class="flex-1"):
            with CardHeader():
                CardTitle("Net Flow (4 wk)")
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
                Muted("No activity 30+ days")

    # ── Cumulative Issue Flow ──────────────────────────────────────
    with Card(css_class="mt-6"):
        with CardHeader():
            CardTitle("Cumulative Issue Flow (All non-EPIC)")
            Muted("Gap = issue debt")
        with CardContent():
            AreaChart(
                data=cumulative_flow,
                series=[
                    ChartSeries(data_key="cumulative_opened", label="Opened", color="hsl(0, 70%, 60%)"),
                    ChartSeries(data_key="cumulative_closed", label="Closed", color="hsl(140, 70%, 45%)"),
                ],
                x_axis="week",
                show_legend=True,
                height=300,
            )

    # ── Bug vs Enhancement flow side by side ───────────────────────
    with Row(gap=4, css_class="mt-6"):
        with Card(css_class="flex-1"):
            with CardHeader():
                CardTitle("Bug Flow")
            with CardContent():
                AreaChart(
                    data=cumulative_flow,
                    series=[
                        ChartSeries(data_key="cum_bugs_opened", label="Opened", color="hsl(0, 70%, 60%)"),
                        ChartSeries(data_key="cum_bugs_closed", label="Closed", color="hsl(140, 70%, 45%)"),
                    ],
                    x_axis="week",
                    show_legend=True,
                    height=250,
                )

        with Card(css_class="flex-1"):
            with CardHeader():
                CardTitle("Enhancement Flow")
            with CardContent():
                AreaChart(
                    data=cumulative_flow,
                    series=[
                        ChartSeries(data_key="cum_enh_opened", label="Opened", color="hsl(30, 80%, 55%)"),
                        ChartSeries(data_key="cum_enh_closed", label="Closed", color="hsl(200, 70%, 50%)"),
                    ],
                    x_axis="week",
                    show_legend=True,
                    height=250,
                )

    # ── Velocity: bugs vs enhancements ─────────────────────────────
    with Row(gap=4, css_class="mt-6"):
        with Card(css_class="flex-1"):
            with CardHeader():
                CardTitle("Median Days to Close: Bugs vs Enhancements")
            with CardContent():
                LineChart(
                    data=velocity_data,
                    series=[
                        ChartSeries(data_key="bugs", label="Bugs", color="hsl(0, 70%, 55%)"),
                        ChartSeries(data_key="enhancements", label="Enhancements", color="hsl(200, 70%, 50%)"),
                    ],
                    x_axis="week",
                    show_legend=True,
                    curve="smooth",
                    height=300,
                )

        with Card(css_class="flex-1"):
            with CardHeader():
                CardTitle("Time to First Response (hours)")
                Muted("p25 / p50 / p75 bands")
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

    # ── Age distribution + close time by label ─────────────────────
    with Row(gap=4, css_class="mt-6"):
        with Card(css_class="flex-1"):
            with CardHeader():
                CardTitle("Open Issue Age (by type)")
            with CardContent():
                BarChart(
                    data=age_chart_data,
                    series=[
                        ChartSeries(data_key="bug", label="Bug", color="hsl(0, 70%, 55%)"),
                        ChartSeries(data_key="enhancement", label="Enhancement", color="hsl(200, 70%, 50%)"),
                        ChartSeries(data_key="other", label="Other", color="hsl(0, 0%, 60%)"),
                    ],
                    x_axis="age_bucket",
                    stacked=True,
                    show_legend=True,
                    height=300,
                )

        with Card(css_class="flex-1"):
            with CardHeader():
                CardTitle("Median Days to Close by Label")
            with CardContent():
                BarChart(
                    data=close_by_label,
                    series=[ChartSeries(data_key="median_days_to_close", label="Days")],
                    x_axis="label_name",
                    horizontal=True,
                    show_legend=False,
                    height=400,
                )

    # ── Triage Health ──────────────────────────────────────────────
    with Card(css_class="mt-6"):
        with CardHeader():
            CardTitle("Triage Health (Open Issues)")
            Muted("How well-organized is the backlog?")
        with CardContent():
            with Row(gap=4):
                with Card(css_class="flex-1"):
                    with CardContent():
                        H3(f"{int(triage['pct_labeled'])}%")
                        Muted("Have labels")
                with Card(css_class="flex-1"):
                    with CardContent():
                        H3(f"{int(triage['pct_typed'])}%")
                        Muted("Have type (bug/enhancement)")
                with Card(css_class="flex-1"):
                    with CardContent():
                        H3(f"{int(triage['pct_assigned'])}%")
                        Muted("Are assigned")
                with Card(css_class="flex-1"):
                    with CardContent():
                        H3(f"{int(triage['pct_milestoned'])}%")
                        Muted("In a milestone")
                with Card(css_class="flex-1"):
                    with CardContent():
                        H3(str(triage["unlabeled_count"]))
                        Muted("Unlabeled issues")

    # ── Milestone Burndown ─────────────────────────────────────────
    if burndown_data:
        with Card(css_class="mt-6"):
            with CardHeader():
                CardTitle("Milestone Burndown")
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
                    series=[ChartSeries(data_key=t, label=t) for t in open_milestone_titles],
                    x_axis="date",
                    show_legend=True,
                    height=300,
                )

    # ── EPICs ──────────────────────────────────────────────────────
    with Card(css_class="mt-6"):
        with CardHeader():
            CardTitle("EPICs")
            Muted(f"{sum(1 for e in epic_list if e['state'] == 'OPEN')} open / {len(epic_list)} total")
        with CardContent():
            for epic in epic_list:
                if epic["state"] == "OPEN":
                    with Row(gap=2, css_class="py-1 border-b"):
                        Badge(f"#{epic['issue_number']}", variant="outline")
                        Text(
                            epic["title"][:70] + ("..." if len(epic["title"]) > 70 else ""),
                            css_class="flex-1 text-sm",
                        )
                        Badge(f"{epic['reactions_total_count']} reactions", variant="secondary")
                        Badge(f"{epic['comments_total_count']} comments", variant="secondary")

    # ── Assignee workload + community priorities ───────────────────
    with Row(gap=4, css_class="mt-6"):
        with Card(css_class="flex-1"):
            with CardHeader():
                CardTitle("Open Issues by Assignee")
            with CardContent():
                BarChart(
                    data=assignee_workload,
                    series=[
                        ChartSeries(data_key="bugs", label="Bugs", color="hsl(0, 70%, 55%)"),
                        ChartSeries(data_key="enhancements", label="Enhancements", color="hsl(200, 70%, 50%)"),
                    ],
                    x_axis="assignee_login",
                    stacked=True,
                    horizontal=True,
                    show_legend=True,
                    height=400,
                )

        with Card(css_class="flex-1"):
            with CardHeader():
                CardTitle("Community Priorities")
                Muted("Most-reacted open issues")
            with CardContent():
                for issue in community_priorities:
                    with Row(gap=2, css_class="py-1 border-b"):
                        Badge(f"#{issue['issue_number']}", variant="outline")
                        Badge(issue["issue_category"], variant="secondary")
                        Text(
                            issue["title"][:55] + ("..." if len(issue["title"]) > 55 else ""),
                            css_class="flex-1 text-sm",
                        )
                        Badge(f"{issue['reactions_total_count']} reactions", variant="default")

    # ── Open Issues Table ──────────────────────────────────────────
    with Card(css_class="mt-6"):
        with CardHeader():
            CardTitle("Oldest Open Issues")
            Muted("Top 50 by age")
        with CardContent():
            DataTable(
                data=open_issues_table,
                columns=[
                    DataTableColumn(key="#", header="#", sortable=True),
                    DataTableColumn(key="title", header="Title"),
                    DataTableColumn(key="type", header="Type", sortable=True),
                    DataTableColumn(key="age_days", header="Age (days)", sortable=True),
                    DataTableColumn(key="reactions", header="Reactions", sortable=True),
                    DataTableColumn(key="comments", header="Comments", sortable=True),
                    DataTableColumn(key="milestone", header="Milestone"),
                ],
                search=True,
                pagination=15,
            )

    # ── Contributor Leaderboard ────────────────────────────────────
    with Card(css_class="mt-6"):
        with CardHeader():
            CardTitle("Contributor Leaderboard")
            Muted("Top 15 by issues closed (all time)")
        with CardContent():
            BarChart(
                data=leaderboard,
                series=[ChartSeries(data_key="issues_closed", label="Issues Closed", color="hsl(260, 70%, 60%)")],
                x_axis="author_login",
                horizontal=True,
                show_legend=False,
                height=400,
            )
