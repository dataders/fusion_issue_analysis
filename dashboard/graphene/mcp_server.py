import atexit
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root so MOTHERDUCK_TOKEN etc. don't need to be
# hardcoded in claude_desktop_config.json.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

import duckdb
import fastmcp
from fastmcp.apps import AppConfig, ResourceCSP

import build as graphene_build

GRAPHENE_DIR = Path(__file__).resolve().parent
DB_PATH = GRAPHENE_DIR / "fusion_graphene.duckdb"
RESOURCE_URI = "ui://fusion-graphene/issue-health.html"
GRAPHENE_PORT = 4000
GRAPHENE_URL = f"http://localhost:{GRAPHENE_PORT}"


def _build_snapshot() -> None:
    # Redirect stdout so build.py's print() doesn't corrupt the stdio transport.
    sys.stdout = sys.stderr
    try:
        graphene_build.build_snapshot()
    finally:
        sys.stdout = sys.__stdout__


def _start_graphene_serve() -> subprocess.Popen:
    proc = subprocess.Popen(
        ["npm", "exec", "graphene", "--", "serve"],
        cwd=str(GRAPHENE_DIR),
        stdout=sys.stderr,
        stderr=sys.stderr,
    )
    atexit.register(proc.terminate)

    for _ in range(30):
        try:
            urllib.request.urlopen(f"{GRAPHENE_URL}/", timeout=1)
            return proc
        except Exception:
            time.sleep(1)

    raise RuntimeError(f"graphene serve did not start on port {GRAPHENE_PORT} within 30s")


_build_snapshot()
_start_graphene_serve()

mcp = fastmcp.FastMCP("Fusion Issue Health (Graphene)")


@mcp.tool(app=AppConfig(resource_uri=RESOURCE_URI))
def show_issue_health() -> str:
    """Show dbt Fusion issue health as a live interactive dashboard."""
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


@mcp.resource(
    RESOURCE_URI,
    app=AppConfig(csp=ResourceCSP(frame_domains=[GRAPHENE_URL])),
)
def graphene_view() -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>html, body, iframe {{ margin: 0; padding: 0; width: 100%; height: 100vh; border: none; }}</style>
</head>
<body>
  <iframe src="{GRAPHENE_URL}/" allowfullscreen></iframe>
</body>
</html>"""


if __name__ == "__main__":
    mcp.run()
