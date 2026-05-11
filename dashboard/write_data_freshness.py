"""Write dashboard freshness from dlt's built-in load history table."""

from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import duckdb


OUTPUT = Path(__file__).with_name("data_freshness.json")


def _isoformat(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        value = datetime.combine(value, datetime.min.time(), tzinfo=timezone.utc)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return str(value)


def _latest_dlt_load_at() -> str | None:
    if not os.environ.get("MOTHERDUCK_TOKEN"):
        return None

    db_path = os.environ.get("FUSION_DB", "md:fusion_issues")
    with duckdb.connect(db_path) as con:
        latest_load_at = con.sql(
            """
            select max(inserted_at)
            from raw_github._dlt_loads
            where status = 0
            """
        ).fetchone()[0]
    return _isoformat(latest_load_at)


def main() -> None:
    latest_load_at = _latest_dlt_load_at()
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "latest_load_at": latest_load_at,
        "source": "raw_github._dlt_loads" if latest_load_at else "unavailable",
    }
    OUTPUT.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
