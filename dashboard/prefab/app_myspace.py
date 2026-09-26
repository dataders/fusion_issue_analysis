"""
~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~
    dbt v2 Issue Health Dashboard
    -=- MySpace Edition -=-
    Best viewed in Internet Explorer 6.0 at 800x600
~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~

Renders the tile contract in dashboard/tiles.yml (sections, tiles, palette)
from the dbt dashboard models. Layout and neon only — no metric logic here.
"""

import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tiles
from prefab_ui.app import PrefabApp, Theme
from prefab_ui.components import (
    H2,
    H3,
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Div,
    Link,
    Muted,
    Progress,
    Row,
    Separator,
    Span,
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

MODE = "dark"  # MySpace is a dark theme -> dark palette variants


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
    "is_customer_reported": "Customer?", "areas": "Areas", "triage_status": "Triage",
    "child_closed": "Closed", "child_total": "Sub-issues", "pct_complete": "% done",
    "milestone_title": "Milestone",
}


def cell(key: str, value) -> str:
    if value is None or value == "":
        return "—"
    if isinstance(value, bool):
        return "yes!!" if value else "no"
    if key == "issue_category":
        return tiles.label("issue_category", value)
    if key == "triage_status":
        return str(value).replace("_", " ")
    if key == "title":
        return value[:70] + ("..." if len(value) > 70 else "")
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


GUESTBOOK = [
    ("xX_d4ta_qu33n_Xx", "2003-07-14", "omg ur dashboard is SO cool!! add me 2 ur top 8 plzzz"),
    ("~*SQLboy2002*~", "2003-08-02", "nice analytics bro. check out MY dashboard at geocities.com/sqlboy2002"),
    ("dbt_angel_kissez", "2003-09-11", "luv the charts!! ur issue metrics r off da chain xD"),
    ("warehouse_gangsta", "2003-10-05", "yo this backlog chart is FIRE. a/s/l??"),
    ("PiPeLiNe_PrInCeSs", "2003-11-22", "OMG the triage queue made me cry lol. *~hugz~*"),
]


# ══════════════════════════════════════════════════════════════════
#  MYSPACE CSS THEME
# ══════════════════════════════════════════════════════════════════

MYSPACE_CSS = """
@keyframes blink { 0%,49%{opacity:1} 50%,100%{opacity:0} }
@keyframes rainbow { 0%{color:#f00} 16%{color:#f80} 33%{color:#ff0} 50%{color:#39ff14} 66%{color:#0ff} 83%{color:#ff69b4} 100%{color:#f00} }
@keyframes marquee { 0%{transform:translateX(100%)} 100%{transform:translateX(-100%)} }
@keyframes sparkle { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.5;transform:scale(1.3)} }

body {
    background-color: #0a0a0a !important;
    background-image: url("data:image/svg+xml,%3Csvg width='60' height='60' xmlns='http://www.w3.org/2000/svg'%3E%3Ctext x='10' y='40' font-size='30' opacity='0.07'%3E%E2%AD%90%3C/text%3E%3C/svg%3E");
    cursor: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16'%3E%3Ctext y='14' font-size='14'%3E%E2%9C%A8%3C/text%3E%3C/svg%3E"), auto;
}
#root { color: #39ff14 !important; }
h1,h2,h3,h4 { color: #ff69b4 !important; text-shadow: 0 0 10px #ff69b4, 0 0 20px #ff1493; }
p,span,td,th,label { color: #39ff14 !important; }
.neon-card { border: 2px solid #0ff !important; box-shadow: 0 0 10px #0ff !important; background: rgba(10,10,10,.9) !important; }
.neon-pink { border: 2px solid #ff69b4 !important; box-shadow: 0 0 10px #ff69b4 !important; background: rgba(10,10,10,.9) !important; }
.neon-green { border: 2px solid #39ff14 !important; box-shadow: 0 0 10px #39ff14 !important; background: rgba(10,10,10,.9) !important; }
.neon-yellow { border: 2px solid #ff0 !important; box-shadow: 0 0 10px #ff0 !important; background: rgba(10,10,10,.9) !important; }
.blink { animation: blink 1s step-end infinite; }
.rainbow { animation: rainbow 3s linear infinite; font-weight: bold; }
.marquee-wrap { overflow: hidden; }
.marquee { display:inline-block; animation: marquee 12s linear infinite; white-space:nowrap; }
.sparkle { animation: sparkle 2s ease-in-out infinite; display:inline-block; }
.visitor-ctr { background:#000 !important; border:2px inset #808080 !important; color:#39ff14 !important; font-family:'Courier New',monospace !important; padding:4px 12px; display:inline-block; }
.construction { border:3px dashed #ff0 !important; background:repeating-linear-gradient(45deg,rgba(255,255,0,.05),rgba(255,255,0,.05) 10px,rgba(0,0,0,.1) 10px,rgba(0,0,0,.1) 20px) !important; }
.pf-card-title { color: #ff69b4 !important; font-weight: bold; }
.recharts-legend-wrapper div { color: #39ff14 !important; }
.stale-warning { border:3px dashed #f00 !important; background: rgba(255,0,0,.12) !important; }
.stale-warning span { color: #ff0 !important; }
"""

