"""
Prefab dashboard for dbt v2 issue health.
Windows 2000 desktop app edition.

Renders the tile contract in dashboard/tiles.yml (sections, tiles, palette)
from the dbt dashboard models. Layout and chrome only — no metric logic here.
"""

import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tiles
from prefab_ui.actions import OpenLink
from prefab_ui.app import PrefabApp, Theme
from prefab_ui.components import (
    H2,
    H3,
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    DataTable,
    DataTableColumn,
    Div,
    Muted,
    Row,
    Span,
    Text,
)
from prefab_ui.components.charts import (
    AreaChart,
    BarChart,
    ChartSeries,
    LineChart,
)

MODE = "light"


# ── Data (dashboard models only; see tiles.yml) ─────────────────────

def clean(rows: list[dict]) -> list[dict]:
    """NaN -> None so the baked-in JSON stays valid."""
    return [{k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in r.items()} for r in rows]


def rows(tile_id: str) -> list[dict]:
    return clean(tiles.tile_rows(tile_id))


def wide(tile_id: str, index: str, column: str = "issue_category", value: str = "issue_count") -> list[dict]:
    pivoted = tiles.pivot(rows(tile_id), index=index, column=column, value=value)
    return [{(k if k == index else safe_key(k)): v for k, v in r.items()} for r in pivoted]


def safe_key(name: str) -> str:
    """Series keys become CSS variables in the renderer; '180d+' would break them."""
    return re.sub(r"\W", "_", str(name))


meta = tiles.one("dashboard_meta")
FRESHNESS = tiles.freshness_note(meta)
IS_STALE = meta["days_stale"] > tiles.MANIFEST["meta"]["stale_after_days"]
KPIS = tiles.kpis()  # headline_kpis, formatted per tiles.yml

DATA = {
    "backlog_weekly": wide("backlog_weekly", "week", value="open_issues"),
    "weekly_flow": rows("weekly_flow"),
    "triage_pipeline": wide("triage_pipeline", "status_label", column="age_bucket"),
    "response_weekly": rows("response_weekly"),
    "triage_queue": rows("triage_queue"),
    "open_by_area": wide("open_by_area", "area"),
    "open_by_adapter": wide("open_by_adapter", "adapter"),
    "epic_progress": rows("epic_progress"),
    "top_requested": rows("top_requested"),
    "assignee_workload": wide("assignee_workload", "assignee_login"),
}


def series(palette_key: str, data: list[dict]) -> list[ChartSeries]:
    """One series per palette entry present in the data, in palette order."""
    present = set().union(*(r.keys() for r in data)) if data else set()
    return [
        ChartSeries(data_key=safe_key(k), label=tiles.label(palette_key, k), color=tiles.color(palette_key, k, MODE))
        for k in tiles.categories(palette_key)
        if safe_key(k) in present
    ]


HEADERS = {
    "issue_number": "#", "epic_number": "#", "title": "Title", "issue_category": "Type",
    "age_days": "Age (d)", "days_idle": "Idle (d)", "reactions": "Reactions", "comments": "Comments",
    "is_customer_reported": "Customer", "areas": "Areas", "triage_status": "Triage",
    "child_closed": "Closed", "child_total": "Sub-issues", "pct_complete": "% done",
    "milestone_title": "Milestone",
}
SORTABLE = {"issue_number", "epic_number", "age_days", "days_idle", "reactions", "comments",
            "child_closed", "child_total", "pct_complete", "issue_category"}


# Long issue titles wrap instead of pushing the numeric columns off-screen.
TITLE_COLUMN = {"min_width": "240px", "max_width": "480px", "cell_class": "whitespace-normal"}


def display(key: str, value):
    if value is None or value == "":
        return "—"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if key == "issue_category":
        return tiles.label("issue_category", value)
    if key == "triage_status":
        return str(value).replace("_", " ")
    return value


