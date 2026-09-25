"""
Prefab dashboard — reactive variant.

Renders the tile contract in dashboard/tiles.yml from the dbt dashboard
models, plus client-side interactivity that only *selects* already-modeled
rows (it never re-aggregates):

- issue-type chips: hide/show type series in the stacked charts and filter
  the issue tables by type
- "customer-reported only" switch for the issue tables
- week window (all / 26 / 13 weeks) for the weekly trend tiles
- an issue drill-down dialog ("Details") on the issue tables; search and
  sortable columns on the epic table

Stays statically exportable (no server) so the GitHub Pages deploy keeps
working.
"""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tiles
from prefab_ui.actions import CallHandler, OpenLink
from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    H2,
    H3,
    Alert,
    AlertDescription,
    AlertTitle,
    Badge,
    Button,
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    DataTable,
    DataTableColumn,
    Dialog,
    Div,
    Link,
    Muted,
    Row,
    Select,
    SelectOption,
    Switch,
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
    Text,
)
from prefab_ui.components.charts import (
    AreaChart,
    BarChart,
    ChartSeries,
    LineChart,
)
from prefab_ui.components.control_flow import ForEach
from prefab_ui.rx import Rx

MODE = "light"
CATEGORIES = tiles.categories("issue_category")  # feature, bug, task, other


# ── Data (dashboard models only; see tiles.yml) ─────────────────────

def clean(rows: list[dict]) -> list[dict]:
    """NaN -> None so the baked-in JSON state stays valid."""
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


def with_type_label(data: list[dict]) -> list[dict]:
    return [{**r, "type": tiles.label("issue_category", r["issue_category"])} for r in data]


# Unfiltered rows per tile. The filter handler only slices / drops from these.
BASE = {
    "backlog_weekly": wide("backlog_weekly", "week", value="open_issues"),
    "weekly_flow": rows("weekly_flow"),
    "triage_pipeline": wide("triage_pipeline", "status_label", column="age_bucket"),
    "response_weekly": rows("response_weekly"),
    "triage_queue": with_type_label(rows("triage_queue")),
    "open_by_area": wide("open_by_area", "area"),
    "open_by_adapter": wide("open_by_adapter", "adapter"),
    "epic_progress": rows("epic_progress"),
    "top_requested": with_type_label(rows("top_requested")),
    "assignee_workload": wide("assignee_workload", "assignee_login"),
}

WEEKLY_TILES = ["backlog_weekly", "weekly_flow", "response_weekly"]
CATEGORY_CHART_TILES = ["backlog_weekly", "open_by_area", "open_by_adapter", "assignee_workload"]
ISSUE_TABLE_TILES = ["triage_queue", "top_requested"]

DEFAULT_FILTERS = {"categories": [], "customer_only": False, "weeks": "0"}


def series(palette_key: str, data: list[dict]) -> list[ChartSeries]:
    """One series per palette entry present in the data, in palette order."""
    present = set().union(*(r.keys() for r in data)) if data else set()
    return [
        ChartSeries(data_key=safe_key(k), label=tiles.label(palette_key, k), color=tiles.color(palette_key, k, MODE))
        for k in tiles.categories(palette_key)
        if safe_key(k) in present
    ]


# ══════════════════════════════════════════════════════════════════════════
#  JS HANDLERS — selection only (drop series keys, filter rows, slice weeks)
#  The renderer calls each handler with {state, event, arguments} and merges
#  the returned object into state.
# ══════════════════════════════════════════════════════════════════════════

