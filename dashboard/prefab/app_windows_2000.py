"""
Prefab dashboard for dbt-fusion issue analytics.
Windows 2000 desktop app edition.
"""

import os

import duckdb
from prefab_ui.app import PrefabApp, Theme
from prefab_ui.components import (
    Badge,
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    DataTable,
    DataTableColumn,
    Div,
    H2,
    H3,
    Muted,
    Row,
    Span,
    Text,
)
from prefab_ui.components.charts import AreaChart, BarChart, ChartSeries, LineChart

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if os.environ.get("FUSION_DB"):
    DB_PATH = os.environ["FUSION_DB"]
elif os.environ.get("MOTHERDUCK_TOKEN"):
    DB_PATH = "md:fusion_issues"
else:
    DB_PATH = os.path.join(PROJECT_ROOT, "data", "fusion_issues.duckdb")


def query(sql: str) -> list[dict]:
    con = duckdb.connect(DB_PATH, read_only=True)
    if not DB_PATH.startswith("md:"):
        file_search_root = os.environ.get("FUSION_PROJECT_ROOT", PROJECT_ROOT)
        con.execute(f"SET file_search_path = '{os.path.join(file_search_root, 'transform')}'")
    result = con.execute(sql).fetchdf()
    con.close()
    return result.to_dict("records")


summary = query("SELECT * FROM summary_kpis")[0]
triage = query("SELECT * FROM triage_health")[0]
cumulative_flow = query("SELECT * FROM cumulative_flow")
response_pctiles = query("SELECT * FROM response_pctiles")
bug_velocity = query("SELECT * FROM bug_velocity")
enh_velocity = query("SELECT * FROM enh_velocity")
age_dist = query("SELECT * FROM age_distribution")
close_by_label = query("SELECT * FROM close_by_label")
assignee_workload = query("SELECT * FROM assignee_workload")
community_priorities = query("SELECT * FROM community_priorities")
open_issues_table = query("SELECT * FROM open_issues_table")

net_flow = summary["closed_4w"] - summary["opened_4w"]
net_flow_sign = "+" if net_flow > 0 else ""

velocity_map: dict[str, dict] = {}
for row in bug_velocity:
    velocity_map[row["week"]] = {"week": row["week"], "bugs": row["median_days"], "enhancements": None}
for row in enh_velocity:
    if row["week"] in velocity_map:
        velocity_map[row["week"]]["enhancements"] = row["median_days"]
    else:
        velocity_map[row["week"]] = {"week": row["week"], "bugs": None, "enhancements": row["median_days"]}
velocity_data = sorted(velocity_map.values(), key=lambda row: row["week"])

age_buckets = ["0-7d", "8-30d", "31-90d", "91-180d", "180d+"]
age_chart_data = []
for bucket in age_buckets:
    chart_row = {"age_bucket": bucket}
    for issue_type in ["bug", "enhancement", "other"]:
        chart_row[issue_type] = sum(
            row["issue_count"]
            for row in age_dist
            if row["age_bucket"] == bucket and row["issue_category"] == issue_type
        )
    age_chart_data.append(chart_row)

WIN2K_CSS = """
body {
    background: linear-gradient(180deg, #1b5aa8 0%, #0f4d9d 100%) !important;
    color: #000 !important;
    font-family: Tahoma, "MS Sans Serif", sans-serif !important;
}
#root { color: #000 !important; }
.win-window {
    background: #c3c7cb !important;
    border-top: 2px solid #fff !important;
    border-left: 2px solid #fff !important;
    border-right: 2px solid #404040 !important;
    border-bottom: 2px solid #404040 !important;
    box-shadow: 10px 16px 28px rgba(0, 0, 0, .35) !important;
}
.title-bar {
    align-items: center;
    background: linear-gradient(90deg, #0a246a 0%, #2b63b5 100%) !important;
    color: #fff !important;
    display: flex;
    justify-content: space-between;
    min-height: 30px;
    padding: 5px 8px;
}
.title-bar span { color: #fff !important; }
.window-button {
    background: #d4d0c8 !important;
    border-top: 1px solid #fff !important;
    border-left: 1px solid #fff !important;
    border-right: 1px solid #404040 !important;
    border-bottom: 1px solid #404040 !important;
    color: #000 !important;
    display: inline-flex;
    font-size: 11px;
    font-weight: 700;
    height: 18px;
    justify-content: center;
    min-width: 18px;
}
.menu-bar, .status-bar { background: #d4d0c8 !important; }
.menu-bar { border-bottom: 1px solid #9b9b9b; padding: 4px 8px 5px; }
.menu-item { color: #000 !important; display: inline-block; font-size: 12px; margin-right: 18px; }
.workspace { background: #3a6ea5 !important; padding: 12px; }
.win-panel {
    background: #d4d0c8 !important;
    border-top: 1px solid #fff !important;
    border-left: 1px solid #fff !important;
    border-right: 1px solid #808080 !important;
    border-bottom: 1px solid #808080 !important;
}
.win-inset {
    background: #fff !important;
    border-top: 2px solid #808080 !important;
    border-left: 2px solid #808080 !important;
    border-right: 2px solid #fff !important;
    border-bottom: 2px solid #fff !important;
    padding: 8px;
}
.group-caption { color: #000 !important; font-size: 11px; font-weight: 700; text-transform: uppercase; }
.kpi-label { color: #404040 !important; font-size: 11px; text-transform: uppercase; }
.kpi-value { color: #000 !important; font-size: 28px; font-weight: 700; line-height: 1.1; }
.kpi-detail, .status-mini { color: #404040 !important; font-size: 11px; }
.shell-title { color: #000 !important; font-size: 26px; font-weight: 700; line-height: 1.1; }
.shell-subtitle { color: #404040 !important; font-size: 12px; }
.priority-row { border-bottom: 1px solid #d7d7d7; color: #000 !important; font-size: 12px; padding: 6px 0; }
.priority-meta { color: #5a5a5a !important; font-size: 11px; }
.status-bar { border-top: 1px solid #808080; padding: 4px 6px; }
.status-segment {
    border-top: 1px solid #808080 !important;
    border-left: 1px solid #808080 !important;
    border-right: 1px solid #fff !important;
    border-bottom: 1px solid #fff !important;
    color: #000 !important;
    display: inline-block;
    font-size: 11px;
    margin-right: 6px;
    min-height: 20px;
    padding: 3px 8px;
}
"""