# ══════════════════════════════════════════════════════════════════
#  WINDOWS 2000 CSS THEME
# ══════════════════════════════════════════════════════════════════

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
.section-caption { display: block; color: #fff !important; font-size: 15px; font-weight: 700; margin-top: 18px; }
.kpi-label { color: #404040 !important; font-size: 11px; text-transform: uppercase; }
.kpi-value { color: #000 !important; font-size: 28px; font-weight: 700; line-height: 1.1; }
.kpi-detail, .status-mini { color: #404040 !important; font-size: 11px; }
.shell-title { color: #fff !important; font-size: 26px; font-weight: 700; line-height: 1.1; }
.shell-subtitle { display: block; color: #e8eef8 !important; font-size: 12px; }
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
.msgbox {
    background: #d4d0c8 !important;
    border-top: 2px solid #fff !important;
    border-left: 2px solid #fff !important;
    border-right: 2px solid #404040 !important;
    border-bottom: 2px solid #404040 !important;
    color: #000 !important;
    font-size: 12px;
    margin-top: 10px;
    padding: 8px 10px;
}
.msgbox span { color: #000 !important; }
"""

WIN2K_THEME = Theme(mode="light", font="Tahoma", css=WIN2K_CSS, accent="#0a246a")


# ══════════════════════════════════════════════════════════════════
#  TILE RENDERERS (keyed by tile id in tiles.yml)
# ══════════════════════════════════════════════════════════════════

def text_bar(pct) -> str:
    """pct_complete (0-100) as a 10-cell text bar. DataTable renders component
    cells outside the table in this Prefab version, so the bar is text."""
    filled = round((pct or 0) / 10)
    return "█" * filled + "░" * (10 - filled)


def bar_height(data: list[dict]) -> int:
    return max(220, 32 * len(data) + 60)


def kpi_card(title: str, value: str, detail: str) -> None:
    with Card(css_class="win-panel flex-1", style={"min-width": "150px"}):
        with CardHeader():
            CardTitle(title, css_class="kpi-label")
        with CardContent():
            H3(value, css_class="kpi-value")
            Text(detail or " ", css_class="kpi-detail")


def issue_table(tile: dict, data: list[dict], bar_key: str | None = None) -> None:
    """DataTable (Details view); click a row to open the issue on GitHub."""
    columns = tile["columns"]
    table_rows = []
    for r in data:
        row = {c: display(c, r[c]) for c in columns}
        row["issue_url"] = r["issue_url"]
        if bar_key:
            row["_bar"] = text_bar(r[bar_key])
        table_rows.append(row)
    DataTable(
        rows=table_rows,
        columns=[
            DataTableColumn(key=c, header=HEADERS.get(c, c), sortable=c in SORTABLE,
                            **TITLE_COLUMN if c == "title" else {})
            for c in columns
        ] + ([DataTableColumn(key="_bar", header="Progress", min_width="140px", cell_class="font-mono whitespace-nowrap")] if bar_key else []),
        search=True,
        paginated=True,
        page_size=10,
        on_row_click=OpenLink("{{ $event.issue_url }}"),
    )


def render_backlog_weekly(tile: dict) -> None:
    data = DATA["backlog_weekly"]
    AreaChart(data=data, series=series("issue_category", data), x_axis="week",
              stacked=True, show_legend=True, height=285)


def render_weekly_flow(tile: dict) -> None:
    data = DATA["weekly_flow"]
    BarChart(data=data, series=series("flow", data), x_axis="week", show_legend=True, height=285)


def render_triage_pipeline(tile: dict) -> None:
    data = DATA["triage_pipeline"]
    BarChart(data=data, series=series("age_bucket", data), x_axis="status_label",
             stacked=True, horizontal=True, show_legend=True, height=bar_height(data))


def render_response_weekly(tile: dict) -> None:
    LineChart(
        data=DATA["response_weekly"],
        series=[ChartSeries(data_key="pct_responded_48h", label="% answered within 48h",
                            color=tiles.MANIFEST["palette"]["single_series"])],
        x_axis="week", show_legend=False, curve="linear", height=265,
    )


def render_stacked_category_bar(key: str, y: str):
    def render(tile: dict) -> None:
        data = DATA[key]
        BarChart(data=data, series=series("issue_category", data), x_axis=y,
                 stacked=True, horizontal=True, show_legend=True, height=bar_height(data))
    return render


RENDER = {
    "backlog_weekly": render_backlog_weekly,
    "weekly_flow": render_weekly_flow,
    "triage_pipeline": render_triage_pipeline,
    "response_weekly": render_response_weekly,
    "triage_queue": lambda t: issue_table(t, DATA["triage_queue"]),
    "open_by_area": render_stacked_category_bar("open_by_area", "area"),
    "open_by_adapter": render_stacked_category_bar("open_by_adapter", "adapter"),
    "epic_progress": lambda t: issue_table(t, DATA["epic_progress"], bar_key="pct_complete"),
    "top_requested": lambda t: issue_table(t, DATA["top_requested"]),
    "assignee_workload": render_stacked_category_bar("assignee_workload", "assignee_login"),
}

# Tables and long bar lists get a full-width window; charts sit two per row.
FULL_WIDTH = {"triage_queue", "epic_progress", "top_requested"}


def tile_window(tile: dict) -> None:
    with Card(css_class="win-panel flex-1", style={"min-width": "360px"}):
        with CardHeader():
            CardTitle(tile["title"], css_class="group-caption")
            Muted(tile["subtitle"])
        with CardContent():
            with Div(css_class="win-inset"):
                RENDER[tile["id"]](tile)


def flush(pending: list[dict]) -> None:
    """Lay out queued chart tiles two per row."""
    for i in range(0, len(pending), 2):
        with Row(gap=3, css_class="mt-2 flex-wrap"):
            for t in pending[i:i + 2]:
                tile_window(t)
    pending.clear()

# ══════════════════════════════════════════════════════════════════
#  BUILD DASHBOARD
# ══════════════════════════════════════════════════════════════════

with PrefabApp(title=f"{tiles.MANIFEST['title']} (Windows 2000)", css_class="mx-auto p-4", theme=WIN2K_THEME) as app:
    with Div(css_class="win-window", style={"max-width": "1440px", "margin": "0 auto"}):
        with Div(css_class="title-bar"):
            Span("v2 Issue Explorer")
            with Div():
                Span("_", css_class="window-button")
                Span("[]", css_class="window-button")
                Span("X", css_class="window-button")

        with Div(css_class="menu-bar"):
            for item in ["File", "Edit", "View", "Go", "Tools", "Help"]:
                Span(item, css_class="menu-item")

        with Div(css_class="workspace"):
            H2(tiles.MANIFEST["title"], css_class="shell-title")
            Text(tiles.MANIFEST["subtitle"], css_class="shell-subtitle")
            Text(FRESHNESS, css_class="shell-subtitle")

            if IS_STALE:
                with Div(css_class="msgbox"):
                    Span("⚠ v2 Issue Explorer — ", style={"font-weight": "700"})
                    Span(f"The data is {meta['days_stale']} days old. The extract may have stopped. [ OK ]")

            for section in tiles.sections():
                Text(section["question"], css_class="section-caption")
                pending: list[dict] = []

                for tile in section["tiles"]:
                    if tile["id"] == "headline_kpis":
                        with Row(gap=3, css_class="mt-2 flex-wrap"):
                            for k in KPIS:
                                kpi_card(k["label"], k["value"], k["context"])
                    elif tile["id"] in FULL_WIDTH:
                        flush(pending)
                        with Row(gap=3, css_class="mt-2"):
                            tile_window(tile)
                    else:
                        pending.append(tile)
                flush(pending)

        with Div(css_class="status-bar"):
            Span("Ready", css_class="status-segment")
            Span(f"{KPIS[0]['value']} open issues", css_class="status-segment")
            Span(f"{meta['source_repo']} · {meta['source_label']}", css_class="status-segment")
            Span(f"As of {str(meta['as_of_date'])[:10]}", css_class="status-segment")
            Span("DuckDB workspace", css_class="status-segment")
