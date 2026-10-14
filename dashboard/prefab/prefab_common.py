"""Helpers shared by the Prefab dashboard variants (app*.py).

Pure data shaping only: no layout, no theme, no metric logic. Each variant keeps
its own renderers and chrome; anything identical across them lives here so a
tile or contract change is made once.
"""

import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import tiles  # noqa: E402
from prefab_ui.components.charts import ChartSeries  # noqa: E402


def clean(rows: list[dict]) -> list[dict]:
    """NaN -> None so the baked-in JSON stays valid."""
    return [{k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in r.items()} for r in rows]


def rows(tile_id: str) -> list[dict]:
    return clean(tiles.tile_rows(tile_id))


def safe_key(name: str) -> str:
    """Series keys become CSS variables in the renderer; '180d+' would break them."""
    return re.sub(r"\W", "_", str(name))


def wide(tile_id: str, index: str, column: str = "issue_category", value: str = "issue_count") -> list[dict]:
    pivoted = tiles.pivot(rows(tile_id), index=index, column=column, value=value)
    return [{(k if k == index else safe_key(k)): v for k, v in r.items()} for r in pivoted]


def series(palette_key: str, data: list[dict], mode: str) -> list[ChartSeries]:
    """One series per palette entry present in the data, in palette order."""
    present = set().union(*(r.keys() for r in data)) if data else set()
    return [
        ChartSeries(data_key=safe_key(k), label=tiles.label(palette_key, k), color=tiles.color(palette_key, k, mode))
        for k in tiles.categories(palette_key)
        if safe_key(k) in present
    ]


def text_bar(pct) -> str:
    """pct_complete (0-100) as a 10-cell text bar. DataTable renders component
    cells outside the table in this Prefab version, so the bar is text."""
    filled = round((pct or 0) / 10)
    return "█" * filled + "░" * (10 - filled)


def page_meta() -> tuple[dict, str, bool, list[dict]]:
    """(dashboard_meta row, freshness note, is_stale, formatted headline KPIs)."""
    meta = tiles.one("dashboard_meta")
    is_stale = meta["days_stale"] > tiles.MANIFEST["meta"]["stale_after_days"]
    return meta, tiles.freshness_note(meta), is_stale, tiles.kpis()
