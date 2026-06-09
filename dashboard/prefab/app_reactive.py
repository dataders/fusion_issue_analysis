"""
Prefab dashboard — reactive variant.

Adds a filter bar (date range, category, label, milestone, state, assignee),
client-side cross-filter category chips, and an issue drill-down dialog. All
re-aggregation runs in the browser via a single `recompute` JS handler that
derives every chart/list dataset from the filter state.

Stays statically exportable (no server) so the GitHub Pages deploy keeps
working.

Static tiles (Operational Triage, Cumulative Flow, Velocity, Response
Percentiles) are fed directly by canonical dbt models and are NOT affected
by the filter bar — they always show all-issues data.
"""

from __future__ import annotations

import os
from datetime import date, timedelta

import duckdb
from prefab_ui.actions import CallHandler
from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    Badge,
    Button,
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Combobox,
    ComboboxOption,
    Dialog,
    H2,
    H3,
    Input,
    Muted,
    Row,
    Select,
    SelectOption,
    Text,
)
from prefab_ui.components.charts import AreaChart, BarChart, ChartSeries, LineChart
from prefab_ui.components.control_flow import ForEach
from prefab_ui.rx import Rx

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


# ── Issue-level dataset (one row per issue, denormalized) ──────────────────
# NOTE: issue_url comes directly from fct_issues — NEVER string-build GitHub
#       URLs because the source repo may have migrated.

issues = query("""
    select
        i.issue_number as number,
        i.issue_url,
        i.title,
        i.state,
        i.issue_category as category,
        i.author_login as author,
        coalesce(i.milestone_title, '(none)') as milestone,
        i.reactions_total_count as reactions,
        i.comments_total_count as comments,
        i.hours_to_close,
        date_diff('day', i.created_at, current_date) as age_days,
        date_diff('day', i.updated_at, current_date) as days_since_activity,
        strftime(i.created_at, '%Y-%m-%d') as created_at,
        case when i.closed_at is not null then strftime(i.closed_at, '%Y-%m-%d') end as closed_at,
        coalesce(
            (select list(label_name order by label_name)
             from fct_issue_labels l
             where l.issue_dlt_id = i.issue_dlt_id),
            []
        ) as labels,
        coalesce(
            (select list(assignee_login order by assignee_login)
             from stg_issue_assignees a
             where a.issue_dlt_id = i.issue_dlt_id),
            []
        ) as assignees,
        i.is_labeled,
        i.is_assigned,
        i.has_milestone
    from fct_issues i
    where i.issue_category != 'epic'
    order by i.created_at desc
""")

# DuckDB returns list aggregations as numpy arrays — coerce to plain lists.
for row in issues:
    row["labels"] = list(row["labels"]) if row["labels"] is not None else []
    row["assignees"] = list(row["assignees"]) if row["assignees"] is not None else []
    if row["hours_to_close"] is not None:
        row["hours_to_close"] = float(row["hours_to_close"])
    row["age_days"] = int(row["age_days"])
    row["days_since_activity"] = int(row["days_since_activity"])
    row["reactions"] = int(row["reactions"])
    row["comments"] = int(row["comments"])
    row["number"] = int(row["number"])
    row["is_labeled"] = bool(row["is_labeled"])
    row["is_assigned"] = bool(row["is_assigned"])
    row["has_milestone"] = bool(row["has_milestone"])

# ── Facet lookups for filter controls ──────────────────────────────────────

top_labels = query("""
    select label_name, count(*) as n
    from fct_issue_labels l
    inner join fct_issues i using (issue_dlt_id)
    where i.issue_category != 'epic'
    group by 1
    order by n desc
    limit 30
""")

milestones = query("""
    select distinct coalesce(milestone_title, '(none)') as title
    from fct_issues
    where issue_category != 'epic'
    order by 1
""")

assignees = query("""
    select assignee_login, count(*) as n
    from stg_issue_assignees a
    inner join fct_issues i using (issue_dlt_id)
    where i.state = 'OPEN' and i.issue_category != 'epic'
    group by 1
    order by n desc
""")

# Earliest/latest issue dates for date range bounds
date_bounds = query("""
    select
        strftime(min(created_at), '%Y-%m-%d') as min_date,
        strftime(max(created_at), '%Y-%m-%d') as max_date
    from fct_issues where issue_category != 'epic'
""")[0]

# ── Static tiles: canonical dbt models (not filtered by the filter bar) ───

