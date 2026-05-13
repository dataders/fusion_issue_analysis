from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

import duckdb
import fastmcp
from fastmcp.apps import AppConfig, ResourceCSP

GRAPHENE_DIR = Path(__file__).resolve().parent
HTML_PATH = GRAPHENE_DIR / "widget" / "dist" / "index.html"
RESOURCE_URI = "ui://fusion-graphene/issue-health.html"

if not HTML_PATH.exists():
    raise SystemExit(f"Widget not built. Run: make graphene\n(expected: {HTML_PATH})")

mcp = fastmcp.FastMCP("Fusion Issue Health (Graphene)")


def _normalize(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        as_int = int(value)
        return as_int if value == as_int else float(value)
    return value


def _rows(conn: duckdb.DuckDBPyConnection, sql: str) -> list[dict]:
    result = conn.execute(sql)
    columns = [d[0] for d in result.description]
    return [
        {col: _normalize(val) for col, val in zip(columns, row)}
        for row in result.fetchall()
    ]


@mcp.tool(app=AppConfig(resource_uri=RESOURCE_URI))
def get_dashboard_data() -> dict:
    """Return all six Fusion issue dashboard tables from MotherDuck as JSON."""
    with duckdb.connect() as conn:
        conn.execute("INSTALL motherduck; LOAD motherduck;")
        conn.execute("ATTACH 'md:fusion_issues' AS fusion_issues (READ_ONLY);")

        summary_kpis = _rows(
            conn,
            """
            SELECT
              opened_4w,
              closed_4w,
              open_issues,
              total_issues,
              rolling_median_close_days,
              pct_responded_48h,
              stale_count
            FROM fusion_issues.main.summary_kpis
            """,
        )[0]

        triage_health = _rows(
            conn,
            """
            SELECT
              total_open,
              pct_labeled,
              pct_assigned,
              pct_milestoned,
              pct_typed,
              unlabeled_count,
              unassigned_count
            FROM fusion_issues.main.triage_health
            """,
        )[0]

        weekly_flow = _rows(
            conn,
            """
            SELECT
              CAST(week AS DATE) AS week,
              opened,
              closed
            FROM fusion_issues.main.weekly_flow
            ORDER BY week
            """,
        )

        categories = _rows(
            conn,
            """
            SELECT
              issue_category,
              state,
              n
            FROM fusion_issues.main.open_vs_closed_by_category
            ORDER BY issue_category, state
            """,
        )

        response_pctiles = _rows(
            conn,
            """
            SELECT
              CAST(week AS DATE) AS week,
              p25,
              p50,
              p75
            FROM fusion_issues.main.response_pctiles
            ORDER BY week
            """,
        )

        community_priorities = _rows(
            conn,
            """
            SELECT
              issue_number,
              title,
              issue_category,
              reactions_total_count,
              comments_total_count,
              age_days,
              'https://github.com/dbt-labs/dbt-fusion/issues/' || CAST(issue_number AS VARCHAR) AS url
            FROM fusion_issues.main.community_priorities
            ORDER BY reactions_total_count DESC, comments_total_count DESC
            """,
        )

    return {
        "summary_kpis": summary_kpis,
        "triage_health": triage_health,
        "weekly_flow": weekly_flow,
        "categories": categories,
        "response_pctiles": response_pctiles,
        "community_priorities": community_priorities,
    }


@mcp.resource(RESOURCE_URI, app=AppConfig(csp=ResourceCSP()))
def graphene_view() -> str:
    return HTML_PATH.read_text()


if __name__ == "__main__":
    mcp.run()