JS_APPLY_FILTERS = f"""
({{ state, arguments: args = {{}} }}) => {{
  const f = state.filters || {{}};
  const cats = f.categories || [];
  const CATS = {json.dumps(CATEGORIES)};
  const keep = (c) => cats.length === 0 || cats.includes(c);
  const n = parseInt(f.weeks || '0', 10);
  const lastWeeks = (rows) => (n > 0 ? rows.slice(-n) : rows);
  const pickCats = (rows) => rows.map(r =>
    Object.fromEntries(Object.entries(r).filter(([k]) => !CATS.includes(k) || keep(k))));
  const pickIssues = (rows) => rows.filter(r =>
    keep(r.issue_category) && (!f.customer_only || r.is_customer_reported));
  const b = state.base;
  const out = {{}};
  for (const t of {json.dumps(CATEGORY_CHART_TILES)}) out[t] = pickCats(b[t]);
  for (const t of {json.dumps(WEEKLY_TILES)}) out[t] = lastWeeks(out[t] || b[t]);
  for (const t of {json.dumps(ISSUE_TABLE_TILES)}) out[t] = pickIssues(b[t]);
  out.chip = Object.fromEntries(CATS.map(c => [c, cats.includes(c) ? 'default' : 'outline']));
  out.filter_label = cats.length ? cats.join(', ') : 'all types';
  return out;
}}
"""

JS_TOGGLE_CATEGORY = """
({ state, arguments: args = {} }) => {
  const cur = (state.filters && state.filters.categories) || [];
  const next = cur.includes(args.value) ? cur.filter(v => v !== args.value) : [...cur, args.value];
  return { filters: { ...state.filters, categories: next } };
}
"""

JS_CLEAR_FILTERS = f"""
({{ state }}) => ({{ filters: {json.dumps(DEFAULT_FILTERS)} }})
"""

JS_OPEN_ISSUE = """
({ state, arguments: args = {} }) => ({
  selected_issue: (state.base[args.tile] || []).find(r => r.issue_number === Number(args.number)) || null,
  drill_open: true,
})
"""

INITIAL_STATE = {
    "base": BASE,
    **BASE,
    "filters": DEFAULT_FILTERS,
    "chip": {c: "outline" for c in CATEGORIES},
    "filter_label": "all types",
    "selected_issue": None,
    "drill_open": False,
}

APPLY = CallHandler("apply_filters")

# ══════════════════════════════════════════════════════════════════════════
#  TILE RENDERERS (keyed by tile id in tiles.yml)
# ══════════════════════════════════════════════════════════════════════════

HEADERS = {
    "issue_number": "#", "epic_number": "#", "title": "Title", "issue_category": "Type",
    "age_days": "Age (d)", "days_idle": "Idle (d)", "reactions": "Reactions", "comments": "Comments",
    "is_customer_reported": "Customer", "areas": "Areas", "triage_status": "Triage",
    "child_closed": "Closed", "child_total": "Sub-issues", "pct_complete": "% done",
    "milestone_title": "Milestone",
}
NUMERIC = {"issue_number", "epic_number", "age_days", "days_idle", "reactions", "comments",
           "child_closed", "child_total", "pct_complete"}


def text_bar(pct) -> str:
    """pct_complete (0-100) as a 10-cell text bar. DataTable renders component
    cells outside the table in this Prefab version, so the bar is text."""
    filled = round((pct or 0) / 10)
    return "█" * filled + "░" * (10 - filled)


def bar_height(data: list[dict]) -> int:
    return max(220, 32 * len(data) + 60)


def issue_table(tile: dict) -> None:
    """Rows come from state so the filters apply (DataTable can't bind rows
    to state in this Prefab version, so this is a ForEach over a Table).
    '#' links to GitHub; 'Details' opens the drill-down."""
    cols = tile["columns"]
    with Div(css_class="max-h-[520px] overflow-auto"):
        with Table():
            with TableHeader():
                with TableRow():
                    for c in cols:
                        TableHead(HEADERS.get(c, c), css_class="text-right" if c in NUMERIC else None)
                    TableHead("")
            with TableBody():
                with ForEach(tile["id"]) as item:
                    with TableRow():
                        for c in cols:
                            if c == "issue_number":
                                with TableCell():
                                    Link(f"#{item.issue_number}", href=item.issue_url, target="_blank")
                            elif c == "issue_category":
                                with TableCell():
                                    Badge(item.type, variant="secondary")
                            elif c == "is_customer_reported":
                                TableCell(item.is_customer_reported.then("yes", ""))
                            elif c == "title":
                                TableCell(item.title, css_class="max-w-[420px] truncate")
                            elif c == "triage_status":
                                TableCell(item.triage_status, css_class="text-xs")
                            else:
                                TableCell(item[c], css_class="text-right" if c in NUMERIC else None)
                        with TableCell():
                            Button("Details", variant="ghost", size="sm",
                                   on_click=CallHandler("open_issue", arguments={
                                       "tile": tile["id"], "number": item.issue_number}))
    Muted(f"{Rx(tile['id']).length()} of {len(BASE[tile['id']])} issues · {Rx('filter_label')}")


