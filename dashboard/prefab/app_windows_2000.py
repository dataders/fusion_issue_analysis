"""
Prefab dashboard for dbt-fusion issue analytics.
Windows 2000 desktop app edition.
"""

import os

import duckdb
from prefab_ui.app import PrefabApp, Theme
from prefab_ui.components import (
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


summary_cards = query("SELECT * FROM summary_kpis")[0]
triage = query("SELECT * FROM triage_health")[0]
cumulative_flow = query("SELECT * FROM cumulative_flow")
response_pctiles = query("SELECT * FROM response_pctiles")
bug_velocity = query("SELECT * FROM bug_velocity")
enh_velocity = query("SELECT * FROM enh_velocity")
age_dist = query("SELECT * FROM age_distribution")
assignee_workload = query("SELECT * FROM assignee_workload")
community_priorities = query("SELECT * FROM community_priorities")
open_issues_table = query("SELECT * FROM open_issues_table")
leaderboard = query("SELECT * FROM leaderboard")

net_flow = summary_cards["closed_4w"] - summary_cards["opened_4w"]
net_flow_sign = "+" if net_flow > 0 else ""

velocity_map: dict[str, dict] = {}
for row in bug_velocity:
    velocity_map[row["week"]] = {
        "week": row["week"],
        "bugs": row["median_days"],
        "enhancements": None,
    }
for row in enh_velocity:
    if row["week"] not in velocity_map:
        velocity_map[row["week"]] = {
            "week": row["week"],
            "bugs": None,
            "enhancements": row["median_days"],
        }
    else:
        velocity_map[row["week"]]["enhancements"] = row["median_days"]
velocity_data = sorted(velocity_map.values(), key=lambda item: item["week"])

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

open_issues_preview = open_issues_table[:25]
priority_preview = community_priorities[:8]
leaderboard_preview = leaderboard[:10]
workload_preview = assignee_workload[:10]

response_sla = summary_cards["pct_responded_48h"]
median_close = summary_cards["rolling_median_close_days"]

WIN2K_CSS = """
body {
    background:
        linear-gradient(135deg, rgba(255, 255, 255, 0.10), rgba(255, 255, 255, 0) 30%),
        linear-gradient(180deg, #1957a8 0%, #2668b5 45%, #0f4d9d 100%) !important;
    color: #000 !important;
    font-family: Tahoma, "MS Sans Serif", sans-serif !important;
}

#root {
    color: #000 !important;
}

.win-window {
    background: #c3c7cb !important;
    border-top: 2px solid #ffffff !important;
    border-left: 2px solid #ffffff !important;
    border-right: 2px solid #404040 !important;
    border-bottom: 2px solid #404040 !important;
    box-shadow:
        1px 1px 0 #808080,
        10px 16px 28px rgba(0, 0, 0, 0.35) !important;
}

.title-bar {
    align-items: center;
    background: linear-gradient(90deg, #0a246a 0%, #2b63b5 100%) !important;
    color: #ffffff !important;
    display: flex;
    justify-content: space-between;
    min-height: 30px;
    padding: 5px 8px;
}

.title-bar span,
.title-bar p {
    color: #ffffff !important;
}

.title-text {
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.01em;
}

.window-buttons {
    display: flex;
    gap: 4px;
}

.window-button {
    align-items: center;
    background: #d4d0c8 !important;
    border-top: 1px solid #ffffff !important;
    border-left: 1px solid #ffffff !important;
    border-right: 1px solid #404040 !important;
    border-bottom: 1px solid #404040 !important;
    color: #000000 !important;
    display: inline-flex;
    font-size: 11px;
    font-weight: 700;
    height: 18px;
    justify-content: center;
    min-width: 18px;
}

.menu-bar,
.toolbar,
.status-bar {
    background: #d4d0c8 !important;
}

.menu-bar {
    border-bottom: 1px solid #9b9b9b;
    padding: 4px 8px 5px;
}

.menu-item {
    color: #000000 !important;
    display: inline-block;
    font-size: 12px;
    margin-right: 18px;
}

.toolbar {
    align-items: center;
    border-top: 1px solid #ece9d8;
    border-bottom: 1px solid #9b9b9b;
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    padding: 6px 8px;
}

.toolbar-button {
    align-items: center;
    background: #d4d0c8 !important;
    border-top: 1px solid #ffffff !important;
    border-left: 1px solid #ffffff !important;
    border-right: 1px solid #7b7b7b !important;
    border-bottom: 1px solid #7b7b7b !important;
    color: #000000 !important;
    display: inline-flex;
    font-size: 11px;
    gap: 6px;
    padding: 3px 8px;
}

.toolbar-icon {
    background: #0a246a;
    border: 1px solid #ffffff;
    box-shadow: 1px 1px 0 #7b7b7b;
    display: inline-block;
    height: 11px;
    width: 11px;
}

.toolbar-divider {
    background: #9b9b9b;
    display: inline-block;
    height: 22px;
    margin: 0 2px;
    width: 1px;
}

.workspace {
    background: #3a6ea5 !important;
    padding: 12px;
}

.win-panel {
    background: #d4d0c8 !important;
    border-top: 1px solid #ffffff !important;
    border-left: 1px solid #ffffff !important;
    border-right: 1px solid #808080 !important;
    border-bottom: 1px solid #808080 !important;
    box-shadow:
        inset 1px 1px 0 #f5f5f5,
        inset -1px -1px 0 #b4b4b4 !important;
}

.win-panel .pf-card-header,
.win-panel .pf-card-content,
.win-panel .pf-card-title {
    color: #000000 !important;
}

.group-caption {
    color: #000000 !important;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.02em;
    text-transform: uppercase;
}

.win-inset {
    background: #ffffff !important;
    border-top: 2px solid #808080 !important;
    border-left: 2px solid #808080 !important;
    border-right: 2px solid #ffffff !important;
    border-bottom: 2px solid #ffffff !important;
    box-shadow: inset 1px 1px 0 #d0d0d0;
}

.nav-item {
    border: 1px solid transparent;
    color: #000000 !important;
    display: block;
    font-size: 12px;
    margin-bottom: 4px;
    padding: 6px 8px;
}

.nav-item.active {
    background: #0a246a !important;
    color: #ffffff !important;
    font-weight: 700;
}

.nav-item.active span,
.nav-item.active p {
    color: #ffffff !important;
}

.nav-tree-dot {
    background: #0a246a;
    border: 1px solid #7b7b7b;
    display: inline-block;
    height: 8px;
    margin-right: 8px;
    width: 8px;
}

.inner-tabs {
    align-items: end;
    display: flex;
    gap: 4px;
    margin-bottom: 8px;
}

.inner-tab {
    background: #d4d0c8 !important;
    border-top: 1px solid #ffffff !important;
    border-left: 1px solid #ffffff !important;
    border-right: 1px solid #7b7b7b !important;
    border-bottom: 1px solid #7b7b7b !important;
    color: #000000 !important;
    display: inline-block;
    font-size: 11px;
    padding: 5px 10px 4px;
}

.inner-tab.active {
    background: #ffffff !important;
    border-bottom: 1px solid #ffffff !important;
    font-weight: 700;
    position: relative;
    top: 1px;
}

.kpi-box {
    min-height: 90px;
}

.kpi-label {
    color: #404040 !important;
    font-size: 11px;
    text-transform: uppercase;
}

.kpi-value {
    color: #000000 !important;
    font-size: 28px;
    font-weight: 700;
    line-height: 1.1;
}

.kpi-detail {
    color: #404040 !important;
    font-size: 11px;
}

.shell-title {
    color: #000000 !important;
    font-size: 26px;
    font-weight: 700;
    line-height: 1.1;
}

.shell-subtitle {
    color: #404040 !important;
    font-size: 12px;
}

.priority-row,
.leader-row {
    border-bottom: 1px solid #d7d7d7;
    color: #000000 !important;
    font-size: 12px;
    padding: 6px 0;
}

.priority-row:last-child,
.leader-row:last-child {
    border-bottom: none;
}

.priority-meta,
.status-mini {
    color: #5a5a5a !important;
    font-size: 11px;
}

.status-bar {
    border-top: 1px solid #808080;
    padding: 4px 6px;
}

.status-segment {
    background: #d4d0c8 !important;
    border-top: 1px solid #808080 !important;
    border-left: 1px solid #808080 !important;
    border-right: 1px solid #ffffff !important;
    border-bottom: 1px solid #ffffff !important;
    color: #000000 !important;
    display: inline-block;
    font-size: 11px;
    margin-right: 6px;
    min-height: 20px;
    padding: 3px 8px;
}

.pane-note {
    color: #4f4f4f !important;
    font-size: 11px;
}

.win-window table,
.win-window th,
.win-window td,
.win-window input,
.win-window button,
.win-window select,
.win-window label {
    font-family: Tahoma, "MS Sans Serif", sans-serif !important;
}

.win-window th {
    background: #d4d0c8 !important;
}
"""

WIN2K_THEME = Theme(
    mode="light",
    font="Tahoma",
    css=WIN2K_CSS,
    accent="#0a246a",
)


with PrefabApp(
    css_class="mx-auto p-4",
    theme=WIN2K_THEME,
) as app:
    with Div(css_class="win-window", style={"max-width": "1440px", "margin": "0 auto"}):
        with Div(css_class="title-bar"):
            Span("Fusion Issue Explorer", css_class="title-text")
            with Div(css_class="window-buttons"):
                Span("_", css_class="window-button")
                Span("[]", css_class="window-button")
                Span("X", css_class="window-button")

        with Div(css_class="menu-bar"):
            Span("File", css_class="menu-item")
            Span("Edit", css_class="menu-item")
            Span("View", css_class="menu-item")
            Span("Go", css_class="menu-item")
            Span("Tools", css_class="menu-item")
            Span("Help", css_class="menu-item")

        with Div(css_class="toolbar"):
            with Div(css_class="toolbar-button"):
                Span("", css_class="toolbar-icon")
                Span("Refresh")
            with Div(css_class="toolbar-button"):
                Span("", css_class="toolbar-icon")
                Span("Backlog")
            with Div(css_class="toolbar-button"):
                Span("", css_class="toolbar-icon")
                Span("Owners")
            Span("", css_class="toolbar-divider")
            with Div(css_class="toolbar-button"):
                Span("", css_class="toolbar-icon")
                Span("Export")
            with Div(css_class="toolbar-button"):
                Span("", css_class="toolbar-icon")
                Span("Inspect")

        with Div(css_class="workspace"):
            with Row(gap=3):
                with Card(
                    css_class="win-panel",
                    style={"width": "260px", "flex-shrink": "0", "align-self": "stretch"},
                ):
                    with CardHeader():
                        CardTitle("Navigation", css_class="group-caption")
                    with CardContent():
                        with Div(css_class="win-inset", style={"padding": "10px", "margin-bottom": "12px"}):
                            with Div(css_class="nav-item active"):
                                Span("", css_class="nav-tree-dot")
                                Span("Summary")
                            with Div(css_class="nav-item"):
                                Span("", css_class="nav-tree-dot")
                                Span("Issue Queue")
                            with Div(css_class="nav-item"):
                                Span("", css_class="nav-tree-dot")
                                Span("Workflow")
                            with Div(css_class="nav-item"):
                                Span("", css_class="nav-tree-dot")
                                Span("Contributors")

                        Text("Backlog workstation", css_class="pane-note")
                        Text(f"Open issues: {summary_cards['open_issues']}", css_class="status-mini")
                        Text(
                            f"Response SLA: {int(response_sla)}%" if response_sla is not None else "Response SLA: N/A",
                            css_class="status-mini",
                        )
                        Text(f"Unlabeled queue: {triage['unlabeled_count']}", css_class="status-mini")

                    with CardHeader():
                        CardTitle("System", css_class="group-caption")
                    with CardContent():
                        with Div(css_class="win-inset", style={"padding": "10px"}):
                            Text("Mode: static export", css_class="status-mini")
                            Text("Runtime: Prefab renderer", css_class="status-mini")
                            Text("Source: DuckDB analytics layer", css_class="status-mini")
                            Text("Shell: Windows 2000", css_class="status-mini")

                with Div(style={"flex": "1", "min-width": "0"}):
                    H2("Fusion Issue Explorer", css_class="shell-title")
                    Text(
                        "dbt-fusion backlog shell with old desktop chrome over live repo metrics",
                        css_class="shell-subtitle",
                    )

                    with Div(css_class="inner-tabs mt-3"):
                        Span("Summary", css_class="inner-tab active")
                        Span("Backlog", css_class="inner-tab")
                        Span("Workflow", css_class="inner-tab")
                        Span("Contributors", css_class="inner-tab")

                    with Div(css_class="win-inset", style={"padding": "10px"}):
                        with Row(gap=3):
                            with Card(css_class="win-panel flex-1 kpi-box"):
                                with CardHeader():
                                    CardTitle("Net Flow", css_class="kpi-label")
                                with CardContent():
                                    H3(f"{net_flow_sign}{net_flow}", css_class="kpi-value")
                                    Text(
                                        f"{summary_cards['opened_4w']} opened / {summary_cards['closed_4w']} closed",
                                        css_class="kpi-detail",
                                    )

                            with Card(css_class="win-panel flex-1 kpi-box"):
                                with CardHeader():
                                    CardTitle("Open Issues", css_class="kpi-label")
                                with CardContent():
                                    H3(str(summary_cards["open_issues"]), css_class="kpi-value")
                                    Text("Current queue depth", css_class="kpi-detail")

                            with Card(css_class="win-panel flex-1 kpi-box"):
                                with CardHeader():
                                    CardTitle("Median Close", css_class="kpi-label")
                                with CardContent():
                                    H3(
                                        f"{median_close}d" if median_close is not None else "N/A",
                                        css_class="kpi-value",
                                    )
                                    Text("Rolling 4 week median", css_class="kpi-detail")

                            with Card(css_class="win-panel flex-1 kpi-box"):
                                with CardHeader():
                                    CardTitle("Stale Issues", css_class="kpi-label")
                                with CardContent():
                                    H3(str(summary_cards["stale_count"]), css_class="kpi-value")
                                    Text("No activity for 30+ days", css_class="kpi-detail")

                    with Row(gap=3, css_class="mt-3"):
                        with Card(css_class="win-panel flex-1"):
                            with CardHeader():
                                CardTitle("Workflow Gap", css_class="group-caption")
                                Muted("Cumulative issue flow")
                            with CardContent():
                                with Div(css_class="win-inset", style={"padding": "8px"}):
                                    AreaChart(
                                        data=cumulative_flow,
                                        series=[
                                            ChartSeries(
                                                data_key="cumulative_opened",
                                                label="Opened",
                                                color="#245edb",
                                            ),
                                            ChartSeries(
                                                data_key="cumulative_closed",
                                                label="Closed",
                                                color="#2f7d32",
                                            ),
                                        ],
                                        x_axis="week",
                                        show_legend=True,
                                        height=290,
                                    )

                        with Card(css_class="win-panel flex-1"):
                            with CardHeader():
                                CardTitle("Response Console", css_class="group-caption")
                                Muted("Time to first response")
                            with CardContent():
                                with Div(css_class="win-inset", style={"padding": "8px"}):
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
                                        height=290,
                                    )

                    with Row(gap=3, css_class="mt-3"):
                        with Card(css_class="win-panel flex-1"):
                            with CardHeader():
                                CardTitle("Aging Buckets", css_class="group-caption")
                                Muted("Open issue age by type")
                            with CardContent():
                                with Div(css_class="win-inset", style={"padding": "8px"}):
                                    BarChart(
                                        data=age_chart_data,
                                        series=[
                                            ChartSeries(data_key="bug", label="Bug", color="#b22222"),
                                            ChartSeries(
                                                data_key="enhancement",
                                                label="Enhancement",
                                                color="#245edb",
                                            ),
                                            ChartSeries(data_key="other", label="Other", color="#707070"),
                                        ],
                                        x_axis="age_bucket",
                                        stacked=True,
                                        show_legend=True,
                                        height=265,
                                    )

                        with Card(css_class="win-panel flex-1"):
                            with CardHeader():
                                CardTitle("Close Velocity", css_class="group-caption")
                                Muted("Median days to close")
                            with CardContent():
                                with Div(css_class="win-inset", style={"padding": "8px"}):
                                    LineChart(
                                        data=velocity_data,
                                        series=[
                                            ChartSeries(data_key="bugs", label="Bugs", color="#b22222"),
                                            ChartSeries(
                                                data_key="enhancements",
                                                label="Enhancements",
                                                color="#245edb",
                                            ),
                                        ],
                                        x_axis="week",
                                        show_legend=True,
                                        curve="smooth",
                                        height=265,
                                    )

                    with Row(gap=3, css_class="mt-3"):
                        with Card(css_class="win-panel", style={"flex": "1.4", "min-width": "0"}):
                            with CardHeader():
                                CardTitle("Issue Queue", css_class="group-caption")
                                Muted("Oldest open issues")
                            with CardContent():
                                with Div(css_class="win-inset", style={"padding": "8px"}):
                                    DataTable(
                                        data=open_issues_preview,
                                        columns=[
                                            DataTableColumn(key="#", header="#", sortable=True),
                                            DataTableColumn(key="title", header="Title"),
                                            DataTableColumn(key="type", header="Type", sortable=True),
                                            DataTableColumn(key="age_days", header="Age", sortable=True),
                                            DataTableColumn(
                                                key="reactions",
                                                header="Reactions",
                                                sortable=True,
                                            ),
                                            DataTableColumn(
                                                key="comments",
                                                header="Comments",
                                                sortable=True,
                                            ),
                                        ],
                                        search=True,
                                        pagination=10,
                                    )

                        with Div(style={"flex": "0.85", "min-width": "280px"}):
                            with Card(css_class="win-panel"):
                                with CardHeader():
                                    CardTitle("Priority Inbox", css_class="group-caption")
                                    Muted("Most-reacted open issues")
                                with CardContent():
                                    with Div(css_class="win-inset", style={"padding": "10px"}):
                                        for issue in priority_preview:
                                            with Div(css_class="priority-row"):
                                                Text(
                                                    f"#{issue['issue_number']} {issue['title'][:58]}",
                                                    style={"font-weight": "700"},
                                                )
                                                Text(
                                                    f"{issue['issue_category']}  |  {issue['reactions_total_count']} reactions  |  {issue['age_days']} days old",
                                                    css_class="priority-meta",
                                                )

                            with Card(css_class="win-panel mt-3"):
                                with CardHeader():
                                    CardTitle("Owners", css_class="group-caption")
                                    Muted("Open issue load by assignee")
                                with CardContent():
                                    with Div(css_class="win-inset", style={"padding": "8px"}):
                                        BarChart(
                                            data=workload_preview,
                                            series=[
                                                ChartSeries(data_key="bugs", label="Bugs", color="#b22222"),
                                                ChartSeries(
                                                    data_key="enhancements",
                                                    label="Enhancements",
                                                    color="#245edb",
                                                ),
                                            ],
                                            x_axis="assignee_login",
                                            stacked=True,
                                            horizontal=True,
                                            show_legend=True,
                                            height=300,
                                        )

                    with Card(css_class="win-panel mt-3"):
                        with CardHeader():
                            CardTitle("Contributor Rank", css_class="group-caption")
                            Muted("Top issue closers")
                        with CardContent():
                            with Div(css_class="win-inset", style={"padding": "10px"}):
                                with Row(gap=3):
                                    with Div(style={"flex": "1"}):
                                        for row in leaderboard_preview[:5]:
                                            with Div(css_class="leader-row"):
                                                Text(
                                                    f"{row['author_login']}",
                                                    style={"font-weight": "700"},
                                                )
                                                Text(
                                                    f"{row['issues_closed']} issues closed",
                                                    css_class="priority-meta",
                                                )
                                    with Div(style={"flex": "1"}):
                                        for row in leaderboard_preview[5:10]:
                                            with Div(css_class="leader-row"):
                                                Text(
                                                    f"{row['author_login']}",
                                                    style={"font-weight": "700"},
                                                )
                                                Text(
                                                    f"{row['issues_closed']} issues closed",
                                                    css_class="priority-meta",
                                                )

        with Div(css_class="status-bar"):
            Span("Ready", css_class="status-segment")
            Span(f"{summary_cards['open_issues']} issues loaded", css_class="status-segment")
            Span(f"{triage['unlabeled_count']} unlabeled", css_class="status-segment")
            Span("DuckDB workspace", css_class="status-segment")
