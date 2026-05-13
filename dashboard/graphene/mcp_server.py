import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

import duckdb
import fastmcp
from fastmcp.apps import AppConfig, ResourceCSP

import build as graphene_build

GRAPHENE_DIR = Path(__file__).resolve().parent
HTML_PATH = GRAPHENE_DIR / "widget" / "dist" / "index.html"
RESOURCE_URI = "ui://fusion-graphene/issue-health.html"

# Build snapshot from MotherDuck → index.html at startup.
sys.stdout = sys.stderr
try:
    graphene_build.main()
finally:
    sys.stdout = sys.__stdout__

# Read KPIs directly from MotherDuck — no local DB lock contention.
with duckdb.connect() as _conn:
    _conn.execute("INSTALL motherduck; LOAD motherduck;")
    _conn.execute("ATTACH 'md:fusion_issues' AS fusion_issues (READ_ONLY);")
    _kpis = _conn.execute(
        "SELECT * FROM fusion_issues.main.summary_kpis"
    ).fetchdf().to_dict("records")[0]

mcp = fastmcp.FastMCP("Fusion Issue Health (Graphene)")


@mcp.tool(app=AppConfig(resource_uri=RESOURCE_URI))
def show_issue_health() -> str:
    """Show dbt Fusion issue health as a live interactive dashboard."""
    opened = _kpis.get("opened_4w", "?")
    closed = _kpis.get("closed_4w", "?")
    open_issues = _kpis.get("open_issues", "?")
    stale = _kpis.get("stale_count", "?")
    responded = _kpis.get("pct_responded_48h", "?")

    delta = int(closed) - int(opened) if isinstance(closed, (int, float)) and isinstance(opened, (int, float)) else 0
    trend = f"{abs(delta)} more {'closed' if delta >= 0 else 'opened'} than {'opened' if delta >= 0 else 'closed'}"

    return (
        f"{trend} in the last 4 weeks. "
        f"{open_issues} open issues, {stale} stale, {responded}% responded within 48h."
    )


@mcp.resource(RESOURCE_URI, app=AppConfig(csp=ResourceCSP()))
def graphene_view() -> str:
    return HTML_PATH.read_text()


if __name__ == "__main__":
    mcp.run()