WIN2K_THEME = Theme(mode="light", font="Tahoma", css=WIN2K_CSS, accent="#0a246a")


def kpi_card(title: str, value: str, detail: str) -> None:
    with Card(css_class="win-panel flex-1"):
        with CardHeader():
            CardTitle(title, css_class="kpi-label")
        with CardContent():
            H3(value, css_class="kpi-value")
            Text(detail, css_class="kpi-detail")


with PrefabApp(css_class="mx-auto p-4", theme=WIN2K_THEME) as app:
    with Div(css_class="win-window", style={"max-width": "1440px", "margin": "0 auto"}):
        with Div(css_class="title-bar"):
            Span("Fusion Issue Explorer")
            with Div():
                Span("_", css_class="window-button")
                Span("[]", css_class="window-button")
                Span("X", css_class="window-button")

        with Div(css_class="menu-bar"):
            for item in ["File", "Edit", "View", "Go", "Tools", "Help"]:
                Span(item, css_class="menu-item")

        with Div(css_class="workspace"):
            H2("Fusion Issue Explorer", css_class="shell-title")
            Text("dbt-fusion backlog shell over shared dbt dashboard marts", css_class="shell-subtitle")

            with Row(gap=3, css_class="mt-3"):
                kpi_card("Open Issues", str(summary["open_issues"]), "Current queue depth")
                kpi_card("Net Flow", f"{net_flow_sign}{net_flow}", f"{summary['opened_4w']} opened / {summary['closed_4w']} closed")
                kpi_card(
                    "Median Close",
                    f"{summary['rolling_median_close_days']}d" if summary["rolling_median_close_days"] is not None else "N/A",
                    "Rolling 4 week median",
                )
                kpi_card(
                    "48h Response",
                    f"{int(summary['pct_responded_48h'])}%" if summary["pct_responded_48h"] is not None else "N/A",
                    "First response SLA",
                )
                kpi_card("Stale Issues", str(summary["stale_count"]), "No activity 30+ days")

            with Row(gap=3, css_class="mt-3"):
                with Card(css_class="win-panel flex-1"):
                    with CardHeader():
                        CardTitle("Cumulative Issue Flow", css_class="group-caption")
                        Muted("Running opened vs closed issue totals")
                    with CardContent():
                        with Div(css_class="win-inset"):
                            AreaChart(
                                data=cumulative_flow,
                                series=[
                                    ChartSeries(data_key="cumulative_opened", label="Opened", color="#245edb"),
                                    ChartSeries(data_key="cumulative_closed", label="Closed", color="#2f7d32"),
                                ],
                                x_axis="week",
                                show_legend=True,
                                height=285,
                            )

                with Card(css_class="win-panel flex-1"):
                    with CardHeader():
                        CardTitle("Median Days to Close", css_class="group-caption")
                        Muted("Bugs vs enhancements")
                    with CardContent():
                        with Div(css_class="win-inset"):
                            LineChart(
                                data=velocity_data,
                                series=[
                                    ChartSeries(data_key="bugs", label="Bugs", color="#b22222"),
                                    ChartSeries(data_key="enhancements", label="Enhancements", color="#245edb"),
                                ],
                                x_axis="week",
                                show_legend=True,
                                curve="smooth",
                                height=285,
                            )

            with Row(gap=3, css_class="mt-3"):
                with Card(css_class="win-panel flex-1"):
                    with CardHeader():
                        CardTitle("Time to First Response", css_class="group-caption")
                        Muted("p25 / p50 / p75 hours")
                    with CardContent():
                        with Div(css_class="win-inset"):
                            LineChart(
                                data=response_pctiles,
                                series=[
                                    ChartSeries(data_key="p75", label="p75", color="#8a4d00"),
                                    ChartSeries(data_key="p50", label="Median", color="#0a246a"),
                                    ChartSeries(data_key="p25", label="p25", color="#2f7d32"),
                                ],
                                x_axis="week",
                                show_legend=True,
                                curve="smooth",
                                height=265,
                            )

                with Card(css_class="win-panel flex-1"):
                    with CardHeader():
                        CardTitle("Open Issue Age by Type", css_class="group-caption")
                    with CardContent():
                        with Div(css_class="win-inset"):
                            BarChart(
                                data=age_chart_data,
                                series=[
                                    ChartSeries(data_key="bug", label="Bug", color="#b22222"),
                                    ChartSeries(data_key="enhancement", label="Enhancement", color="#245edb"),
                                    ChartSeries(data_key="other", label="Other", color="#707070"),
                                ],
                                x_axis="age_bucket",
                                stacked=True,
                                show_legend=True,
                                height=265,
                            )

            with Row(gap=3, css_class="mt-3"):
                with Card(css_class="win-panel flex-1"):
                    with CardHeader():
                        CardTitle("Median Days to Close by Label", css_class="group-caption")
                    with CardContent():
                        with Div(css_class="win-inset"):
                            BarChart(
                                data=close_by_label,
                                series=[ChartSeries(data_key="median_days_to_close", label="Days", color="#0a246a")],
                                x_axis="label_name",
                                horizontal=True,
                                show_legend=False,
                                height=280,
                            )

                with Card(css_class="win-panel flex-1"):
                    with CardHeader():
                        CardTitle("Triage Health", css_class="group-caption")
                    with CardContent():
                        with Div(css_class="win-inset"):
                            for label, value in [
                                ("Labeled", triage["pct_labeled"]),
                                ("Typed", triage["pct_typed"]),
                                ("Assigned", triage["pct_assigned"]),
                                ("Milestoned", triage["pct_milestoned"]),
                            ]:
                                Badge(f"{label}: {int(value)}%", variant="outline")

            with Row(gap=3, css_class="mt-3"):
                with Card(css_class="win-panel flex-1"):
                    with CardHeader():
                        CardTitle("Open Issues by Assignee", css_class="group-caption")
                    with CardContent():
                        with Div(css_class="win-inset"):
                            BarChart(
                                data=assignee_workload,
                                series=[
                                    ChartSeries(data_key="bugs", label="Bugs", color="#b22222"),
                                    ChartSeries(data_key="enhancements", label="Enhancements", color="#245edb"),
                                ],
                                x_axis="assignee_login",
                                stacked=True,
                                horizontal=True,
                                show_legend=True,
                                height=320,
                            )

                with Card(css_class="win-panel flex-1"):
                    with CardHeader():
                        CardTitle("Community Priorities", css_class="group-caption")
                        Muted("Most-reacted open issues")
                    with CardContent():
                        with Div(css_class="win-inset"):
                            for issue in community_priorities[:8]:
                                with Div(css_class="priority-row"):
                                    Text(f"#{issue['issue_number']} {issue['title'][:58]}", style={"font-weight": "700"})
                                    Text(
                                        f"{issue['issue_category']} | {issue['reactions_total_count']} reactions | {issue['age_days']} days old",
                                        css_class="priority-meta",
                                    )

            with Card(css_class="win-panel mt-3"):
                with CardHeader():
                    CardTitle("Oldest Open Issues", css_class="group-caption")
                with CardContent():
                    with Div(css_class="win-inset"):
                        DataTable(
                            data=open_issues_table[:25],
                            columns=[
                                DataTableColumn(key="#", header="#", sortable=True),
                                DataTableColumn(key="title", header="Title"),
                                DataTableColumn(key="type", header="Type", sortable=True),
                                DataTableColumn(key="age_days", header="Age", sortable=True),
                                DataTableColumn(key="reactions", header="Reactions", sortable=True),
                                DataTableColumn(key="comments", header="Comments", sortable=True),
                            ],
                            search=True,
                            pagination=10,
                        )

        with Div(css_class="status-bar"):
            Span("Ready", css_class="status-segment")
            Span(f"{summary['open_issues']} issues loaded", css_class="status-segment")
            Span(f"{triage['unlabeled_count']} unlabeled", css_class="status-segment")
            Span("DuckDB workspace", css_class="status-segment")