MYSPACE_THEME = Theme(
    mode="dark",
    font="Comic Neue",
    css=MYSPACE_CSS,
    accent="#ff69b4",
)

NEON = ["neon-card", "neon-pink", "neon-green", "neon-yellow"]


# ══════════════════════════════════════════════════════════════════
#  TILE RENDERERS (keyed by tile id in tiles.yml)
# ══════════════════════════════════════════════════════════════════

def bar_height(data: list[dict]) -> int:
    return max(220, 34 * len(data) + 60)


def neon_table(tile: dict, data: list[dict], bar_key: str | None = None) -> None:
    columns = tile["columns"]
    with Table():
        with TableHeader():
            with TableRow():
                for col in columns:
                    TableHead(HEADERS.get(col, col), style={"color": "#ff69b4"})
                if bar_key:
                    TableHead("", style={"color": "#ff69b4"})
        with TableBody():
            for r in data:
                with TableRow():
                    for col in columns:
                        if col in ("issue_number", "epic_number"):
                            with TableCell():
                                Link(f"#{r[col]}", href=r["issue_url"], target="_blank", style={"color": "#0ff"})
                        else:
                            TableCell(cell(col, r[col]), style={"color": "#39ff14", "font-size": "0.85rem"})
                    if bar_key:
                        with TableCell(style={"min-width": "120px"}):
                            Progress(value=r[bar_key] or 0, indicator_class="bg-pink-500")


def render_backlog_weekly(tile: dict) -> None:
    data = DATA["backlog_weekly"]
    AreaChart(data=data, series=series("issue_category", data), x_axis="week",
              stacked=True, show_legend=True, height=300)


def render_weekly_flow(tile: dict) -> None:
    data = DATA["weekly_flow"]
    BarChart(data=data, series=series("flow", data), x_axis="week", show_legend=True, height=280)


def render_triage_pipeline(tile: dict) -> None:
    data = DATA["triage_pipeline"]
    BarChart(data=data, series=series("age_bucket", data), x_axis="status_label",
             stacked=True, horizontal=True, show_legend=True, height=bar_height(data))


def render_response_weekly(tile: dict) -> None:
    LineChart(
        data=DATA["response_weekly"],
        series=[ChartSeries(data_key="pct_responded_48h", label="% answered within 48h",
                            color=tiles.MANIFEST["palette"]["single_series"])],
        x_axis="week", show_legend=False, curve="smooth", height=260,
    )


def render_triage_queue(tile: dict) -> None:
    neon_table(tile, DATA["triage_queue"])


def render_stacked_category_bar(key: str, y: str):
    def render(tile: dict) -> None:
        data = DATA[key]
        BarChart(data=data, series=series("issue_category", data), x_axis=y,
                 stacked=True, horizontal=True, show_legend=True, height=bar_height(data))
    return render


def render_epic_progress(tile: dict) -> None:
    neon_table(tile, DATA["epic_progress"], bar_key="pct_complete")


def render_top_requested(tile: dict) -> None:
    neon_table(tile, DATA["top_requested"])


RENDER = {
    "backlog_weekly": render_backlog_weekly,
    "weekly_flow": render_weekly_flow,
    "triage_pipeline": render_triage_pipeline,
    "response_weekly": render_response_weekly,
    "triage_queue": render_triage_queue,
    "open_by_area": render_stacked_category_bar("open_by_area", "area"),
    "open_by_adapter": render_stacked_category_bar("open_by_adapter", "adapter"),
    "epic_progress": render_epic_progress,
    "top_requested": render_top_requested,
    "assignee_workload": render_stacked_category_bar("assignee_workload", "assignee_login"),
}

SECTION_EMOJI = {"status": "⭐", "backlog": "📉", "triage": "🚨", "where": "🗺️", "epics": "🏆", "next": "💖"}


def render_kpis() -> None:
    """headline_kpis tile: 'Da Stats' neon cards."""
    with Row(gap=3, css_class="mt-4 flex-wrap"):
        for i, k in enumerate(KPIS):
            with Card(css_class=f"flex-1 {NEON[i % len(NEON)]}", style={"min-width": "150px"}):
                with CardHeader():
                    CardTitle(k["label"])
                with CardContent():
                    H3(k["value"], css_class="rainbow" if i == 0 else None, style={"font-size": "2rem"})
                    if k["context"]:
                        Muted(k["context"])


# ══════════════════════════════════════════════════════════════════
#  BUILD DASHBOARD
# ══════════════════════════════════════════════════════════════════

