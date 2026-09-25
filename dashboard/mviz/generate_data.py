"""
Generate the mviz component specs (data/*.json) and palette theme.

dashboard.md is pure layout; every component reads one spec file from data/.
Tiles follow dashboard/tiles.yml and read only the dbt dashboard models via
the shared tiles helper. This script only selects, sorts, renames, formats
and pivots — no metrics.
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tiles  # noqa: E402

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
CATEGORIES = tiles.categories("issue_category")  # feature, bug, task, other
CATEGORY_LABELS = [tiles.label("issue_category", c) for c in CATEGORIES]


def write_json(filename: str, data) -> None:
    path = DATA_DIR / filename
    path.write_text(json.dumps(data, default=str))
    print(f"  wrote {path}")


def write_theme() -> None:
    """mviz colors series by index from one global palette, so every chart
    lists its series in this order: feature / closed / single series = blue,
    bug / opened = orange, task = green, other = grey (tiles.yml, light)."""
    palette = [tiles.color("issue_category", c) for c in CATEGORIES]
    assert tiles.color("flow", "closed") == palette[0] == tiles.MANIFEST["palette"]["single_series"]
    assert tiles.color("flow", "opened") == palette[1]
    lines = ["extends: light", "palette:", *[f'  - "{c}"' for c in palette]]
    (DATA_DIR / "theme.yaml").write_text("\n".join(lines) + "\n")


def link(row: dict, text) -> str:
    # mviz inserts string cells as raw HTML, so escape and wrap in an anchor.
    return f'<a href="{html.escape(row["issue_url"])}" target="_blank">{html.escape(str(text))}</a>'


def spec(tile_id: str, **fields) -> None:
    """One tile: its subtitle (a text component) and its chart/table spec."""
    t = tiles.tile(tile_id)
    write_json(f"{tile_id}_subtitle.json", {"content": t["subtitle"]})
    write_json(f"{tile_id}.json", {"title": t["title"], **fields})


def category_bars(tile_id: str, index: str) -> None:
    """Long (index, issue_category, issue_count) -> wide stacked horizontal bars.

    Rows arrive sorted by the *_total column, largest first; ECharts draws the
    first category at the bottom, so reverse to put the largest on top.
    """
    wide = tiles.pivot(tiles.tile_rows(tile_id), index=index, column="issue_category", value="issue_count")
    data = [{index: r[index], **{tiles.label("issue_category", c): r.get(c, 0) for c in CATEGORIES}} for r in wide]
    spec(tile_id, x=index, y=CATEGORY_LABELS, stacked=True, horizontal=True, format="num0",
         data=list(reversed(data)))


def issue_table(tile_id: str, number_col: str, columns: list[tuple[str, str, dict]], row_fn) -> None:
    cols = [{"id": "issue", "title": "#", "bold": True}, {"id": "title", "title": "Title"}]
    cols += [{"id": cid, "title": title, **opts} for cid, title, opts in columns]
    data = [{"issue": link(r, f"#{r[number_col]}"), "title": link(r, r["title"]), **row_fn(r)}
            for r in tiles.tile_rows(tile_id)]
    spec(tile_id, columns=cols, data=data, sortable=True, compact=True)


def issue_type(r: dict) -> str:
    return tiles.label("issue_category", r["issue_category"])


def yes(value) -> str:
    return "yes" if value else ""


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    write_theme()

    # -- Header: freshness banner; a warning note when the extract looks stopped --
    meta = tiles.one("dashboard_meta")
    stale = meta["days_stale"] > tiles.MANIFEST["meta"]["stale_after_days"]
    write_json("dashboard_meta.json", {
        "content": tiles.freshness_note(meta),
        "noteType": "warning" if stale else "tip",
        "label": "Stale data:" if stale else "Fresh:",
    })
    write_json("subtitle.json", {"content": tiles.MANIFEST["subtitle"]})

    # -- Where do things stand? headline_kpis, formatted per tiles.yml. mviz
    # big_value only takes a single number, so cards are small markdown blocks.
    for i, kpi in enumerate(tiles.kpis(), start=1):
        context = f"\n\n*{kpi['context']}*" if kpi["context"] else ""
        write_json(f"headline_kpis_{i}.json", {"content": f"### {kpi['value']}\n**{kpi['label']}**{context}"})

    # -- Is the backlog shrinking? --
    backlog = tiles.pivot(tiles.tile_rows("backlog_weekly"), index="week", column="issue_category", value="open_issues")
    spec("backlog_weekly", x="week", y=CATEGORY_LABELS, stacked=True, format="num0",
         data=[{"week": r["week"], **{tiles.label("issue_category", c): r[c] for c in CATEGORIES}} for r in backlog])

    closed, opened = tiles.label("flow", "closed"), tiles.label("flow", "opened")
    spec("weekly_flow", x="week", y=[closed, opened], format="num0",
         data=[{"week": r["week"], closed: r["closed"], opened: r["opened"]} for r in tiles.tile_rows("weekly_flow")])

    # -- Are we keeping up with triage? --
    # mviz has a single global palette (the issue-category colors), so the
    # status x age stacked bar is drawn as a status x age heatmap instead.
    pipeline = tiles.tile_rows("triage_pipeline")
    buckets = list(dict.fromkeys(r["age_bucket"] for r in pipeline))
    statuses = list(dict.fromkeys(r["status_label"] for r in pipeline))[::-1]  # first status on top
    spec("triage_pipeline", xCategories=buckets, yCategories=statuses, format="num0",
         data=[[buckets.index(r["age_bucket"]), statuses.index(r["status_label"]), r["issue_count"]]
               for r in pipeline])

    spec("response_weekly", x="week", y="answered_48h", format="pct0", yMin=0, yMax=1,
         data=[{"week": r["week"], "answered_48h": None if r["pct_responded_48h"] is None else r["pct_responded_48h"] / 100}
               for r in tiles.tile_rows("response_weekly")])

    issue_table("triage_queue", "issue_number", [
        ("type", "Type", {}), ("age_days", "Age (d)", {"fmt": "num0"}), ("days_idle", "Idle (d)", {"fmt": "num0"}),
        ("reactions", "Reactions", {"fmt": "num0"}), ("comments", "Comments", {"fmt": "num0"}),
        ("customer", "Customer", {}),
    ], lambda r: {"type": issue_type(r), "age_days": r["age_days"], "days_idle": r["days_idle"],
                  "reactions": r["reactions"], "comments": r["comments"], "customer": yes(r["is_customer_reported"])})

    # -- Where is the work? --
    category_bars("open_by_area", "area")
    category_bars("open_by_adapter", "adapter")

    # -- How close are the epics? --
    issue_table("epic_progress", "epic_number", [
        ("closed", "Closed", {"fmt": "num0"}), ("total", "Sub-issues", {"fmt": "num0"}),
        ("pct_complete", "% closed", {"type": "sparkline", "sparkType": "pct_bar"}),
        ("milestone", "Milestone", {}),
    ], lambda r: {"closed": r["child_closed"], "total": r["child_total"],
                  "pct_complete": (r["pct_complete"] or 0) / 100,  # pct_bar wants 0-1
                  "milestone": r["milestone_title"]})

    # -- What should we work on, and who is on it? --
    issue_table("top_requested", "issue_number", [
        ("type", "Type", {}), ("areas", "Areas", {}), ("triage", "Triage", {}),
        ("reactions", "Reactions", {"fmt": "num0"}), ("comments", "Comments", {"fmt": "num0"}),
        ("age_days", "Age (d)", {"fmt": "num0"}), ("customer", "Customer", {}),
    ], lambda r: {"type": issue_type(r), "areas": r["areas"], "triage": r["triage_status"],
                  "reactions": r["reactions"], "comments": r["comments"], "age_days": r["age_days"],
                  "customer": yes(r["is_customer_reported"])})

    category_bars("assignee_workload", "assignee_login")

    print("\nDone. All specs written to mviz/data/")


if __name__ == "__main__":
    main()