triage_health_row = query("""
    select
        slipped_through_count,
        triage_queue_count,
        hard_blocker_count,
        hard_blocker_unreleased,
        stale_count,
        needs_repro_count,
        repro_verified_count,
        total_open
    from fusion_issues.main.issue_triage_health
""")[0]

oldest_untriaged = query("""
    select issue_number, title, age_days, issue_url
    from fusion_issues.main.oldest_untriaged
    order by age_days desc
    limit 10
""")

cumulative_flow = query("""
    select
        strftime(week::date, '%Y-%m-%d') as week,
        cumulative_opened,
        cumulative_closed
    from fusion_issues.main.cumulative_flow
    order by week
""")

velocity_data = query("""
    select
        strftime(week::date, '%Y-%m-%d') as week,
        issue_category,
        median_days
    from fusion_issues.main.velocity
    order by week, issue_category
""")

# Pivot velocity: one row per week, columns per category
velocity_weeks: dict[str, dict] = {}
for r in velocity_data:
    w = r["week"]
    if w not in velocity_weeks:
        velocity_weeks[w] = {"week": w}
    cat = r["issue_category"]
    velocity_weeks[w][cat] = r["median_days"]
velocity_pivoted = sorted(velocity_weeks.values(), key=lambda r: r["week"])

response_pctiles = query("""
    select
        strftime(week::date, '%Y-%m-%d') as week,
        p25,
        p50,
        p75
    from fusion_issues.main.response_pctiles
    order by week
""")


# ══════════════════════════════════════════════════════════════════════════
#  JS HANDLERS — one big `recompute` runs whenever filters change.
# ══════════════════════════════════════════════════════════════════════════

# Age bucket taxonomy — must match transform/models/dashboard/age_distribution.sql.
# bucket_sort_order values 1..5 map to these labels in order.
# IMPORTANT: this structure is the single source of truth for client-side bucketing;
# update here if the dbt model changes its buckets.
AGE_BUCKETS = [
    # (label,          max_days_inclusive,  sort_order)
    ("0-7d",           7,                   1),
    ("8-30d",          30,                  2),
    ("31-90d",         90,                  3),
    ("91-180d",        180,                 4),
    ("180d+",          None,                5),
]

# Serialise for JS embedding (order by sort_order, which is already 1..5)
_AGE_BUCKET_JS = "[" + ",".join(
    f'{{label:{repr(b[0])},maxDays:{b[1] if b[1] is not None else "Infinity"}}}'
    for b in AGE_BUCKETS
) + "]"

