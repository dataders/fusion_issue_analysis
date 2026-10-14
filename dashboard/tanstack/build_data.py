"""Bake the shared dbt tile contract into the TanStack Charts static bundle."""

from __future__ import annotations

import json
import math
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import tiles  # noqa: E402


def json_value(value):
    """Preserve missing values and serialize native/pandas database scalars."""
    if isinstance(value, dict):
        return {key: json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_value(item) for item in value]
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, Decimal):
        value = float(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, (date, datetime)):
        return value.isoformat()[:10]
    return value


def build_payload():
    meta = tiles.one(tiles.MANIFEST["meta"]["model"])
    rows = {tile["id"]: tiles.tile_rows(tile["id"]) for section in tiles.sections() for tile in section["tiles"]}
    return json_value(
        {
            "manifest": tiles.MANIFEST,
            "rows": rows,
            "kpis": tiles.kpis(rows["headline_kpis"][0]),
            "freshness": tiles.freshness_note(meta),
            "is_stale": meta["days_stale"] > tiles.MANIFEST["meta"]["stale_after_days"],
        }
    )


if __name__ == "__main__":
    output = HERE / "data" / "tiles.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(build_payload(), allow_nan=False) + "\n")
    print(f"Wrote {output}")
