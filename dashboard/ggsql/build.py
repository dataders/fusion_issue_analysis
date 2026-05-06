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


HEADER_RE = re.compile(r"^--\s*(title|blurb|type)\s*:\s*(.+?)\s*$", re.IGNORECASE)


@dataclass
class Chart:
    name: str
    title: str
    blurb: str
    query: str
    kind: str = "chart"  # "chart" | "kpi" | "table"
    spec_json: str = ""
    data: pl.DataFrame | None = None


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
        kind = meta.get("type", "chart").lower()
        charts.append(Chart(name=path.stem, title=title, blurb=blurb, query=text, kind=kind))
    if not charts:
        raise SystemExit(f"no *.sql files found under {QUERIES_DIR}")
    return charts


def _strip_header(query: str) -> str:
    lines = []
    in_header = True
    for line in query.splitlines():
        if in_header and (not line.strip() or line.startswith("--")):
            continue
        in_header = False
        lines.append(line)
    return "\n".join(lines)


def render(charts: list[Chart], db_path: str) -> None:
    # Local dev marts are DuckDB views over parquet at paths relative to the
    # dbt project root, so we have to run the queries from there. MotherDuck
    # marts are materialized tables with no such dependency.
    if not db_path.startswith("md:"):
        os.chdir(ROOT / "transform")
    reader = DuckDBConnReader(db_path)
    writer = ggsql.VegaLiteWriter()
    for c in charts:
        if c.kind in ("kpi", "table"):
            c.data = reader.execute_sql(_strip_header(c.query))
        else:
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
  .kpi-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
             gap: 0.75rem; margin: 0.5rem 0 1rem; }
  .kpi { border: 1px solid #e5e7eb; border-radius: 6px; padding: 0.75rem 1rem; background: #fafafa; }
  .kpi .label { color: #666; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.04em; }
  .kpi .value { font-size: 1.6rem; font-weight: 600; margin-top: 0.25rem; }
  table.data { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
  table.data th, table.data td { border-bottom: 1px solid #eee; padding: 0.4rem 0.6rem;
                                  text-align: left; vertical-align: top; }
  table.data th { background: #f6f8fa; font-weight: 600; }
  table.data td.num { text-align: right; font-variant-numeric: tabular-nums; }
</style>
"""


def _humanize(col: str) -> str:
    return col.replace("_", " ").replace("count", "").strip().title()


def _kpi_html(c: Chart) -> str:
    assert c.data is not None
    row = c.data.row(0, named=True) if c.data.height else {}
    cards = "\n".join(
        f'<div class="kpi"><div class="label">{_humanize(k)}</div>'
        f'<div class="value">{v if v is not None else "—"}</div></div>'
        for k, v in row.items()
    )
    return f'<div class="kpi-row">{cards}</div>'


def _table_html(c: Chart) -> str:
    assert c.data is not None
    cols = c.data.columns
    numeric = {col for col, dt in zip(cols, c.data.dtypes) if dt.is_numeric()}
    head = "".join(f"<th>{_humanize(col)}</th>" for col in cols)
    rows_html = []
    for row in c.data.iter_rows(named=True):
        cells = []
        for col in cols:
            v = row[col]
            cls = ' class="num"' if col in numeric else ""
            if col == "issue_url" and v:
                cell = f'<a href="{v}">link</a>'
            elif col == "issue_number" and v is not None and row.get("issue_url"):
                cell = f'<a href="{row["issue_url"]}">#{v}</a>'
            else:
                cell = "" if v is None else str(v)
            cells.append(f"<td{cls}>{cell}</td>")
        rows_html.append("<tr>" + "".join(cells) + "</tr>")
    drop_url = "issue_url" in cols and "issue_number" in cols
    if drop_url:
        # `issue_number` already links; hide the redundant URL column.
        idx = cols.index("issue_url")
        head = "".join(f"<th>{_humanize(col)}</th>" for col in cols if col != "issue_url")
        rows_html = []
        for row in c.data.iter_rows(named=True):
            cells = []
            for col in cols:
                if col == "issue_url":
                    continue
                v = row[col]
                cls = ' class="num"' if col in numeric else ""
                if col == "issue_number" and v is not None and row.get("issue_url"):
                    cell = f'<a href="{row["issue_url"]}">#{v}</a>'
                else:
                    cell = "" if v is None else str(v)
                cells.append(f"<td{cls}>{cell}</td>")
            rows_html.append("<tr>" + "".join(cells) + "</tr>")
    return (
        '<table class="data"><thead><tr>' + head + "</tr></thead>"
        "<tbody>" + "\n".join(rows_html) + "</tbody></table>"
    )


def to_html(charts: list[Chart], db_url: str) -> str:
    # Render KPIs and tables first so the operational view sits above the charts.
    order = {"kpi": 0, "table": 1, "chart": 2}
    ordered = sorted(charts, key=lambda c: (order.get(c.kind, 2), c.name))
    body = [
        "<h1>ggsql spike</h1>",
        f'<div class="source">Rendered from <code>{db_url}</code> via ggsql → Vega-Lite.</div>',
    ]
    embeds: list[str] = []
    for c in ordered:
        body.append("<section>")
        body.append(f"<h2>{c.title}</h2>")
        if c.blurb:
            body.append(f'<div class="blurb">{c.blurb}</div>')
        if c.kind == "kpi":
            body.append(_kpi_html(c))
        elif c.kind == "table":
            body.append(_table_html(c))
        else:
            body.append(f'<div id="chart-{c.name}" class="chart"></div>')
            embeds.append(f"vegaEmbed('#chart-{c.name}', {c.spec_json}, {{actions: true}});")
        body.append(
            f"<details><summary>ggsql query ({c.name}.sql)</summary>"
            f"<pre>{c.query.strip()}</pre></details>"
        )
        body.append("</section>")
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
