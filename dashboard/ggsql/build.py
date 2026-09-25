# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "duckdb>=1",
#     "ggsql>=0.3",
#     "pandas>=2",
#     "polars>=1",
#     "pyarrow>=15",
#     "pyyaml>=6",
# ]
# ///
"""ggsql dashboard: render the dashboard/tiles.yml tiles to a static HTML page.

Each tile is one `queries/NN_<tile_id>.sql` file, numbered in tiles.yml order.
Chart files are ggsql (`SELECT … VISUALISE … DRAW …`) over a dbt dashboard
model; `-- type: kpi` / `-- type: table` files are plain SELECTs rendered as
HTML. Section questions, tile titles and subtitles come from tiles.yml.

Header comments:
    -- tile: <tile id in tiles.yml>
    -- type: chart | kpi | table      (default chart)
    -- order: y                       keep the query's row order on the y axis
                                      (ggsql sorts discrete axes alphabetically)

Reads FUSION_DB, else MotherDuck when MOTHERDUCK_TOKEN is set, else the local
DuckDB file (see dashboard/tiles.py).

Usage:
    uv run dashboard/ggsql/build.py
"""

from __future__ import annotations

import html
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import duckdb
import ggsql
import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import tiles  # noqa: E402

QUERIES_DIR = HERE / "queries"
OUT_HTML = HERE / "index.html"


class DuckDBConnReader:
    """ggsql-compatible reader wrapping a duckdb.Connection.

    Accepts any DuckDB connection string — a local file path or a MotherDuck
    URI like `md:fusion_issues`. ggsql's built-in DuckDBReader mangles
    absolute paths, so we expose the minimal `execute_sql` protocol instead.
    Strings are cast to Categorical because ggsql's discrete scales reject
    the Utf8View arrays polars produces.
    """

    def __init__(self, db_path: str) -> None:
        self._con = duckdb.connect(db_path, read_only=True)

    def execute_sql(self, sql: str) -> pl.DataFrame:
        df = self._con.execute(sql).pl()
        return df.with_columns(pl.col(c).cast(pl.Categorical) for c, t in df.schema.items() if t == pl.String)

    def select(self, sql: str) -> pl.DataFrame:
        return self._con.execute(sql).pl()

    def register(self, name: str, df: pl.DataFrame, *args, **kwargs) -> None:
        self._con.register(name, df)


HEADER_RE = re.compile(r"^--\s*(tile|type|order)\s*:\s*(.+?)\s*$", re.IGNORECASE)


@dataclass
class Tile:
    name: str
    tile_id: str
    query: str
    kind: str = "chart"  # "chart" | "kpi" | "table"
    order: str = ""
    spec_json: str = ""
    data: pl.DataFrame | None = None

    @property
    def select_sql(self) -> str:
        """The plain SQL part (before VISUALISE), header comments dropped."""
        body = re.split(r"^\s*VISUALI[SZ]E\b", self.query, maxsplit=1, flags=re.MULTILINE | re.IGNORECASE)[0]
        return "\n".join(line for line in body.splitlines() if not line.startswith("--"))


def load_tiles() -> dict[str, Tile]:
    loaded: dict[str, Tile] = {}
    for path in sorted(QUERIES_DIR.glob("*.sql")):
        text = path.read_text()
        meta = {m.group(1).lower(): m.group(2) for m in map(HEADER_RE.match, text.splitlines()) if m}
        t = Tile(name=path.stem, tile_id=meta["tile"], query=text,
                 kind=meta.get("type", "chart").lower(), order=meta.get("order", ""))
        loaded[t.tile_id] = t
    manifest_ids = [t["id"] for s in tiles.sections() for t in s["tiles"]]
    ordered = [QUERIES_DIR / f"{i:02d}_{tid}.sql" for i, tid in enumerate(manifest_ids, start=1)]
    missing = [p.name for p in ordered if not p.exists()]
    if missing or len(loaded) != len(manifest_ids):
        raise SystemExit(f"queries/ must hold exactly {[p.name for p in ordered]}; missing {missing}")
    return loaded


