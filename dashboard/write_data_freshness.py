"""Write source-data freshness metadata for the static dashboard shell."""

from __future__ import annotations

import argparse
import json
import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "dashboard" / "data_freshness.json"


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


def _db_path(source: str) -> str:
    if source == "motherduck":
        return os.environ.get("FUSION_DB", "md:fusion_issues")
    return os.environ.get("FUSION_DB", str(PROJECT_ROOT / "data" / "fusion_issues.duckdb"))


def _detect_source(source: str) -> str:
    if source != "auto":
        return source
    db_path = os.environ.get("FUSION_DB", "")
    if db_path.startswith("md:") or os.environ.get("MOTHERDUCK_TOKEN"):
        return "motherduck"
    return "local"


def _motherduck_metadata() -> dict[str, Any]:
    with duckdb.connect(_db_path("motherduck")) as con:
        row = con.sql(
            """
            select
                max(l.inserted_at) as latest_load_at,
                max(i.updated_at) as latest_source_updated_at,
                count(*) as issue_rows,
                count(distinct i._dlt_load_id) as issue_load_count
            from raw_github.issues i
            left join raw_github._dlt_loads l
                on i._dlt_load_id = l.load_id
            where coalesce(l.status, 0) = 0
            """
        ).fetchone()
    return {
        "source": "motherduck",
        "latest_load_at": _isoformat(row[0]),
        "latest_source_updated_at": _isoformat(row[1]),
        "issue_rows": row[2],
        "issue_load_count": row[3],
    }


def _local_metadata() -> dict[str, Any]:
    with duckdb.connect() as con:
        row = con.sql(
            f"""
            select
                (
                    select max(inserted_at)
                    from read_json_auto('{PROJECT_ROOT}/data/raw/fusion_issues/_dlt_loads/*.jsonl')
                    where status = 0
                ) as latest_load_at,
                (
                    select max(updated_at)
                    from read_parquet('{PROJECT_ROOT}/data/raw/fusion_issues/issues/*.parquet')
                ) as latest_source_updated_at,
                (
                    select count(*)
                    from read_parquet('{PROJECT_ROOT}/data/raw/fusion_issues/issues/*.parquet')
                ) as issue_rows
            """
        ).fetchone()
    return {
        "source": "local",
        "latest_load_at": _isoformat(row[0]),
        "latest_source_updated_at": _isoformat(row[1]),
        "issue_rows": row[2],
        "issue_load_count": None,
    }


def build_metadata(source: str = "auto") -> dict[str, Any]:
    detected = _detect_source(source)
    metadata = _motherduck_metadata() if detected == "motherduck" else _local_metadata()
    metadata["generated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path to write the dashboard metadata JSON.",
    )
    parser.add_argument(
        "--source",
        choices=("auto", "motherduck", "local"),
        default="auto",
        help="Source to query for freshness metadata.",
    )
    args = parser.parse_args()

    metadata = build_metadata(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