with PrefabApp(
    title=f"{tiles.MANIFEST['title']} (MySpace)",
    css_class="max-w-5xl mx-auto p-6",
    theme=MYSPACE_THEME,
    stylesheets=["https://fonts.googleapis.com/css2?family=Comic+Neue:wght@400;700&display=swap"],
) as app:

    # ── Marquee banner ─────────────────────────────────────────────
    with Div(css_class="marquee-wrap", style={"border-top": "2px solid #0ff", "border-bottom": "2px solid #0ff", "padding": "8px 0"}):
        Span(f"~*~Welcome 2 my dashboard~*~ ---- {meta['source_repo']} {meta['source_label']} issues ---- best viewed in IE6 @ 800x600 ---- dont steal my HTML!! ----",
             css_class="marquee", style={"color": "#0ff", "font-size": "1.5rem", "font-weight": "bold", "text-shadow": "0 0 10px #0ff"})

    # ── Title + freshness ──────────────────────────────────────────
    H2(f"~*~ {tiles.MANIFEST['title']} ~*~", css_class="text-center mt-4", style={"font-size": "2.5rem"})
    Text(tiles.MANIFEST["subtitle"], css_class="text-center block", style={"color": "#0ff"})
    Text(FRESHNESS, css_class="text-center block", style={"color": "#ff0", "font-size": "0.85rem"})

    if IS_STALE:
        with Div(css_class="text-center stale-warning p-3 my-4"):
            Span("⚠ !! DATA IS STALE !! ⚠ ", css_class="blink", style={"font-weight": "bold", "font-size": "1.1rem"})
            Span(f"last update {meta['days_stale']} days ago — the extract may have stopped :(")

    # ── Visitor counter + under construction ───────────────────────
    with Div(css_class="text-center my-4"):
        Span("✨", css_class="sparkle", style={"font-size": "1.5rem"})
        Span(" ", style={"color": "transparent"})
        Span(f"You are visitor #{meta['issue_count']:,}", css_class="visitor-ctr")
        Span(" ", style={"color": "transparent"})
        Span("✨", css_class="sparkle", style={"font-size": "1.5rem"})

    with Div(css_class="text-center construction p-3 my-4"):
        Span("🚧 ", style={"font-size": "1.3rem"})
        Span("!! UNDER CONSTRUCTION !!", css_class="blink", style={"color": "#ff0", "font-weight": "bold", "font-size": "1.1rem"})
        Span(" 🚧", style={"font-size": "1.3rem"})

    # ── Sections, in tiles.yml order ───────────────────────────────
    n = 0
    for section in tiles.sections():
        emoji = SECTION_EMOJI.get(section["id"], "✨")
        H3(f"{emoji} ~*~ {section['question']} ~*~ {emoji}", css_class="mt-8")
        for tile in section["tiles"]:
            if tile["id"] == "headline_kpis":
                render_kpis()
                continue
            with Card(css_class=f"mt-4 {NEON[n % len(NEON)]}"):
                with CardHeader():
                    CardTitle(f"~*~ {tile['title']} ~*~")
                    Muted(tile["subtitle"])
                with CardContent():
                    RENDER[tile["id"]](tile)
            n += 1

    # ── Guestbook ──────────────────────────────────────────────────
    H3("📝 ~*~ Guestbook ~*~ 📝", css_class="mt-8")
    Muted("sign my guestbook plzz!! (jk its read-only lol)")

    with Card(css_class="mt-3 neon-card"):
        with CardContent():
            for name, date, msg in GUESTBOOK:
                with Div(style={"border-bottom": "1px dashed #0ff", "padding": "8px 0"}):
                    with Row(gap=2):
                        Text(name, style={"color": "#ff69b4", "font-weight": "bold"})
                        Text(date, style={"color": "#666", "font-size": "0.8rem"})
                    Text(msg, style={"color": "#39ff14", "font-style": "italic"})

    # ── Footer ─────────────────────────────────────────────────────
    Separator(css_class="my-6")
    with Div(css_class="text-center py-4"):
        Text("Thanks 4 visiting my dashboard!! xD", style={"color": "#ff69b4", "font-size": "1.2rem", "font-weight": "bold"})
        Text("~*~*~ made with luv and dbt v2 ~*~*~", style={"color": "#0ff", "font-size": "0.9rem"})
        Span("✨", css_class="sparkle", style={"font-size": "2rem"})
        Span("⭐", css_class="sparkle", style={"font-size": "2rem", "animation-delay": "0.5s"})
        Span("💖", css_class="sparkle", style={"font-size": "2rem", "animation-delay": "1s"})
        Span("🌟", css_class="sparkle", style={"font-size": "2rem", "animation-delay": "1.5s"})
        Span("✨", css_class="sparkle", style={"font-size": "2rem", "animation-delay": "2s"})
