# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "duckdb>=1",
#     "ggsql>=0.2.7",
#     "polars>=1",
#     "pyarrow>=15",
# ]
# ///
"""ggsql spike: render Fusion-issue charts to a static HTML page.

Each chart lives in its own `queries/*.sql` file with a two-line header
(`-- title:` and `-- blurb:`). Files are rendered in filename order, so
prefix them `01_`, `02_`, … to control the layout.

Runs against the local DuckDB file by default. Set FUSION_DB to point at
another DuckDB path.

Usage:
    uv run dashboard/ggsql_spike/build.py
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

import duckdb
import ggsql
import polars as pl

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
QUERIES_DIR = HERE / "queries"
DEFAULT_DB = str(ROOT / "data" / "fusion_issues.duckdb")
OUT_HTML = HERE / "index.html"


class DuckDBConnReader:
    """ggsql-compatible reader wrapping a duckdb.Connection.

    Accepts any DuckDB-compatible connection string — a local file path or a
    MotherDuck URI like `md:fusion_issues`. ggsql's built-in DuckDBReader
    mangles absolute paths, so we expose the minimal `execute_sql` protocol
    ggsql accepts instead.
    """

    def __init__(self, db_path: str) -> None:
        self._con = duckdb.connect(db_path, read_only=True)

    def execute_sql(self, sql: str) -> pl.DataFrame:
        return self._con.execute(sql).pl()

    def register(self, name: str, df: pl.DataFrame, *args, **kwargs) -> None:
        self._con.register(name, df)


HEADER_RE = re.compile(r"^--\s*(title|blurb)\s*:\s*(.+?)\s*$", re.IGNORECASE)


@dataclass
class Chart:
    name: str
    title: str
    blurb: str
    query: str
    spec_json: str = ""


def load_charts() -> list[Chart]:
    charts: list[Chart] = []
    for path in sorted(QUERIES_DIR.glob("*.sql")):
        text = path.read_text()
        meta: dict[str, str] = {}
        for line in text.splitlines():
            if not line.strip():
                continue
            if not line.startswith("--"):
                break
            m = HEADER_RE.match(line)
            if m:
                meta[m.group(1).lower()] = m.group(2)
        title = meta.get("title") or path.stem
        blurb = meta.get("blurb", "")
        charts.append(Chart(name=path.stem, title=title, blurb=blurb, query=text))
    if not charts:
        raise SystemExit(f"no *.sql files found under {QUERIES_DIR}")
    return charts


def render(charts: list[Chart], db_path: str) -> None:
    # Local dev marts are DuckDB views over parquet at paths relative to the
    # dbt project root, so we have to run the queries from there. MotherDuck
    # marts are materialized tables with no such dependency.
    if not db_path.startswith("md:"):
        os.chdir(ROOT / "transform")
    reader = DuckDBConnReader(db_path)
    writer = ggsql.VegaLiteWriter()
    for c in charts:
        spec = ggsql.execute(c.query, reader)
        c.spec_json = writer.render(spec)


HEAD = """<!doctype html>
<meta charset="utf-8">
<title>ggsql spike — Fusion issue analysis</title>
<script src="https://cdn.jsdelivr.net/npm/vega@6"></script>
<script src="https://cdn.jsdelivr.net/npm/vega-lite@6"></script>
<script src="https://cdn.jsdelivr.net/npm/vega-embed@7"></script>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
         max-width: 960px; margin: 2rem auto; padding: 0 1rem; color: #1b1b1b; }
  h1 { margin-bottom: 0.25rem; }
  .source { color: #666; font-size: 0.9rem; margin-bottom: 2rem; }
  section { margin-bottom: 2.5rem; border-top: 1px solid #eee; padding-top: 1.25rem; }
  h2 { margin-bottom: 0.25rem; }
  .blurb { color: #555; margin-bottom: 0.75rem; }
  .chart { width: 100%; height: 360px; }
  details pre { background: #f6f8fa; padding: 0.75rem; overflow-x: auto; font-size: 0.85rem; }
</style>
"""


def to_html(charts: list[Chart], db_url: str) -> str:
    body = [
        "<h1>ggsql spike</h1>",
        f'<div class="source">Rendered from <code>{db_url}</code> via ggsql → Vega-Lite.</div>',
    ]
    embeds: list[str] = []
    for c in charts:
        body.append("<section>")
        body.append(f"<h2>{c.title}</h2>")
        if c.blurb:
            body.append(f'<div class="blurb">{c.blurb}</div>')
        body.append(f'<div id="chart-{c.name}" class="chart"></div>')
        body.append(
            f"<details><summary>ggsql query ({c.name}.sql)</summary>"
            f"<pre>{c.query.strip()}</pre></details>"
        )
        body.append("</section>")
        embeds.append(f"vegaEmbed('#chart-{c.name}', {c.spec_json}, {{actions: true}});")
    script = "<script>\n" + "\n".join(embeds) + "\n</script>"
    return HEAD + "\n".join(body) + "\n" + script


def main() -> None:
    db_path = os.environ.get("FUSION_DB", DEFAULT_DB)
    print(f"[ggsql-spike] using {db_path}")
    charts = load_charts()
    print(f"[ggsql-spike] loaded {len(charts)} queries from {QUERIES_DIR}")
    render(charts, db_path)
    OUT_HTML.write_text(to_html(charts, db_path))
    print(f"[ggsql-spike] wrote {OUT_HTML} ({OUT_HTML.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
