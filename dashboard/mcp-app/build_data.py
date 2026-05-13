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


def _number(value: Any) -> float:
    if value is None:
        return 0
    return float(value)


def _whole(value: Any) -> int:
    return int(round(_number(value)))


def _queue(
    queue_id: str,
    label: str,
    count: int,
    severity: str,
    why: str,
    action: str,
) -> dict[str, Any]:
    return {
        "id": queue_id,
        "label": label,
        "count": count,
        "severity": severity if count else "clear",
        "why": why,
        "action": action,
    }


def build_issue_pulse(payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload.get("summary_kpis", {})
    opened = _whole(summary.get("opened_4w"))
    closed = _whole(summary.get("closed_4w"))
    net_closed = closed - opened

    if net_closed > 0:
        state = "cooling"
        label = "Backlog cooling"
        headline = f"{net_closed} more closed than opened over the last 4 weeks"
    elif net_closed < 0:
        state = "heating"
        label = "Backlog heating"
        headline = f"{abs(net_closed)} more opened than closed over the last 4 weeks"
    else:
        state = "steady"
        label = "Backlog steady"
        headline = "Opened and closed volume matched over the last 4 weeks"

    return {
        "state": state,
        "label": label,
        "headline": headline,
        "opened_4w": opened,
        "closed_4w": closed,
        "net_closed_4w": net_closed,
        "response_pct_48h": _whole(summary.get("pct_responded_48h")),
    }


def build_attention_queues(payload: dict[str, Any]) -> list[dict[str, Any]]:
    ops = payload.get("operational_triage", {})
    triage = payload.get("triage_health", {})
    return [
        _queue(
            "slipped-through",
            "Slipped-through bugs",
            _whole(ops.get("slipped_through_count")),
            "critical",
            "Open bugs with zero triage signal.",
            "Work the oldest zero-signal bugs first.",
        ),
        _queue(
            "triage-queue",
            "Triage queue",
            _whole(ops.get("triage_queue_count")),
            "warning",
            "Issues already marked for triage.",
            "Decide owner, type, and next label.",
        ),
        _queue(
            "hard-blockers",
            "Hard blockers",
            _whole(ops.get("hard_blocker_count")),
            "critical",
            "Open issues carrying the hard-blocker label.",
            "Confirm release impact and unblock path.",
        ),
        _queue(
            "needs-repro",
            "Needs repro",
            _whole(ops.get("needs_repro_count")),
            "warning",
            "Bugs waiting on reproduction detail.",
            "Ask for repro steps or move to verified.",
        ),
        _queue(
            "stale",
            "Stale",
            _whole(ops.get("stale_count")),
            "watch",
            "Open issues stale by label or 90+ days without activity.",
            "Close, revive, or attach to a milestone.",
        ),
        _queue(
            "unassigned",
            "Unassigned",
            _whole(triage.get("unassigned_count")),
            "watch",
            "Open non-epic issues without an assignee.",
            "Assign a directly responsible owner.",
        ),
    ]


def build_agent_brief(payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload.get("summary_kpis", {})
    triage = payload.get("triage_health", {})
    ops = payload.get("operational_triage", {})
    pulse = payload["issue_pulse"]
    queues = payload["attention_queues"]
    oldest = payload.get("oldest_untriaged", [])

    top_queue = next((queue for queue in queues if queue["count"] > 0), queues[0])
    bullets = [
        f"{_whole(summary.get('open_issues'))} open issues; {_whole(summary.get('stale_count'))} stale by the 30-day dashboard definition.",
        f"{_whole(triage.get('pct_typed'))}% typed, {_whole(triage.get('pct_assigned'))}% assigned, {_whole(triage.get('pct_milestoned'))}% milestoned.",
        f"{_whole(ops.get('slipped_through_count'))} slipped-through bugs and {_whole(ops.get('triage_queue_count'))} issues in the triage queue.",
    ]
    if oldest:
        first = oldest[0]
        bullets.append(
            f"Oldest zero-signal bug: #{first['issue_number']} has waited {first['age_days']} days - {first['title']}."
        )

    return {
        "headline": f"{pulse['headline']}. Start with {top_queue['label'].lower()}.",
        "bullets": bullets,
        "suggested_prompts": [
            "Show the oldest zero-signal bugs",
            "Summarize what changed in issue health",
            "Find the highest-leverage triage queue",
        ],
    }


def enrich_payload(payload: dict[str, Any]) -> dict[str, Any]:
    payload["issue_pulse"] = build_issue_pulse(payload)
    payload["attention_queues"] = build_attention_queues(payload)
    payload["agent_brief"] = build_agent_brief(payload)
    return payload


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
            "operational_triage": _one(
                con,
                """
                select
                  total_open,
                  slipped_through_count,
                  triage_queue_count,
                  needs_repro_count,
                  repro_verified_count,
                  awaiting_release_count,
                  hard_blocker_count,
                  hard_blocker_unreleased,
                  stale_count
                from fusion_issues.main.issue_triage_health
                """,
            ),
            "oldest_untriaged": _rows(
                con,
                """
                select
                  issue_number,
                  title,
                  author_login,
                  issue_category,
                  reactions_total_count,
                  comments_total_count,
                  issue_url,
                  age_days,
                  days_since_activity
                from fusion_issues.main.oldest_untriaged
                order by age_days desc, issue_number
                limit 12
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
                  issue_number as epic_number,
                  'https://github.com/dbt-labs/dbt-fusion/issues/' || issue_number::varchar as epic_url,
                  title,
                  state,
                  null::integer as child_total,
                  null::integer as child_open,
                  null::integer as child_closed,
                  null::double as pct_complete,
                  reactions_total_count,
                  comments_total_count
                from fusion_issues.main.epic_list
                where state = 'OPEN'
                order by issue_number
                limit 8
                """,
            ),
        }
    finally:
        con.close()

    return enrich_payload(payload)


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(build_payload(), default=_json_default, indent=2) + "\n")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
