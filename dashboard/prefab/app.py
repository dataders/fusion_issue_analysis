"""
Prefab dashboard for dbt Fusion (engine:v2) issue health.

A thin renderer over the tile contract in dashboard/tiles.yml: every section
and tile comes from the manifest, every number from a dbt dashboard model.
Adding a tile = add it to tiles.yml (and its model); no metric logic lives here.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import tiles  # noqa: E402
from prefab_ui.actions import OpenLink  # noqa: E402
from prefab_ui.app import PrefabApp  # noqa: E402
from prefab_ui.components import (  # noqa: E402
    Alert,
    AlertDescription,
    AlertTitle,
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    DataTable,
    DataTableColumn,
    Grid,
    H2,
    H3,
    Metric,
    Muted,
    Row,
)
from prefab_ui.components.charts import AreaChart, BarChart, ChartSeries, LineChart  # noqa: E402

COLUMN_HEADERS = {
    "issue_number": "#",
    "epic_number": "#",
    "title": "Title",
    "issue_category": "Type",
    "age_days": "Age (d)",
    "days_idle": "Idle (d)",
    "reactions": "👍",
    "comments": "💬",
    "is_customer_reported": "Customer",
    "triage_status": "Status",
    "areas": "Area / adapter",
    "child_closed": "Closed",
    "child_total": "Sub-issues",
    "pct_complete": "% done",
    "milestone_title": "Milestone",
}
NUMERIC = {"issue_number", "epic_number", "age_days", "days_idle", "reactions", "comments",
           "child_closed", "child_total", "pct_complete"}


def safe_key(name: str) -> str:
    """Prefab derives a CSS variable from each series key; '180d+' would break it."""
    return re.sub(r"\W", "_", str(name))


def series_for(palette_key: str, keys: list[str] | None = None) -> list[ChartSeries]:
    keys = keys or tiles.categories(palette_key)
    return [ChartSeries(data_key=safe_key(k), label=tiles.label(palette_key, k), color=tiles.color(palette_key, k))
            for k in keys]


def stacked(tile: dict, rows: list[dict], category_key: str, value_key: str) -> tuple[list[dict], list[ChartSeries]]:
    """Pivot a long model to one key per series, keeping only series present in the data."""
    palette_key = tile["color"]
    wide = [{(k if k == category_key else safe_key(k)): v for k, v in r.items()}
            for r in tiles.pivot(rows, index=category_key, column=palette_key, value=value_key)]
    present = {r[palette_key] for r in rows if r[value_key]}
    keys = [k for k in tiles.categories(palette_key) if k in present]
    return wide, series_for(palette_key, keys)


def display_rows(rows: list[dict], columns: list[str]) -> list[dict]:
    """Presentation-only formatting: booleans to marks, labels for enums."""
    out = []
    for r in rows:
        row = dict(r)
        for c in columns:
            if isinstance(row.get(c), bool):
                row[c] = "✓" if row[c] else ""
        if "issue_category" in row:
            row["issue_category"] = tiles.label("issue_category", row["issue_category"])
        if "triage_status" in row:
            row["triage_status"] = str(row["triage_status"]).replace("_", " ")
        out.append(row)
    return out


def render_tile(tile: dict) -> None:
    form = tile["form"]
    rows = tiles.tile_rows(tile["id"]) if form != "kpi_row" else []

    if form == "kpi_row":
        with Grid(columns={"default": 2, "md": 3, "lg": 6}, gap=3):
            for k in tiles.kpis():
                with Card():
                    with CardContent(css_class="pt-4"):
                        Metric(label=k["label"], value=k["value"], description=k["context"] or None)
        return

    with Card(css_class="h-full"):
        with CardHeader():
            CardTitle(tile["title"])
            Muted(tile["subtitle"])
        with CardContent():
            if form == "stacked_area":
                wide, series = stacked(tile, rows, tile["x"], tile["y"])
                AreaChart(data=wide, series=series, x_axis=tile["x"], stacked=True, show_legend=True, height=300)
            elif form == "grouped_bar":
                BarChart(data=rows, series=series_for("flow", tile["series"]), x_axis=tile["x"],
                         show_legend=True, height=300)
            elif form == "line":
                LineChart(data=rows, x_axis=tile["x"], show_legend=False, height=300,
                          series=[ChartSeries(data_key=tile["y"], label=tile["title"],
                                              color=tiles.MANIFEST["palette"]["single_series"])])
            elif form == "horizontal_stacked_bar":
                wide, series = stacked(tile, rows, tile["y"], tile["x"])
                BarChart(data=wide, series=series, x_axis=tile["y"], stacked=True, horizontal=True,
                         show_legend=True, height=max(220, 34 * len(wide)))
            elif form in ("table", "table_with_bar"):
                cols = tile["columns"]
                DataTable(
                    rows=display_rows(rows, cols),
                    columns=[
                        DataTableColumn(key=c, header=COLUMN_HEADERS.get(c, c), sortable=c in NUMERIC,
                                        align="right" if c in NUMERIC else None)
                        for c in cols
                    ],
                    search=True,
                    paginated=True,
                    page_size=10,
                    on_row_click=OpenLink("{{ $event." + tile["link"] + " }}"),
                )
            else:
                raise ValueError(f"Unknown tile form {form!r} in tiles.yml")


meta = tiles.one(tiles.MANIFEST["meta"]["model"])
is_stale = meta["days_stale"] > tiles.MANIFEST["meta"]["stale_after_days"]

# Tiles that sit side by side on wide screens; everything else is full width.
PAIRED_FORMS = {"stacked_area", "grouped_bar", "line", "horizontal_stacked_bar"}

with PrefabApp(css_class="max-w-7xl mx-auto p-6") as app:
    H2(tiles.MANIFEST["title"])
    Muted(tiles.MANIFEST["subtitle"])
    Muted(tiles.freshness_note(meta))
    if is_stale:
        with Alert(variant="warning", css_class="mt-3"):
            AlertTitle("Stale data")
            AlertDescription(
                f"The newest issue activity is {meta['days_stale']} days old. "
                "The extract has probably stopped — check the Extract GitHub Issues workflow."
            )

    for section in tiles.sections():
        H3(section["question"], css_class="mt-8 mb-3")
        pending: list[dict] = []
        for t in section["tiles"] + [None]:
            if t is not None and t["form"] in PAIRED_FORMS:
                pending.append(t)
                if len(pending) < 2:
                    continue
            if pending:
                with Grid(columns={"default": 1, "lg": len(pending)}, gap=4, css_class="mb-4"):
                    for p in pending:
                        render_tile(p)
                pending = []
            if t is not None and t["form"] not in PAIRED_FORMS:
                with Row(css_class="mb-4"):
                    with Grid(columns=1, css_class="w-full"):
                        render_tile(t)
