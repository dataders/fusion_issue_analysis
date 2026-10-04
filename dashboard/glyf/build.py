# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "duckdb>=1.5.2",
#     "glyf-core>=0.18",
#     "pandas>=2",
#     "pyyaml>=6",
# ]
# ///
"""Glyf dashboard: build the dashboard/tiles.yml tiles into a static site.

Glyf resolves `{{ ref('model') }}` through a dbt manifest and runs the chart SQL
against a DuckDB file. CI has no dbt build, so this script writes the two inputs
from the dashboard models instead:

    target/manifest.json   one model node per tile model in tiles.yml
    target/glyf.duckdb     a copy of those models from FUSION_DB / MotherDuck / local DuckDB

then runs `glyf build`, which writes the site to dashboard/glyf/site/.

Usage:
    uv run dashboard/glyf/build.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import tiles  # noqa: E402

TARGET = HERE / "target"


def tile_models() -> list[str]:
    models = [tiles.MANIFEST["meta"]["model"]]
    models += [t["model"] for s in tiles.sections() for t in s["tiles"]]
    return list(dict.fromkeys(models))


def snapshot(models: list[str]) -> None:
    """Copy each tile model into target/glyf.duckdb (the file Glyf looks for)."""
    TARGET.mkdir(exist_ok=True)
    db_file = TARGET / f"{HERE.name}.duckdb"
    db_file.unlink(missing_ok=True)
    source = duckdb.connect(tiles.db_path(), read_only=True)
    out = duckdb.connect(str(db_file))
    for model in models:
        out.register("_rows", source.execute(f"select * from {model}").arrow().read_all())
        out.execute(f'create table "{model}" as select * from _rows')
        out.unregister("_rows")
    out.close()


def write_manifest(models: list[str]) -> None:
    nodes = {
        f"model.glyf.{m}": {
            "unique_id": f"model.glyf.{m}",
            "name": m,
            "resource_type": "model",
            "package_name": "glyf",
            "relation_name": f'"main"."{m}"',
            "original_file_path": f"models/dashboard/{m}.sql",
            "columns": {},
            "depends_on": {"nodes": []},
        }
        for m in models
    }
    manifest = {"metadata": {"dbt_schema_version": "https://schemas.getdbt.com/dbt/manifest/v12.json"},
                "nodes": nodes, "sources": {}}
    (TARGET / "manifest.json").write_text(json.dumps(manifest, indent=2))


def main() -> None:
    print(f"[glyf] using {tiles.db_path()}")
    models = tile_models()
    snapshot(models)
    write_manifest(models)
    subprocess.run([sys.executable, "-m", "glyf", "build", "--project-dir", str(HERE)], check=True)


if __name__ == "__main__":
    main()
