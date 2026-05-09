#!/usr/bin/env python
from __future__ import annotations

import json
import os
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import duckdb


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
SOURCE_ROOT = Path(os.environ.get("FUSION_PROJECT_ROOT", REPO_ROOT))
SOURCE_DB = os.environ.get("FUSION_DB", str(SOURCE_ROOT / "data" / "fusion_issues.duckdb"))
OUT_PATH = HERE / "data" / "issue-health.json"


def _json_default(value: Any) -> str:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    raise TypeError(f"Cannot serialize {type(value)!r}")


def _rows(con: duckdb.DuckDBPyConnection, query: str) -> list[dict[str, Any]]:
    result = con.execute(query)
    columns = [column[0] for column in result.description]
    return [dict(zip(columns, row, strict=True)) for row in result.fetchall()]


def _one(con: duckdb.DuckDBPyConnection, query: str) -> dict[str, Any]:
    rows = _rows(con, query)
    if not rows:
        return {}
    return rows[0]


def _sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def build_payload() -> dict[str, Any]:
    if not SOURCE_DB.startswith("md:") and not Path(SOURCE_DB).exists():
        raise SystemExit(
            f"Missing source database: {SOURCE_DB}\n"
            "Run `make dbt`, set FUSION_DB, or point FUSION_PROJECT_ROOT at a checkout with data/fusion_issues.duckdb."
        )

    con = duckdb.connect(":memory:")
    con.execute("SET file_search_path = ?", [str(SOURCE_ROOT / "transform")])
    con.execute(f"ATTACH {_sql_string(SOURCE_DB)} AS fusion_issues (READ_ONLY)")
    try:
        payload = {
            "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "summary_kpis": _one(
                con,
                """
                select
                  opened_4w,
                  closed_4w,
                  open_issues,
                  total_issues,
                  rolling_median_close_days,
                  pct_responded_48h,
                  stale_count
                from fusion_issues.main.summary_kpis
                """,
            ),
            "triage_health": _one(
                con,
                """
                select
                  total_open,
                  pct_labeled,
                  pct_assigned,
                  pct_milestoned,
                  pct_typed,
                  unlabeled_count,
                  unassigned_count
                from fusion_issues.main.triage_health
                """,
            ),
            "weekly_flow": _rows(
                con,
                """
                select week, opened, closed
                from fusion_issues.main.weekly_flow
                order by week
                """,
            ),
            "open_vs_closed_by_category": _rows(
                con,
                """
                select issue_category, state, n
                from fusion_issues.main.open_vs_closed_by_category
                order by issue_category, state
                """,
            ),
            "community_priorities": _rows(
                con,
                """
                select
                  issue_number,
                  title,
                  issue_category,
                  reactions_total_count,
                  comments_total_count,
                  age_days,
                  'https://github.com/dbt-labs/dbt-fusion/issues/' || issue_number::varchar as url
                from fusion_issues.main.community_priorities
                order by reactions_total_count desc, comments_total_count desc
                limit 12
                """,
            ),
            "open_epics": _rows(
                con,
                """
                select
                  epic_number,
                  epic_url,
                  title,
                  state,
                  child_total,
                  child_open,
                  child_closed,
                  pct_complete
                from fusion_issues.main.fct_epics
                where state = 'OPEN'
                order by child_open desc, child_total desc, epic_number
                limit 8
                """,
            ),
        }
    finally:
        con.close()

    return payload


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(build_payload(), default=_json_default, indent=2) + "\n")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