def keep_query_order(spec: dict, t: Tile, reader: DuckDBConnReader) -> dict:
    """Override the alphabetical domain of a discrete axis with the query's row order."""
    visualise = re.search(r"VISUALI[SZ]E\s+(.+)", t.query, re.IGNORECASE).group(1)
    column = re.search(rf"(\w+)\s+AS\s+{t.order}\b", visualise, re.IGNORECASE).group(1)
    domain = list(dict.fromkeys(reader.select(t.select_sql)[column].to_list()))
    for layer in spec.get("layer", [spec]):
        enc = layer.get("encoding", {}).get(t.order)
        if enc and enc.get("type") == "nominal":
            enc.setdefault("scale", {})["domain"] = domain
    return spec


def render(loaded: dict[str, Tile], db_path: str) -> None:
    reader = DuckDBConnReader(db_path)
    writer = ggsql.VegaLiteWriter()
    for t in loaded.values():
        if t.kind in ("kpi", "table"):
            t.data = reader.select(t.select_sql)
        else:
            spec = json.loads(writer.render(ggsql.execute(t.query, reader)))
            if t.order:
                spec = keep_query_order(spec, t, reader)
            t.spec_json = json.dumps(spec)


HEAD = """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — ggsql</title>
<script src="https://cdn.jsdelivr.net/npm/vega@6"></script>
<script src="https://cdn.jsdelivr.net/npm/vega-lite@6"></script>
<script src="https://cdn.jsdelivr.net/npm/vega-embed@7"></script>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
         max-width: 1040px; margin: 2rem auto; padding: 0 1rem; color: #1b1b1b; }
  h1 { margin-bottom: 0.25rem; }
  .subtitle { color: #555; margin: 0 0 0.5rem; }
  .source { color: #666; font-size: 0.9rem; margin-bottom: 2rem; }
  .source.stale { color: #7a3d00; background: #fff4e0; border: 1px solid #f0b060;
                  border-radius: 6px; padding: 0.5rem 0.75rem; font-weight: 600; }
  section.question { margin-bottom: 2.5rem; border-top: 2px solid #ddd; padding-top: 1rem; }
  section.question > h2 { margin: 0 0 1rem; }
  .tile { margin-bottom: 2rem; }
  .tile h3 { margin: 0 0 0.15rem; }
  .blurb { color: #555; margin: 0 0 0.75rem; }
  .chart { width: 100%; height: 360px; }
  details pre { background: #f6f8fa; padding: 0.75rem; overflow-x: auto; font-size: 0.85rem; }
  .kpi-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
             gap: 0.75rem; margin: 0.5rem 0 1rem; }
  .kpi { border: 1px solid #e5e7eb; border-radius: 6px; padding: 0.75rem 1rem; background: #fafafa; }
  .kpi .label { color: #666; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.04em; }
  .kpi .value { font-size: 1.6rem; font-weight: 600; margin-top: 0.25rem; }
  .kpi .context { color: #666; font-size: 0.85rem; margin-top: 0.15rem; }
  .table-wrap { overflow-x: auto; }
  table.data { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
  table.data th, table.data td { border-bottom: 1px solid #eee; padding: 0.4rem 0.6rem;
                                  text-align: left; vertical-align: top; }
  table.data th { background: #f6f8fa; font-weight: 600; }
  table.data td.num { text-align: right; font-variant-numeric: tabular-nums; }
  .pct { display: flex; align-items: center; gap: 0.4rem; min-width: 120px; }
  .pct .bar { flex: 1; height: 8px; background: #eee; border-radius: 4px; overflow: hidden; }
  .pct .bar span { display: block; height: 100%; background: #2a78d6; }
</style>
"""

LINK_COLUMNS = {"issue_number", "epic_number", "title"}


def _humanize(col: str) -> str:
    return col.replace("is_", "").replace("_", " ").strip().capitalize()


