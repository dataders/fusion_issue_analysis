#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["duckdb>=1"]
# ///
"""Observable Framework data loader — outputs summary.json to stdout.

Observable runs this at build time and bundles the output as
src/data/summary.json for FileAttachment("data/summary.json").json().

Connects to MotherDuck when MOTHERDUCK_TOKEN is set, otherwise local DuckDB.
"""

import json
import os
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[4]
QUERIES = Path(__file__).resolve().parents[3] / "queries"

if os.environ.get("MOTHERDUCK_TOKEN"):
    DB_PATH = "md:fusion_issues"
    con = duckdb.connect(DB_PATH)
else:
    DB_PATH = str(ROOT / "data" / "fusion_issues.duckdb")
    con = duckdb.connect(DB_PATH, read_only=True)
    con.execute(f"SET file_search_path = '{ROOT / 'transform'}'")


def q(name: str) -> list[dict]:
    sql = (QUERIES / f"{name}.sql").read_text()
    return json.loads(con.execute(sql).fetchdf().to_json(orient="records"))


data = {
    "summary": q("summary")[0],
    "flow": q("weekly_flow"),
    "velocity": q("velocity"),
    "triage": q("triage")[0],
    "top_issues": q("community_priorities"),
}

json.dump(data, sys.stdout)
