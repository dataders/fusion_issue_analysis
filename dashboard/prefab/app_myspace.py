"""
~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~
    dbt-fusion Issue Analytics Dashboard
    -=- MySpace Edition -=-
    Best viewed in Internet Explorer 6.0 at 800x600
~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~
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
    Div,
    H2,
    H3,
    Muted,
    Row,
    Separator,
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


# ── Data queries (same as main dashboard) ──────────────────────────

summary_cards = query("SELECT * FROM summary_kpis")[0]

net_flow = summary_cards["closed_4w"] - summary_cards["opened_4w"]
net_flow_sign = "+" if net_flow > 0 else ""

cumulative_flow = query("SELECT * FROM cumulative_flow")

response_pctiles = query("SELECT * FROM response_pctiles")

community_priorities = query("SELECT * FROM community_priorities")

assignee_workload = query("SELECT * FROM assignee_workload")

GUESTBOOK = [
    ("xX_d4ta_qu33n_Xx", "2003-07-14", "omg ur dashboard is SO cool!! add me 2 ur top 8 plzzz"),
    ("~*SQLboy2002*~", "2003-08-02", "nice analytics bro. check out MY dashboard at geocities.com/sqlboy2002"),
    ("dbt_angel_kissez", "2003-09-11", "luv the charts!! ur issue metrics r off da chain xD"),
    ("warehouse_gangsta", "2003-10-05", "yo this cumulative flow chart is FIRE. a/s/l??"),
    ("PiPeLiNe_PrInCeSs", "2003-11-22", "OMG the stale issues counter made me cry lol. *~hugz~*"),
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
.blink { animation: blink 1s step-end infinite; }
.rainbow { animation: rainbow 3s linear infinite; font-weight: bold; }
.marquee-wrap { overflow: hidden; }
.marquee { display:inline-block; animation: marquee 12s linear infinite; white-space:nowrap; }
.sparkle { animation: sparkle 2s ease-in-out infinite; display:inline-block; }
.top8 { border: 3px dashed #ff69b4 !important; background: linear-gradient(135deg, rgba(255,20,147,.1), rgba(0,255,255,.1)) !important; }
.visitor-ctr { background:#000 !important; border:2px inset #808080 !important; color:#39ff14 !important; font-family:'Courier New',monospace !important; padding:4px 12px; display:inline-block; }
.construction { border:3px dashed #ff0 !important; background:repeating-linear-gradient(45deg,rgba(255,255,0,.05),rgba(255,255,0,.05) 10px,rgba(0,0,0,.1) 10px,rgba(0,0,0,.1) 20px) !important; }
"""

MYSPACE_THEME = Theme(
    mode="dark",
    font="Comic Neue",
    css=MYSPACE_CSS,
    accent="#ff69b4",
)

# ══════════════════════════════════════════════════════════════════
#  BUILD DASHBOARD
# ══════════════════════════════════════════════════════════════════