def epic_table(tile: dict) -> None:
    data = [
        {**{c: (r[c] if r[c] not in (None, "") else "—") for c in tile["columns"]},
         "issue_url": r["issue_url"],
         "progress": text_bar(r["pct_complete"])}
        for r in BASE["epic_progress"]
    ]
    DataTable(
        rows=data,
        columns=[
            DataTableColumn(key=c, header=HEADERS.get(c, c), sortable=c in NUMERIC,
                            align="right" if c in NUMERIC else None,
                            **({"min_width": "240px", "max_width": "480px", "cell_class": "whitespace-normal"}
                               if c == "title" else {}))
            for c in tile["columns"]
        ] + [DataTableColumn(key="progress", header="Progress", min_width="140px", cell_class="font-mono whitespace-nowrap")],
        search=True,
        paginated=True,
        page_size=10,
        on_row_click=OpenLink("{{ $event.issue_url }}"),
    )
    Muted("Click a row to open the epic on GitHub")


def category_bar(y: str):
    def render(tile: dict) -> None:
        BarChart(data=Rx(tile["id"]), series=series("issue_category", BASE[tile["id"]]), x_axis=y,
                 stacked=True, horizontal=True, show_legend=True, height=bar_height(BASE[tile["id"]]))
    return render


RENDER = {
    "backlog_weekly": lambda t: AreaChart(
        data=Rx("backlog_weekly"), series=series("issue_category", BASE["backlog_weekly"]),
        x_axis="week", stacked=True, show_legend=True, height=300),
    "weekly_flow": lambda t: BarChart(
        data=Rx("weekly_flow"), series=series("flow", BASE["weekly_flow"]),
        x_axis="week", show_legend=True, height=300),
    "triage_pipeline": lambda t: BarChart(
        data=BASE["triage_pipeline"], series=series("age_bucket", BASE["triage_pipeline"]),
        x_axis="status_label", stacked=True, horizontal=True, show_legend=True,
        height=bar_height(BASE["triage_pipeline"])),
    "response_weekly": lambda t: LineChart(
        data=Rx("response_weekly"),
        series=[ChartSeries(data_key="pct_responded_48h", label="% answered within 48h",
                            color=tiles.MANIFEST["palette"]["single_series"])],
        x_axis="week", show_legend=False, height=300),
    "triage_queue": issue_table,
    "open_by_area": category_bar("area"),
    "open_by_adapter": category_bar("adapter"),
    "epic_progress": epic_table,
    "top_requested": issue_table,
    "assignee_workload": category_bar("assignee_login"),
}

# Which filters a tile responds to (shown as badges so the scope is explicit).
FILTER_SCOPE = {
    **{t: "type" for t in CATEGORY_CHART_TILES},
    **{t: "type · customer" for t in ISSUE_TABLE_TILES},
}
for t in WEEKLY_TILES:
    FILTER_SCOPE[t] = " · ".join(x for x in [FILTER_SCOPE.get(t), "weeks"] if x)

# Charts that sit two-up; everything else is full width.
PAIRED = {"backlog_weekly", "weekly_flow", "triage_pipeline", "response_weekly",
          "open_by_area", "open_by_adapter"}


def tile_card(tile: dict) -> None:
    with Card(css_class="flex-1 min-w-[380px]"):
        with CardHeader():
            with Row(gap=2, css_class="items-center"):
                CardTitle(tile["title"])
                if tile["id"] in FILTER_SCOPE:
                    Badge(f"filters: {FILTER_SCOPE[tile['id']]}", variant="secondary")
                else:
                    Badge("not filtered", variant="outline")
            Muted(tile["subtitle"])
        with CardContent():
            RENDER[tile["id"]](tile)


# ══════════════════════════════════════════════════════════════════════════
#  BUILD DASHBOARD
# ══════════════════════════════════════════════════════════════════════════

