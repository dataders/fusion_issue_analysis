#!/usr/bin/env python
"""Snapshot the dashboard tile models into data/issue-health.json.

The widget renders the tile contract (dashboard/tiles.yml) generically, so the
payload carries the manifest plus the rows of every tile model. Only select and
sort here; every metric comes from transform/models/dashboard/.

Models baked (from tiles.yml): dashboard_meta, headline_kpis, backlog_weekly,
weekly_flow, triage_pipeline, response_weekly, triage_queue, open_by_area,
open_by_adapter, epic_progress, top_requested, assignee_workload.
"""

from __future__ import annotations

import json
import math
import sys
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import tiles  # noqa: E402

OUT_PATH = HERE / "data" / "issue-health.json"


def _scalar(value: Any) -> Any:
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):  # numpy scalar
        value = value.item()
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)) or hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _row(row: dict) -> dict:
    out = {k: _scalar(v) for k, v in row.items()}
    if isinstance(out.get("week"), str):
        out["week"] = out["week"][:10]
    return out


def build_payload() -> dict[str, Any]:
    source = tiles.db_path()
    if not source.startswith("md:") and not Path(source).exists():
        raise SystemExit(f"Missing source database: {source}\nRun `make dbt` or set FUSION_DB.")

    meta_model = tiles.MANIFEST["meta"]["model"]
    meta = tiles.one(meta_model)
    models: dict[str, Any] = {meta_model: _row(meta)}
    for section in tiles.sections():
        for tile in section["tiles"]:
            model = tile["model"]
            if tile["form"] == "kpi_row":
                models[model] = _row(tiles.one(model))
            else:  # tiles.yml order_by
                models[model] = [_row(r) for r in tiles.tile_rows(tile["id"])]

    return {
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "manifest": {k: tiles.MANIFEST[k] for k in ("title", "subtitle", "meta", "palette", "sections")},
        "freshness_note": tiles.freshness_note(meta),
        "kpis": tiles.kpis(),  # [{label, value, context}] formatted per tiles.yml
        "is_stale": bool(meta["days_stale"] > tiles.MANIFEST["meta"]["stale_after_days"]),
        "models": models,
    }


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(build_payload(), indent=2) + "\n")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