with PrefabApp(
    css_class="max-w-5xl mx-auto p-6",
    theme=MYSPACE_THEME,
    stylesheets=["https://fonts.googleapis.com/css2?family=Comic+Neue:wght@400;700&display=swap"],
) as app:

    # ── Marquee banner ─────────────────────────────────────────────
    Div(css_class="marquee-wrap", style={"border-top": "2px solid #0ff", "border-bottom": "2px solid #0ff", "padding": "8px 0"})
    with Div(css_class="marquee-wrap", style={"border-top": "2px solid #0ff", "border-bottom": "2px solid #0ff", "padding": "8px 0"}):
        Span("~*~Welcome 2 my dashboard~*~ ---- dbt-fusion issue analytics ---- best viewed in IE6 @ 800x600 ---- dont steal my HTML!! ----",
             css_class="marquee", style={"color": "#0ff", "font-size": "1.5rem", "font-weight": "bold", "text-shadow": "0 0 10px #0ff"})

    # ── Title ──────────────────────────────────────────────────────
    H2("dbt-fusion Issue Health", css_class="text-center mt-4", style={"font-size": "2.5rem"})
    Text("Actionable metrics 4 dbt-labs/dbt-fusion -- updated on deploy lol", css_class="text-center", style={"color": "#0ff"})

    # ── Visitor counter + under construction ───────────────────────
    with Div(css_class="text-center my-4"):
        Span("✨", css_class="sparkle", style={"font-size": "1.5rem"})
        Span(" ", style={"color": "transparent"})
        Span("You are visitor #13,337", css_class="visitor-ctr")
        Span(" ", style={"color": "transparent"})
        Span("✨", css_class="sparkle", style={"font-size": "1.5rem"})

    with Div(css_class="text-center construction p-3 my-4"):
        Span("🚧 ", style={"font-size": "1.3rem"})
        Span("!! UNDER CONSTRUCTION !!", css_class="blink", style={"color": "#ff0", "font-weight": "bold", "font-size": "1.1rem"})
        Span(" 🚧", style={"font-size": "1.3rem"})

    # ── Da Stats ───────────────────────────────────────────────────
    H3("⭐ ~*~ Da Stats ~*~ ⭐")

    with Row(gap=3, css_class="mt-4"):
        with Card(css_class="flex-1 neon-card"):
            with CardHeader():
                CardTitle("Net Flow (4 wk)")
            with CardContent():
                H3(f"{net_flow_sign}{net_flow}", css_class="rainbow", style={"font-size": "2rem"})
                Muted(f"{summary_cards['opened_4w']} opened / {summary_cards['closed_4w']} closed")

        with Card(css_class="flex-1 neon-pink"):
            with CardHeader():
                CardTitle("Open Issues")
            with CardContent():
                H3(str(summary_cards["open_issues"]), css_class="blink", style={"font-size": "2rem"})

        with Card(css_class="flex-1 neon-green"):
            with CardHeader():
                CardTitle("Median Close (4 wk)")
            with CardContent():
                val = summary_cards["rolling_median_close_days"]
                H3(f"{val} days" if val else "N/A", style={"font-size": "2rem"})

        with Card(css_class="flex-1 neon-card"):
            with CardHeader():
                CardTitle("48h Response SLA")
            with CardContent():
                pct = summary_cards["pct_responded_48h"]
                H3(f"{int(pct)}%" if pct else "N/A", style={"font-size": "2rem", "color": "#0ff"})

        with Card(css_class="flex-1 neon-pink"):
            with CardHeader():
                CardTitle("Stale Issues")
            with CardContent():
                H3(str(summary_cards["stale_count"]), css_class="blink", style={"font-size": "2rem", "color": "#f00"})
                Muted("no activity 30+ days :(")

    # ── Cumulative Flow ────────────────────────────────────────────
    with Card(css_class="mt-6 neon-card"):
        with CardHeader():
            CardTitle("~*~ Cumulative Issue Flow ~*~")
            Muted("gap = issue debt omg")
        with CardContent():
            AreaChart(
                data=cumulative_flow,
                series=[
                    ChartSeries(data_key="cumulative_opened", label="Opened", color="#ff1493"),
                    ChartSeries(data_key="cumulative_closed", label="Closed", color="#39ff14"),
                ],
                x_axis="week", show_legend=True, height=300,
            )

    # ── Response Time ──────────────────────────────────────────────
    with Card(css_class="mt-6 neon-green"):
        with CardHeader():
            CardTitle("Time 2 First Response (hours)")
            Muted("r we getting faster?? lol")
        with CardContent():
            LineChart(
                data=response_pctiles,
                series=[ChartSeries(data_key="p50", label="Median", color="#0ff")],
                x_axis="week", show_legend=True, curve="smooth", height=250,
            )

    # ── Top 8 Issues (MySpace Top 8 style!!) ──────────────────────
    H3("💖 ~*~ My Top 8 Issues ~*~ 💖", css_class="mt-6")
    Muted("these r my BEST issues. dont be jealous!!")

    with Row(gap=3, css_class="mt-3 flex-wrap"):
        for issue in community_priorities[:8]:
            with Card(css_class="top8", style={"width": "calc(25% - 12px)", "min-width": "200px"}):
                with CardContent():
                    Text(f"#{issue['issue_number']}", style={"color": "#ff69b4", "font-weight": "bold", "font-size": "1.2rem"})
                    Text(
                        issue["title"][:50] + ("..." if len(issue["title"]) > 50 else ""),
                        style={"color": "#0ff", "font-size": "0.85rem"},
                    )
                    with Row(gap=1, css_class="mt-2"):
                        Badge(f"{issue['reactions_total_count']} reactions", variant="outline")
                        Badge(f"{issue['age_days']}d old", variant="outline")

    # ── Assignee workload ──────────────────────────────────────────
    with Card(css_class="mt-6 neon-pink"):
        with CardHeader():
            CardTitle("~*~ Who's Doing All Da Work ~*~")
        with CardContent():
            BarChart(
                data=assignee_workload,
                series=[ChartSeries(data_key="open_issues", label="Open Issues", color="#ff69b4")],
                x_axis="assignee_login", horizontal=True, show_legend=False, height=300,
            )

    # ── Guestbook ──────────────────────────────────────────────────
    H3("📝 ~*~ Guestbook ~*~ 📝", css_class="mt-6")
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
        Text("~*~*~ made with luv and dbt-fusion ~*~*~", style={"color": "#0ff", "font-size": "0.9rem"})
        Span("✨", css_class="sparkle", style={"font-size": "2rem"})
        Span("⭐", css_class="sparkle", style={"font-size": "2rem", "animation-delay": "0.5s"})
        Span("💖", css_class="sparkle", style={"font-size": "2rem", "animation-delay": "1s"})
        Span("🌟", css_class="sparkle", style={"font-size": "2rem", "animation-delay": "1.5s"})
        Span("✨", css_class="sparkle", style={"font-size": "2rem", "animation-delay": "2s"})
