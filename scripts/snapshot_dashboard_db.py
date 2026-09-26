"""Snapshot every dashboard model into one local DuckDB file for a build.

Every framework in a build reads this file (via FUSION_DB), not MotherDuck
directly. Why:
- The extract's dbt build swaps each table in place; reading MotherDuck while
  that runs fails with "table does not exist". The copy takes seconds and is
  retried, so a build can no longer land in the swap window.
- Every tab in one build shows data from the same moment.
- `dct render` opens DuckDB read-only with external access off, so it needs
  base tables in a standalone file anyway.

Frameworks may only read dashboard models (tests/test_tiles_contract.py), so
the snapshot is exactly transform/models/dashboard/*.sql.
"""

from __future__ import annotations

import argparse
import os
import tempfile
import time
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "transform" / "models" / "dashboard"
DEFAULT_OUTPUT = ROOT / "data" / "serve" / "fusion_issues.duckdb"
ATTEMPTS = 6
RETRY_SECONDS = 20


def dashboard_models() -> list[str]:
    return sorted(p.stem for p in MODELS_DIR.glob("*.sql"))


def copy_models(source: str, target: Path, models: list[str]) -> None:
    # Dev staging views hold parquet paths relative to transform/.
    os.chdir(ROOT / "transform")
    # Read local sources read-only so a running dashboard doesn't block the build.
    read_only = not source.startswith("md:")
    with duckdb.connect(source, read_only=read_only) as connection:
        connection.execute(f"ATTACH '{target.as_posix()}' AS serve (READ_WRITE)")
        connection.execute("CREATE SCHEMA IF NOT EXISTS serve.main")
        for model in models:
            connection.execute(
                f'CREATE OR REPLACE TABLE serve.main."{model}" AS SELECT * FROM main."{model}"'
            )
        # A connection whose primary attachment is a MotherDuck (md:) session
        # doesn't reliably checkpoint a secondary local ATTACH on close, so
        # writes can be left stranded in serve's WAL and lost once the file
        # is moved. Force the flush before closing.
        connection.execute("CHECKPOINT serve")


def build(source: str, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    models = dashboard_models()
    for attempt in range(1, ATTEMPTS + 1):
        with tempfile.TemporaryDirectory(prefix="snapshot-", dir=output.parent) as tmpdir:
            next_db = Path(tmpdir) / output.name
            try:
                copy_models(source, next_db, models)
            except duckdb.CatalogException as exc:
                # A table is mid-swap in an extract's dbt build; it reappears in seconds.
                if attempt == ATTEMPTS:
                    raise
                print(f"Snapshot attempt {attempt} hit a table mid-rebuild ({exc}); retrying in {RETRY_SECONDS}s")
                time.sleep(RETRY_SECONDS)
                continue
            os.replace(next_db, output)
            break
    print(f"Snapshot {output}: {len(models)} dashboard models from {source}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--source",
        default=os.environ.get("FUSION_DB", str(ROOT / "data" / "fusion_issues.duckdb")),
        help="DuckDB path or md:fusion_issues (needs MOTHERDUCK_TOKEN).",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build(args.source, args.output)


if __name__ == "__main__":
    main()