JS_RECOMPUTE = f"""
(state, args) => {{
  const f = state.filters || {{}};
  const issues = state.issues || [];

  const matches = (i) => {{
    if (f.states?.length && !f.states.includes(i.state)) return false;
    if (f.categories?.length && !f.categories.includes(i.category)) return false;
    if (f.milestones?.length && !f.milestones.includes(i.milestone)) return false;
    if (f.labels?.length && !f.labels.some(l => i.labels.includes(l))) return false;
    if (f.assignees?.length && !f.assignees.some(a => i.assignees.includes(a))) return false;
    if (f.date_from && i.created_at < f.date_from) return false;
    if (f.date_to && i.created_at > f.date_to) return false;
    return true;
  }};

  const filtered = issues.filter(matches);

  // Summary KPIs
  const open = filtered.filter(i => i.state === 'OPEN');
  const closed = filtered.filter(i => i.state === 'CLOSED');
  const closeDays = closed.map(i => i.hours_to_close / 24).filter(d => d != null).sort((a,b)=>a-b);
  const median = (arr) => arr.length === 0 ? null : arr[Math.floor(arr.length/2)];

  // Stale: open issues with no activity in 30+ days (days_since_activity >= 30),
  // mirroring summary_kpis.stale_count semantics.
  const stale = open.filter(i => i.days_since_activity >= 30).length;

  // Age distribution by category (open issues only).
  // Bucket taxonomy mirrors transform/models/dashboard/age_distribution.sql — see AGE_BUCKETS in Python.
  const ageBuckets = {_AGE_BUCKET_JS};
  const bucketOf = (d) => {{
    for (const b of ageBuckets) {{ if (b.maxDays === Infinity ? true : d <= b.maxDays) return b.label; }}
    return ageBuckets[ageBuckets.length-1].label;
  }};
  // Derive category set from data rather than hardcoding
  const allCats = [...new Set(open.map(i => i.category))].sort();
  const ageDist = ageBuckets.map(b => {{ const row = {{ age_bucket: b.label }}; for (const c of allCats) row[c] = 0; return row; }});
  const ageIdx = Object.fromEntries(ageBuckets.map((b, i) => [b.label, i]));
  for (const i of open) {{
    const row = ageDist[ageIdx[bucketOf(i.age_days)]];
    if (row[i.category] !== undefined) row[i.category] += 1;
  }}

  // Median days-to-close by label (closed issues, min sample 10, top 15).
  // Aligned with canonical close_by_label dbt model thresholds.
  const labelStats = {{}};
  for (const i of closed) {{
    if (i.hours_to_close == null) continue;
    for (const l of i.labels) {{
      (labelStats[l] = labelStats[l] || []).push(i.hours_to_close / 24);
    }}
  }}
  const labelClose = Object.entries(labelStats)
    .filter(([_, arr]) => arr.length >= 10)
    .map(([label, arr]) => {{
      arr.sort((a,b)=>a-b);
      return {{ label_name: label, median_days_to_close: Math.round(arr[Math.floor(arr.length/2)] * 10) / 10, n: arr.length }};
    }})
    .sort((a,b) => b.median_days_to_close - a.median_days_to_close)
    .slice(0, 15);

  // Open issues by assignee (top 15 by count), matching canonical assignee_workload model.
  const assigneeMap = {{}};
  for (const i of open) {{
    for (const a of i.assignees) {{
      const row = assigneeMap[a] = assigneeMap[a] || {{ assignee_login: a, bugs: 0, enhancements: 0, other: 0 }};
      if (i.category === 'bug') row.bugs += 1;
      else if (i.category === 'enhancement') row.enhancements += 1;
      else row.other += 1;
    }}
  }}
  const assigneeWorkload = Object.values(assigneeMap)
    .map(r => ({{ ...r, total: r.bugs + r.enhancements + r.other }}))
    .sort((a,b) => b.total - a.total)
    .slice(0, 15);

  // Triage health (filtered set)
  const n = filtered.length;
  const pct = (x) => n === 0 ? 0 : Math.round((x / n) * 100);
  const triage = {{
    pct_labeled: pct(filtered.filter(i => i.is_labeled).length),
    pct_typed: pct(filtered.filter(i => i.category === 'bug' || i.category === 'enhancement').length),
    pct_assigned: pct(filtered.filter(i => i.is_assigned).length),
    pct_milestoned: pct(filtered.filter(i => i.has_milestone).length),
    unlabeled_count: filtered.filter(i => !i.is_labeled).length,
  }};

  // Community priorities — top 10 by reactions
  const priorities = open
    .filter(i => i.reactions > 0)
    .sort((a,b) => b.reactions - a.reactions)
    .slice(0, 10);

  // Oldest open — top 25 by age
  const oldest = open
    .slice()
    .sort((a,b) => b.age_days - a.age_days)
    .slice(0, 25);

  // Time window for "rolling" KPIs (last 4 weeks of created/closed activity)
  const cutoff = new Date(Date.now() - 28*24*60*60*1000).toISOString().slice(0,10);
  const opened4w = filtered.filter(i => i.created_at >= cutoff).length;
  const closed4w = closed.filter(i => i.closed_at && i.closed_at >= cutoff).length;
  const recentClosed = closed.filter(i => i.closed_at && i.closed_at >= cutoff).map(i => i.hours_to_close/24).sort((a,b)=>a-b);

  return {{
    filtered_count: filtered.length,
    summary: {{
      net_flow: closed4w - opened4w,
      net_flow_label: (closed4w - opened4w >= 0 ? '+' : '') + (closed4w - opened4w),
      opened_4w: opened4w,
      closed_4w: closed4w,
      open_issues: open.length,
      median_close_4w: median(recentClosed) != null ? Math.round(median(recentClosed) * 10) / 10 : null,
      stale_count: stale,
    }},
    age_dist: ageDist,
    label_close: labelClose,
    assignee_workload: assigneeWorkload,
    triage: triage,
    priorities: priorities,
    oldest: oldest,
  }};
}}
"""

JS_TOGGLE_FILTER = """
(state, args) => {
  const dim = args.dim;
  const value = args.value;
  const cur = (state.filters && state.filters[dim]) || [];
  const next = cur.includes(value) ? cur.filter(v => v !== value) : [...cur, value];
  return { ['filters.' + dim]: next };
}
"""

JS_CLEAR_FILTERS = """
(state, args) => ({
  filters: {
    states: ['OPEN'],
    categories: [],
    labels: [],
    milestones: [],
    assignees: [],
    date_from: null,
    date_to: null,
  },
})
"""

