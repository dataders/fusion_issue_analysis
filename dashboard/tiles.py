"""Shared helpers for the Python-based bakeoff frameworks.

Reads the tile contract (tiles.yml) and the dbt dashboard models so each
framework only has to do layout and chart encoding:

    import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
    import tiles

    rows = tiles.query("backlog_weekly")
    wide = tiles.pivot(rows, index="week", column="issue_category", value="open_issues")
    color = tiles.color("issue_category", "bug")
"""

from __future__ import annotations

import os
import string
from functools import cache
from pathlib import Path

import duckdb
import yaml

DASHBOARD_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = DASHBOARD_DIR.parent
MANIFEST: dict = yaml.safe_load((DASHBOARD_DIR / "tiles.yml").read_text())


def db_path() -> str:
    """FUSION_DB wins, then MotherDuck when a token is set, then the local dev DB."""
    if os.environ.get("FUSION_DB"):
        return os.environ["FUSION_DB"]
    if os.environ.get("MOTHERDUCK_TOKEN"):
        return "md:fusion_issues"
    return str(PROJECT_ROOT / "data" / "fusion_issues.duckdb")


@cache
def _connection() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(db_path(), read_only=True)


def query(model: str, order_by: str | None = None) -> list[dict]:
    """All rows of one dashboard model. Frameworks select; they don't compute."""
    sql = f"select * from {model}" + (f" order by {order_by}" if order_by else "")
    return _connection().execute(sql).fetchdf().to_dict("records")


def one(model: str) -> dict:
    """The single row of a one-row model (dashboard_meta, headline_kpis)."""
    rows = query(model)
    assert len(rows) == 1, f"{model} should have exactly one row, got {len(rows)}"
    return rows[0]


def pivot(rows: list[dict], index: str, column: str, value: str) -> list[dict]:
    """Long -> wide for chart libraries that want one key per series.

    Keeps first-seen order of `index`; missing combinations become 0.
    """
    keys = list(dict.fromkeys(r[column] for r in rows))
    out: dict = {}
    for r in rows:
        row = out.setdefault(r[index], {index: r[index], **{k: 0 for k in keys}})
        row[r[column]] = r[value]
    return list(out.values())


def categories(palette_key: str) -> list[str]:
    """Series keys of a palette entry, in their fixed display order."""
    return list(MANIFEST["palette"][palette_key])


def color(palette_key: str, name: str, mode: str = "light") -> str:
    entry = MANIFEST["palette"][palette_key][name]
    return entry[mode] if isinstance(entry, dict) else entry


def label(palette_key: str, name: str) -> str:
    entry = MANIFEST["palette"][palette_key][name]
    return entry.get("label", name) if isinstance(entry, dict) else name


def tile(tile_id: str) -> dict:
    for section in MANIFEST["sections"]:
        for t in section["tiles"]:
            if t["id"] == tile_id:
                return t
    raise KeyError(tile_id)


def sections() -> list[dict]:
    return MANIFEST["sections"]


def tile_rows(tile_id: str) -> list[dict]:
    """Rows for a tile, in the order tiles.yml specifies."""
    t = tile(tile_id)
    return query(t["model"], order_by=t.get("order_by"))


def _fill(template, row: dict) -> str:
    """A bare column name or a str.format template over the row; '—' if any referenced value is null."""
    template = str(template)
    if "{" not in template:
        template = "{" + template + "}"
    fields = [f for _, f, _, _ in string.Formatter().parse(template) if f]
    if any(row.get(f) is None for f in fields):
        return "—"
    return template.format(**row)


def kpis(row: dict | None = None) -> list[dict]:
    """headline_kpis formatted per tiles.yml: [{label, value, context}]."""
    t = tile("headline_kpis")
    row = row or one(t["model"])
    row = {k: int(v) if isinstance(v, float) and v.is_integer() else v for k, v in row.items()}
    return [
        {"label": k["label"], "value": _fill(k["value"], row),
         "context": _fill(k["context"], row) if "context" in k else ""}
        for k in t["kpis"]
    ]


def freshness_note(meta: dict) -> str:
    as_of = str(meta["as_of_date"])[:10]
    note = f"Data as of {as_of} · {meta['source_repo']} · label {meta['source_label']}"
    if meta["days_stale"] > MANIFEST["meta"]["stale_after_days"]:
        note += f" · ⚠ {meta['days_stale']} days old — the extract may have stopped"
    return note
