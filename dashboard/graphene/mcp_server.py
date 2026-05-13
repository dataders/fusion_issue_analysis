import sys
from pathlib import Path

import duckdb
import fastmcp
from fastmcp.apps import AppConfig

import build as graphene_build

GRAPHENE_DIR = Path(__file__).resolve().parent
DB_PATH = GRAPHENE_DIR / "fusion_graphene.duckdb"
HTML_PATH = GRAPHENE_DIR / "index.html"
RESOURCE_URI = "ui://fusion-graphene/issue-health.html"

# Redirect stdout → stderr during build so print() doesn't corrupt the stdio transport.
sys.stdout = sys.stderr
graphene_build.main()
sys.stdout = sys.__stdout__

mcp = fastmcp.FastMCP("Fusion Issue Health (Graphene)")


@mcp.tool(app=AppConfig(resource_uri=RESOURCE_URI))
def show_issue_health() -> str:
    """Show dbt Fusion issue health as a live dashboard."""
    with duckdb.connect(str(DB_PATH), read_only=True) as conn:
        row = conn.execute("SELECT * FROM summary_kpis").fetchdf().to_dict("records")[0]

    opened = row.get("opened_4w", "?")
    closed = row.get("closed_4w", "?")
    open_issues = row.get("open_issues", "?")
    stale = row.get("stale_count", "?")
    responded = row.get("pct_responded_48h", "?")

    delta = int(closed) - int(opened) if isinstance(closed, (int, float)) and isinstance(opened, (int, float)) else 0
    trend = f"{abs(delta)} more {'closed' if delta >= 0 else 'opened'} than {'opened' if delta >= 0 else 'closed'}"

    return (
        f"{trend} in the last 4 weeks. "
        f"{open_issues} open issues, {stale} stale, {responded}% responded within 48h."
    )


@mcp.resource(RESOURCE_URI)
def graphene_view() -> str:
    return HTML_PATH.read_text()


if __name__ == "__main__":
    mcp.run()