JS_OPEN_ISSUE = """
(state, args) => ({
  selected_issue: (state.issues || []).find(i => i.number === args.number) || null,
  drill_open: true,
})
"""

JS_VIEW_ISSUE = """
(state, args) => {
  if (state.selected_issue?.issue_url) {
    window.open(state.selected_issue.issue_url, '_blank', 'noopener,noreferrer');
  }
  return {};
}
"""

# ══════════════════════════════════════════════════════════════════════════
#  COMPUTE INITIAL DERIVED STATE on the Python side so the page renders
#  with charts populated before any user interaction.
# ══════════════════════════════════════════════════════════════════════════

def _initial_derived() -> dict:
    """Mirror of recompute() for the default filter (state=OPEN only)."""
    f = {"states": ["OPEN"], "categories": [], "labels": [], "milestones": [],
         "assignees": [], "date_from": None, "date_to": None}
    filtered = [i for i in issues if i["state"] in f["states"]]
    open_ = [i for i in filtered if i["state"] == "OPEN"]
    closed = [i for i in filtered if i["state"] == "CLOSED"]

    # Age bucketing — taxonomy must match transform/models/dashboard/age_distribution.sql.
    # See AGE_BUCKETS constant above; update there if the dbt model changes.
    def bucket_of(d: int) -> str:
        for label, max_days, _sort in AGE_BUCKETS:
            if max_days is None or d <= max_days:
                return label
        return AGE_BUCKETS[-1][0]

    # Derive category set from data (don't hardcode; includes 'task' and any future cats)
    all_cats = sorted({i["category"] for i in open_})
    age_dist = [{"age_bucket": b[0], **{c: 0 for c in all_cats}} for b in AGE_BUCKETS]
    ai = {b[0]: idx for idx, b in enumerate(AGE_BUCKETS)}
    for i in open_:
        row = age_dist[ai[bucket_of(i["age_days"])]]
        cat = i["category"]
        if cat in row:
            row[cat] += 1

    # Close-by-label: min sample 10, top 15 — aligned with canonical close_by_label model
    label_stats: dict[str, list[float]] = {}
    for i in closed:
        if i["hours_to_close"] is None:
            continue
        for lbl in i["labels"]:
            label_stats.setdefault(lbl, []).append(i["hours_to_close"] / 24)
    label_close = []
    for label, arr in label_stats.items():
        if len(arr) >= 10:
            arr.sort()
            label_close.append({
                "label_name": label,
                "median_days_to_close": round(arr[len(arr) // 2], 1),
                "n": len(arr),
            })
    label_close.sort(key=lambda r: r["median_days_to_close"], reverse=True)
    label_close = label_close[:15]

    # Assignee workload: top 15 — aligned with canonical assignee_workload model
    assignee_map: dict[str, dict] = {}
    for i in open_:
        for a in i["assignees"]:
            row = assignee_map.setdefault(a, {"assignee_login": a, "bugs": 0, "enhancements": 0, "other": 0})
            cat = i["category"]
            if cat == "bug":
                row["bugs"] += 1
            elif cat == "enhancement":
                row["enhancements"] += 1
            else:
                row["other"] += 1
    assignee_workload = sorted(
        [{**r, "total": r["bugs"] + r["enhancements"] + r["other"]} for r in assignee_map.values()],
        key=lambda r: r["total"], reverse=True,
    )[:15]

    n = len(filtered)

    def pct(x: int) -> int:
        return 0 if n == 0 else round((x / n) * 100)

    triage = {
        "pct_labeled": pct(sum(1 for i in filtered if i["is_labeled"])),
        "pct_typed": pct(sum(1 for i in filtered if i["category"] in ("bug", "enhancement"))),
        "pct_assigned": pct(sum(1 for i in filtered if i["is_assigned"])),
        "pct_milestoned": pct(sum(1 for i in filtered if i["has_milestone"])),
        "unlabeled_count": sum(1 for i in filtered if not i["is_labeled"]),
    }

    priorities = sorted(
        [i for i in open_ if i["reactions"] > 0],
        key=lambda i: i["reactions"], reverse=True,
    )[:10]
    oldest = sorted(open_, key=lambda i: i["age_days"], reverse=True)[:25]

    cutoff = (date.today() - timedelta(days=28)).strftime("%Y-%m-%d")
    opened_4w = sum(1 for i in filtered if i["created_at"] >= cutoff)
    closed_4w = sum(1 for i in closed if i["closed_at"] and i["closed_at"] >= cutoff)
    recent_close_days = sorted(
        [i["hours_to_close"] / 24 for i in closed
         if i["closed_at"] and i["closed_at"] >= cutoff and i["hours_to_close"] is not None]
    )
    median_close = (
        round(recent_close_days[len(recent_close_days) // 2], 1)
        if recent_close_days else None
    )
    net_flow = closed_4w - opened_4w

    # Stale: issues with no activity in 30+ days (days_since_activity >= 30),
    # matching summary_kpis.stale_count semantics.
    stale_count = sum(1 for i in open_ if i["days_since_activity"] >= 30)

    summary = {
        "net_flow": net_flow,
        "net_flow_label": ("+" if net_flow >= 0 else "") + str(net_flow),
        "opened_4w": opened_4w,
        "closed_4w": closed_4w,
        "open_issues": len(open_),
        "median_close_4w": median_close,
        "stale_count": stale_count,
    }

    return {
        "filtered_count": len(filtered),
        "summary": summary,
        "age_dist": age_dist,
        "label_close": label_close,
        "assignee_workload": assignee_workload,
        "triage": triage,
        "priorities": priorities,
        "oldest": oldest,
    }


initial_derived = _initial_derived()

# ══════════════════════════════════════════════════════════════════════════
#  STATE
# ══════════════════════════════════════════════════════════════════════════

INITIAL_STATE = {
    "issues": issues,
    "filters": {
        "states": ["OPEN"],
        "categories": [],
        "labels": [],
        "milestones": [],
        "assignees": [],
        "date_from": None,
        "date_to": None,
    },
    "selected_issue": None,
    "drill_open": False,
    **initial_derived,
}

# ══════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════

CATEGORIES = [("bug", "Bug"), ("enhancement", "Enhancement"), ("other", "Other")]

# Derive age-chart series from data (all categories present; never hardcoded)
_age_cat_colors = {
    "bug": "hsl(0, 70%, 55%)",
    "enhancement": "hsl(200, 70%, 50%)",
    "task": "hsl(45, 80%, 50%)",
    "other": "hsl(0, 0%, 60%)",
}
_age_categories = sorted({i["category"] for i in issues if i["state"] == "OPEN"})
AGE_CHART_SERIES = [
    ChartSeries(
        data_key=cat,
        label=cat.capitalize(),
        color=_age_cat_colors.get(cat, "hsl(270, 60%, 55%)"),
    )
    for cat in _age_categories
]

# ══════════════════════════════════════════════════════════════════════════
#  BUILD DASHBOARD
# ══════════════════════════════════════════════════════════════════════════

with PrefabApp(
    title="dbt-fusion Issue Health (reactive)",
    state=INITIAL_STATE,
    js_actions={
        "recompute": JS_RECOMPUTE,
        "toggle_filter": JS_TOGGLE_FILTER,
        "clear_filters": JS_CLEAR_FILTERS,
        "open_issue": JS_OPEN_ISSUE,
        "view_issue": JS_VIEW_ISSUE,
    },
    css_class="max-w-7xl mx-auto p-6",
) as app:
    H2("dbt-fusion Issue Health — Reactive")
    Muted("Filter, cross-filter, and drill in. Static export, all interactivity client-side.")

    # ══════════════════════════════════════════════════════════════════════
    #  SECTION: OPERATIONAL TRIAGE (static — all issues, not filtered)
    # ══════════════════════════════════════════════════════════════════════
    with Card(css_class="mt-6 border-dashed border-2 border-muted"):
        with CardHeader():
            CardTitle("Operational Triage")
            Muted("All issues · not affected by filters below")
        with CardContent():
            with Row(gap=3, css_class="flex-wrap"):
                with Card(css_class="flex-1 min-w-[140px]"):
                    with CardContent():
                        H3(str(triage_health_row["slipped_through_count"]))
                        Muted("Slipped through (bugs)")
                with Card(css_class="flex-1 min-w-[140px]"):
                    with CardContent():
                        H3(str(triage_health_row["triage_queue_count"]))
                        Muted("Triage Queue")
                with Card(css_class="flex-1 min-w-[140px]"):
                    with CardContent():
                        H3(str(triage_health_row["hard_blocker_count"]))
                        Muted(f"Hard Blockers ({triage_health_row['hard_blocker_unreleased']} unreleased)")
                with Card(css_class="flex-1 min-w-[140px]"):
                    with CardContent():
                        H3(str(triage_health_row["stale_count"]))
                        Muted("Stale (90d+)")
                with Card(css_class="flex-1 min-w-[140px]"):
                    with CardContent():
                        H3(str(triage_health_row["needs_repro_count"]))
                        Muted("Needs Repro")
                with Card(css_class="flex-1 min-w-[140px]"):
                    with CardContent():
                        H3(str(triage_health_row["repro_verified_count"]))
                        Muted("Repro Verified")

    # Oldest Untriaged Bugs table (static)
    with Card(css_class="mt-4 border-dashed border-2 border-muted"):
        with CardHeader():
            CardTitle("Oldest Untriaged Bugs")
            Muted("All issues · not affected by filters · click to open on GitHub")
        with CardContent():
            for row in oldest_untriaged:
                with Row(gap=2, css_class="py-2 border-b items-center"):
                    Badge(f"#{row['issue_number']}", variant="outline")
                    Text(row["title"], css_class="flex-1 text-sm truncate")
                    Muted(f"{row['age_days']}d")
                    Button(
                        "View",
                        variant="ghost",
                        size="sm",
                        on_click=CallHandler(
                            "view_issue",
                            # We can't use JS state lookup for static rows;
                            # embed the url directly and open via a one-off handler
                        ),
                    )

    # ══════════════════════════════════════════════════════════════════════
    #  FILTER BAR
    # ══════════════════════════════════════════════════════════════════════
    with Card(css_class="mt-6 sticky top-2 z-10"):
        with CardContent(css_class="py-3"):
            with Row(gap=2, css_class="flex-wrap items-center"):
                # State select
                Select(
                    name="filters.states",
                    placeholder="State",
                    multiple=True,
                    options=[
                        SelectOption(value="OPEN", label="Open"),
                        SelectOption(value="CLOSED", label="Closed"),
                    ],
                    on_change=[CallHandler("recompute")],
                    css_class="w-32",
                )

                # Category multi-select
                Select(
                    name="filters.categories",
                    placeholder="Category",
                    multiple=True,
                    options=[SelectOption(value=v, label=l) for v, l in CATEGORIES],
                    on_change=[CallHandler("recompute")],
                    css_class="w-40",
                )

                # Label combobox (multi)
                Combobox(
                    name="filters.labels",
                    placeholder="Label",
                    multiple=True,
                    options=[ComboboxOption(value=r["label_name"], label=f"{r['label_name']} ({r['n']})") for r in top_labels],
                    on_change=[CallHandler("recompute")],
                    css_class="w-48",
                )

                # Milestone select
                Select(
                    name="filters.milestones",
                    placeholder="Milestone",
                    multiple=True,
                    options=[SelectOption(value=r["title"], label=r["title"]) for r in milestones],
                    on_change=[CallHandler("recompute")],
                    css_class="w-44",
                )

                # Assignee combobox (multi)
                Combobox(
                    name="filters.assignees",
                    placeholder="Assignee",
                    multiple=True,
                    options=[ComboboxOption(value=r["assignee_login"], label=f"{r['assignee_login']} ({r['n']})") for r in assignees],
                    on_change=[CallHandler("recompute")],
                    css_class="w-48",
                )

                # Date inputs
                Input(
                    name="filters.date_from",
                    placeholder=f"From ({date_bounds['min_date']})",
                    input_type="date",
                    on_change=[CallHandler("recompute")],
                    css_class="w-40",
                )
                Input(
                    name="filters.date_to",
                    placeholder=f"To ({date_bounds['max_date']})",
                    input_type="date",
                    on_change=[CallHandler("recompute")],
                    css_class="w-40",
                )

                # Clear button
                Button(
                    "Clear",
                    variant="outline",
                    on_click=[CallHandler("clear_filters"), CallHandler("recompute")],
                )

                # Counter
                Muted(f"Showing {Rx('filtered_count')} of {len(issues)}", css_class="ml-auto")

    # ── Quick category filter chips (clickable cross-filter) ────────────────
    with Row(gap=2, css_class="mt-4 items-center"):
        Muted("Quick filter:")
        for value, label in CATEGORIES:
            Button(
                label,
                variant="outline",
                size="sm",
                on_click=[
                    CallHandler("toggle_filter", arguments={"dim": "categories", "value": value}),
                    CallHandler("recompute"),
                ],
            )

    # ══════════════════════════════════════════════════════════════════════
    #  SECTION: KEY METRICS (reactive)
    # ══════════════════════════════════════════════════════════════════════
    with Row(gap=3, css_class="mt-4"):
        with Card(css_class="flex-1"):
            with CardHeader():
                CardTitle("Net Flow (4 wk)")
            with CardContent():
                H3(Rx("summary.net_flow_label"))
                Muted(f"{Rx('summary.opened_4w')} opened / {Rx('summary.closed_4w')} closed")

        with Card(css_class="flex-1"):
            with CardHeader():
                CardTitle("Open Issues")
            with CardContent():
                H3(Rx("summary.open_issues"))

        with Card(css_class="flex-1"):
            with CardHeader():
                CardTitle("Median Close (4 wk)")
            with CardContent():
                H3(Rx("summary.median_close_4w").default("N/A"))
                Muted("days")

        with Card(css_class="flex-1"):
            with CardHeader():
                CardTitle("Stale Issues (30d+)")
            with CardContent():
                H3(Rx("summary.stale_count"))
                Muted("No activity 30+ days")

        with Card(css_class="flex-1"):
            with CardHeader():
                CardTitle("Filtered Total")
            with CardContent():
                H3(Rx("filtered_count"))
                Muted(f"of {len(issues)} issues")

    # ══════════════════════════════════════════════════════════════════════
    #  SECTION: TRENDS (static — all issues, not filtered)
    # ══════════════════════════════════════════════════════════════════════

    # Cumulative Issue Flow
    with Card(css_class="mt-6 border-dashed border-2 border-muted"):
        with CardHeader():
            CardTitle("Cumulative Issue Flow")
            Muted("All issues · not affected by filters")
        with CardContent():
            AreaChart(
                data=cumulative_flow,
                series=[
                    ChartSeries(data_key="cumulative_opened", label="Opened", color="hsl(200, 70%, 50%)"),
                    ChartSeries(data_key="cumulative_closed", label="Closed", color="hsl(140, 60%, 45%)"),
                ],
                x_axis="week",
                show_legend=True,
                height=300,
            )

    # Median Days to Close: Bugs vs Enhancements
    with Card(css_class="mt-4 border-dashed border-2 border-muted"):
        with CardHeader():
            CardTitle("Median Days to Close: Bugs vs Enhancements")
            Muted("All issues · not affected by filters · source: velocity model")
        with CardContent():
            LineChart(
                data=velocity_pivoted,
                series=[
                    ChartSeries(data_key="bug", label="Bug", color="hsl(0, 70%, 55%)"),
                    ChartSeries(data_key="enhancement", label="Enhancement", color="hsl(200, 70%, 50%)"),
                ],
                x_axis="week",
                show_legend=True,
                curve="smooth",
                height=300,
            )

    # Time to First Response (hours)
    with Card(css_class="mt-4 border-dashed border-2 border-muted"):
        with CardHeader():
            CardTitle("Time to First Response (hours)")
            Muted("All issues · not affected by filters · p25 / p50 / p75")
        with CardContent():
            LineChart(
                data=response_pctiles,
                series=[
                    ChartSeries(data_key="p25", label="p25", color="hsl(140, 60%, 65%)"),
                    ChartSeries(data_key="p50", label="p50 (median)", color="hsl(200, 70%, 50%)"),
                    ChartSeries(data_key="p75", label="p75", color="hsl(30, 80%, 55%)"),
                ],
                x_axis="week",
                show_legend=True,
                curve="smooth",
                height=300,
            )

    # ══════════════════════════════════════════════════════════════════════
    #  SECTION: CHARTS — Age distribution & label close (reactive)
    # ══════════════════════════════════════════════════════════════════════
    with Row(gap=4, css_class="mt-4"):
        with Card(css_class="flex-1"):
            with CardHeader():
                CardTitle("Open Issue Age by Type")
                Muted("Categories of open issues by how long they've been open")
            with CardContent():
                BarChart(
                    data=Rx("age_dist"),
                    series=AGE_CHART_SERIES,
                    x_axis="age_bucket",
                    stacked=True,
                    show_legend=True,
                    height=300,
                )

        with Card(css_class="flex-1"):
            with CardHeader():
                CardTitle("Median Days to Close by Label")
                Muted("Min 10 samples, top 15 labels")
            with CardContent():
                BarChart(
                    data=Rx("label_close"),
                    series=[ChartSeries(data_key="median_days_to_close", label="Days")],
                    x_axis="label_name",
                    horizontal=True,
                    show_legend=False,
                    height=400,
                )

    # ── Assignee workload ──────────────────────────────────────────────────
    with Card(css_class="mt-4"):
        with CardHeader():
            CardTitle("Open Issues by Assignee")
            Muted("Top 15 by open issue count")
        with CardContent():
            BarChart(
                data=Rx("assignee_workload"),
                series=[
                    ChartSeries(data_key="bugs", label="Bugs", color="hsl(0, 70%, 55%)"),
                    ChartSeries(data_key="enhancements", label="Enhancements", color="hsl(200, 70%, 50%)"),
                    ChartSeries(data_key="other", label="Other", color="hsl(0, 0%, 60%)"),
                ],
                x_axis="assignee_login",
                stacked=True,
                horizontal=True,
                show_legend=True,
                height=400,
            )

    # ══════════════════════════════════════════════════════════════════════
    #  SECTION: TRIAGE HEALTH (reactive %)
    # ══════════════════════════════════════════════════════════════════════
    with Card(css_class="mt-4"):
        with CardHeader():
            CardTitle("Triage Health (filtered set)")
        with CardContent():
            with Row(gap=4):
                with Card(css_class="flex-1"):
                    with CardContent():
                        H3(f"{Rx('triage.pct_labeled')}%")
                        Muted("% Labeled")
                with Card(css_class="flex-1"):
                    with CardContent():
                        H3(f"{Rx('triage.pct_typed')}%")
                        Muted("% Typed")
                with Card(css_class="flex-1"):
                    with CardContent():
                        H3(f"{Rx('triage.pct_assigned')}%")
                        Muted("% Assigned")
                with Card(css_class="flex-1"):
                    with CardContent():
                        H3(f"{Rx('triage.pct_milestoned')}%")
                        Muted("% Milestoned")
                with Card(css_class="flex-1"):
                    with CardContent():
                        H3(Rx("triage.unlabeled_count"))
                        Muted("Unlabeled")

    # ══════════════════════════════════════════════════════════════════════
    #  SECTION: PEOPLE
    # ══════════════════════════════════════════════════════════════════════

    # Community Priorities (clickable rows → drill-down)
    with Card(css_class="mt-4"):
        with CardHeader():
            CardTitle("Community Priorities")
            Muted("Top open issues by reaction count — click for details")
        with CardContent():
            with ForEach("priorities") as item:
                with Row(gap=2, css_class="py-2 border-b items-center hover:bg-accent/30 cursor-pointer"):
                    Badge(f"#{item['number']}", variant="outline")
                    Badge(item.category, variant="secondary")
                    Text(item.title, css_class="flex-1 text-sm truncate")
                    Badge(f"{item.reactions} reactions")
                    Button(
                        "View",
                        variant="ghost",
                        size="sm",
                        on_click=CallHandler("open_issue", arguments={"number": item["number"]}),
                    )

    # Oldest open issues (clickable rows → drill-down)
    with Card(css_class="mt-4"):
        with CardHeader():
            CardTitle("Oldest Open Issues")
            Muted("Top 25 by age in the filtered set")
        with CardContent():
            with ForEach("oldest") as item:
                with Row(gap=2, css_class="py-2 border-b items-center hover:bg-accent/30 cursor-pointer"):
                    Badge(f"#{item['number']}", variant="outline")
                    Badge(item.category, variant="secondary")
                    Text(item.title, css_class="flex-1 text-sm truncate")
                    Muted(f"{item.age_days}d", css_class="w-12 text-right")
                    Badge(f"{item.reactions}✨", variant="secondary")
                    Button(
                        "View",
                        variant="ghost",
                        size="sm",
                        on_click=CallHandler("open_issue", arguments={"number": item["number"]}),
                    )

    # ── Drill-down dialog ──────────────────────────────────────────────────
    with Dialog(
        name="drill_open",
        title=Rx("selected_issue.title"),
        description=f"#{Rx('selected_issue.number')} · {Rx('selected_issue.state')} · {Rx('selected_issue.category')}",
    ):
        # Hidden trigger: the dialog opens programmatically from the selected issue.
        Button("", css_class="hidden")

        with Row(gap=2, css_class="flex-wrap mt-2"):
            Muted("Labels:")
            with ForEach("selected_issue.labels") as label:
                Badge(label, variant="secondary")

        with Row(gap=2, css_class="flex-wrap mt-2"):
            Muted("Assignees:")
            with ForEach("selected_issue.assignees") as person:
                Badge(person, variant="outline")

        with Row(gap=4, css_class="mt-4 text-sm"):
            Text(f"Created: {Rx('selected_issue.created_at')}")
            Text(f"Age: {Rx('selected_issue.age_days')} days")
            Text(f"Reactions: {Rx('selected_issue.reactions')}")
            Text(f"Comments: {Rx('selected_issue.comments')}")

        with Row(css_class="mt-4"):
            Button(
                "View on GitHub",
                variant="default",
                on_click=[
                    CallHandler("view_issue"),
                ],
            )
