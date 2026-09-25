"""
Generate CSV files for the MDV dashboard.

MDV does not query databases directly, so this script keeps warehouse access
in the build step and lets dashboard.mdv stay Markdown-native. Tiles follow
dashboard/tiles.yml and read only the dbt dashboard models via the shared
tiles helper; this script only selects, sorts, renames, formats and pivots.

MDV v1 has table, stat, bar (single series), line and pie blocks — no
stacking, no horizontal bars, no custom colors, no links. So:
  - stacked bars become crosstab tables (one column per stack segment),
  - the stacked area and the grouped bar become multi-series lines,
  - postprocess.py recolors series to the tiles.yml palette and turns issue
    URLs into links after rendering.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tiles  # noqa: E402

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
CATEGORIES = tiles.categories("issue_category")  # feature, bug, task, other


def write_csv(filename: str, rows: list[dict[str, Any]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / filename
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"  wrote {path} ({len(rows)} records)")


def issue_type(row: dict) -> str:
    return tiles.label("issue_category", row["issue_category"])


def yes(value) -> str:
    return "yes" if value else ""


def pct_bar(pct: float | None, width: int = 10) -> str:
    """Text progress bar — MDV tables have no per-cell styling."""
    pct = pct or 0
    filled = round(pct / 100 * width)
    return "█" * filled + "░" * (width - filled) + f" {pct:.0f}%"


def crosstab(tile_id: str, index: str, header: str, total: str | None = None) -> None:
    """Long (index, issue_category, issue_count) -> one row per index, one column per type."""
    rows = tiles.tile_rows(tile_id)
    totals = {r[index]: r[total] for r in rows} if total else {}
    wide = tiles.pivot(rows, index=index, column="issue_category", value="issue_count")
    write_csv(f"{tile_id}.csv", [
        {header: r[index],
         **{tiles.label("issue_category", c): int(r.get(c, 0)) for c in CATEGORIES},
         **({"Total": int(totals[r[index]])} if total else {})}
        for r in wide
    ])


def main() -> None:
    # -- Header: freshness (dashboard_meta) --
    meta = tiles.one("dashboard_meta")
    stale = meta["days_stale"] > tiles.MANIFEST["meta"]["stale_after_days"]
    freshness = [
        {"label": "Data as of", "value": str(meta["as_of_date"])[:10], "delta": ""},
        {"label": f"label {meta['source_label']}", "value": meta["source_repo"], "delta": ""},
    ]
    if stale:
        freshness.append({"label": "⚠ The extract may have stopped",
                          "value": f"{meta['days_stale']} days old", "delta": f"-{meta['days_stale']} days"})
    write_csv("dashboard_meta.csv", freshness)

    # -- Where do things stand? headline_kpis formatted per tiles.yml --
    write_csv("headline_kpis.csv", [
        {"label": f"{k['label']} · {k['context']}" if k["context"] else k["label"], "value": k["value"], "delta": ""}
        for k in tiles.kpis()
    ])

    # -- Is the backlog shrinking? --
    # Rows are ordered week, then palette order, so series appear feature,
    # bug, task, other (postprocess.py colors them in that order).
    rank = {c: i for i, c in enumerate(CATEGORIES)}
    backlog = sorted(tiles.tile_rows("backlog_weekly"), key=lambda r: (r["week"], rank[r["issue_category"]]))
    write_csv("backlog_weekly.csv", [
        {"week": r["week"], "type": issue_type(r), "open_issues": r["open_issues"]} for r in backlog
    ])
    write_csv("weekly_flow.csv", [
        {"week": r["week"], "series": tiles.label("flow", s), "issues": r[s]}
        for r in tiles.tile_rows("weekly_flow") for s in ("opened", "closed")
    ])

    # -- Are we keeping up with triage? --
    pipeline = tiles.tile_rows("triage_pipeline")
    buckets = list(dict.fromkeys(r["age_bucket"] for r in pipeline))
    by_status = tiles.pivot(pipeline, index="status_label", column="age_bucket", value="issue_count")
    write_csv("triage_pipeline.csv", [
        {"Triage status": r["status_label"], **{b: int(r[b]) for b in buckets}} for r in by_status
    ])
    write_csv("response_weekly.csv", [
        {"week": r["week"], "pct_answered_48h": r["pct_responded_48h"] or 0} for r in tiles.tile_rows("response_weekly")
    ])
    write_csv("triage_queue.csv", [
        {"#": r["issue_url"], "Title": r["title"], "Type": issue_type(r), "Age (days)": r["age_days"],
         "Idle (days)": r["days_idle"], "Reactions": r["reactions"], "Comments": r["comments"],
         "Customer": yes(r["is_customer_reported"])}
        for r in tiles.tile_rows("triage_queue")
    ])

    # -- Where is the work? --
    crosstab("open_by_area", "area", "Area", total="area_total")
    crosstab("open_by_adapter", "adapter", "Adapter", total="adapter_total")

    # -- How close are the epics? --
    write_csv("epic_progress.csv", [
        {"#": r["issue_url"], "Epic": r["title"], "Closed": r["child_closed"], "Sub-issues": r["child_total"],
         "% closed": pct_bar(r["pct_complete"]), "Milestone": r["milestone_title"]}
        for r in tiles.tile_rows("epic_progress")
    ])

    # -- What should we work on, and who is on it? --
    write_csv("top_requested.csv", [
        {"#": r["issue_url"], "Title": r["title"], "Type": issue_type(r), "Areas": r["areas"],
         "Triage": r["triage_status"], "Reactions": r["reactions"], "Comments": r["comments"],
         "Age (days)": r["age_days"], "Customer": yes(r["is_customer_reported"])}
        for r in tiles.tile_rows("top_requested")
    ])
    crosstab("assignee_workload", "assignee_login", "Assignee", total="assignee_total")

    print("\nDone. All data files written to mdv/data/")


if __name__ == "__main__":
    main()