def _kpi_html(t: Tile) -> str:
    assert t.data is not None
    cards = "\n".join(
        f'<div class="kpi"><div class="label">{html.escape(k["label"])}</div>'
        f'<div class="value">{html.escape(k["value"])}</div>'
        f'<div class="context">{html.escape(k["context"])}</div></div>'
        for k in tiles.kpis(t.data.row(0, named=True))
    )
    return f'<div class="kpi-row">{cards}</div>'


def _cell(col: str, v, row: dict) -> str:
    if v is None:
        return ""
    if col == "pct_complete":
        return f'<div class="pct"><div class="bar"><span style="width:{v:.0f}%"></span></div>{v:.0f}%</div>'
    if isinstance(v, bool):
        return "yes" if v else ""
    text = f"#{v}" if col in ("issue_number", "epic_number") else str(v)
    if col == "issue_category":
        text = tiles.label("issue_category", v)
    text = html.escape(text)
    if col in LINK_COLUMNS and row.get("issue_url"):
        return f'<a href="{html.escape(row["issue_url"])}" target="_blank">{text}</a>'
    return text


def _table_html(t: Tile) -> str:
    assert t.data is not None
    cols = [c for c in t.data.columns if c != "issue_url"]
    right = {c for c, dt in t.data.schema.items()
             if dt.is_numeric() and c not in ("issue_number", "epic_number", "pct_complete")}
    head = "".join(f"<th>{'#' if c in ('issue_number', 'epic_number') else _humanize(c)}</th>" for c in cols)
    rows = [
        "<tr>" + "".join(
            ('<td class="num">' if c in right else "<td>") + _cell(c, row[c], row) + "</td>" for c in cols
        ) + "</tr>"
        for row in t.data.iter_rows(named=True)
    ]
    return ('<div class="table-wrap"><table class="data"><thead><tr>' + head + "</tr></thead><tbody>"
            + "\n".join(rows) + "</tbody></table></div>")


def to_html(loaded: dict[str, Tile], db_url: str) -> str:
    meta = tiles.one("dashboard_meta")
    stale = meta["days_stale"] > tiles.MANIFEST["meta"]["stale_after_days"]
    body = [
        f"<h1>{html.escape(tiles.MANIFEST['title'])}</h1>",
        f'<p class="subtitle">{html.escape(tiles.MANIFEST["subtitle"])}</p>',
        f'<div class="source{" stale" if stale else ""}">{html.escape(tiles.freshness_note(meta))}'
        f' · rendered from <code>{html.escape(db_url)}</code> via ggsql → Vega-Lite</div>',
    ]
    embeds: list[str] = []
    for section in tiles.sections():
        body.append(f'<section class="question"><h2>{html.escape(section["question"])}</h2>')
        for tile in section["tiles"]:
            t = loaded[tile["id"]]
            body.append('<div class="tile">')
            if tile.get("title"):
                body.append(f"<h3>{html.escape(tile['title'])}</h3>")
            if tile.get("subtitle"):
                body.append(f'<p class="blurb">{html.escape(tile["subtitle"])}</p>')
            if t.kind == "kpi":
                body.append(_kpi_html(t))
            elif t.kind == "table":
                body.append(_table_html(t))
            else:
                body.append(f'<div id="chart-{t.name}" class="chart"></div>')
                embeds.append(f"vegaEmbed('#chart-{t.name}', {t.spec_json}, {{actions: true}});")
            body.append(
                f"<details><summary>ggsql query ({t.name}.sql)</summary>"
                f"<pre>{html.escape(t.query.strip())}</pre></details>"
            )
            body.append("</div>")
        body.append("</section>")
    script = "<script>\n" + "\n".join(embeds) + "\n</script>"
    return HEAD.replace("{title}", html.escape(tiles.MANIFEST["title"])) + "\n".join(body) + "\n" + script


def main() -> None:
    db_path = tiles.db_path()
    print(f"[ggsql] using {db_path}")
    loaded = load_tiles()
    print(f"[ggsql] loaded {len(loaded)} tiles from {QUERIES_DIR}")
    render(loaded, db_path)
    OUT_HTML.write_text(to_html(loaded, db_path))
    print(f"[ggsql] wrote {OUT_HTML} ({OUT_HTML.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