with PrefabApp(
    title=f"{tiles.MANIFEST['title']} (reactive)",
    state=INITIAL_STATE,
    js_actions={
        "apply_filters": JS_APPLY_FILTERS,
        "toggle_category": JS_TOGGLE_CATEGORY,
        "clear_filters": JS_CLEAR_FILTERS,
        "open_issue": JS_OPEN_ISSUE,
    },
    css_class="max-w-7xl mx-auto p-6",
) as app:
    H2(f"{tiles.MANIFEST['title']} — Reactive")
    Muted(tiles.MANIFEST["subtitle"])
    Text(FRESHNESS, css_class="text-sm")
    if IS_STALE:
        with Alert(variant="warning", icon="triangle-alert", css_class="mt-2"):
            AlertTitle("Stale data")
            AlertDescription(f"The newest issue activity is {meta['days_stale']} days old — the extract may have stopped.")

    # ── Filter bar ──────────────────────────────────────────────────────
    with Card(css_class="mt-4 sticky top-2 z-10"):
        with CardContent(css_class="py-3"):
            with Row(gap=2, css_class="flex-wrap items-center"):
                Muted("Issue type:")
                for c in CATEGORIES:
                    Button(
                        tiles.label("issue_category", c),
                        variant=Rx(f"chip.{c}"),
                        size="sm",
                        on_click=[CallHandler("toggle_category", arguments={"value": c}), APPLY],
                    )
                Switch(name="filters.customer_only", label="Customer-reported only", on_change=[APPLY])
                with Select(name="filters.weeks", placeholder="Weeks", on_change=[APPLY], css_class="w-40"):
                    SelectOption(value="0", label="All weeks")
                    SelectOption(value="26", label="Last 26 weeks")
                    SelectOption(value="13", label="Last 13 weeks")
                Button("Clear", variant="ghost", size="sm", on_click=[CallHandler("clear_filters"), APPLY])
                Muted(f"Showing {Rx('filter_label')}", css_class="ml-auto")

    # ── Sections, in tiles.yml order ────────────────────────────────────
    for section in tiles.sections():
        H3(section["question"], css_class="mt-8")
        pending: list[dict] = []
        for tile in section["tiles"] + [None]:
            if tile is not None and tile["id"] in PAIRED:
                pending.append(tile)
                if len(pending) < 2:
                    continue
            if pending:
                with Row(gap=4, css_class="mt-3 flex-wrap"):
                    for p in pending:
                        tile_card(p)
                pending = []
            if tile is None or tile["id"] in PAIRED:
                continue
            if tile["id"] == "headline_kpis":
                with Row(gap=3, css_class="mt-3 flex-wrap"):
                    for k in KPIS:
                        with Card(css_class="flex-1 min-w-[120px]"):
                            with CardHeader():
                                CardTitle(k["label"], css_class="text-sm")
                            with CardContent():
                                H3(k["value"])
                                Muted(k["context"] or " ")
                Muted("Headline numbers are not affected by filters.", css_class="mt-1")
            else:
                with Row(gap=4, css_class="mt-3"):
                    tile_card(tile)

    # ── Drill-down dialog ───────────────────────────────────────────────
    with Dialog(
        name="drill_open",
        title=Rx("selected_issue.title"),
        description=f"#{Rx('selected_issue.issue_number')} · {Rx('selected_issue.type')}",
    ):
        # Hidden trigger: the dialog opens programmatically from a table row.
        Button("", css_class="hidden")

        with Row(gap=2, css_class="flex-wrap mt-2"):
            Badge(f"{Rx('selected_issue.reactions')} reactions", variant="secondary")
            Badge(f"{Rx('selected_issue.comments')} comments", variant="secondary")
            Badge(f"{Rx('selected_issue.age_days')} days old", variant="outline")
            Badge(f"idle {Rx('selected_issue.days_idle')} days", variant="outline")
            Badge(Rx("selected_issue.is_customer_reported").then("customer-reported", "community"), variant="outline")
        with Row(css_class="mt-4"):
            Button("View on GitHub", on_click=OpenLink(Rx("selected_issue.issue_url")))
