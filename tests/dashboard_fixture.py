"""Build a tiny DuckDB with one dummy table per dashboard model.

Lets the dashboard exports run in tests and CI without MotherDuck or a dbt build.
Columns come from transform/models/dashboard/_schema.yml; values are placeholders.
"""

from pathlib import Path

import duckdb
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CATS = ["feature", "bug", "task", "other"]
EXTRA_COLUMNS = {"dashboard_meta": ["source_repo", "source_label", "issue_count"]}  # in the .sql, not the schema
ONE_ROW = {"dashboard_meta", "headline_kpis"}


def _value(col: str, i: int, cat: str):
    fixed = {
        "as_of_date": "2026-10-01",
        "days_stale": 1,
        "source_repo": "dbt-labs/dbt-core",
        "source_label": "engine:v2",
        "issue_category": cat,
        "age_bucket": ["0-7d", "8-30d", "31-90d", "90d+"][i % 4],
        "age_bucket_order": i % 4,
        "status_order": i % 4,
        "triage_status": ["needs_triage", "triaged"][i % 2],
        "status_label": ["Needs triage", "Triaged"][i % 2],
        "area": ["parser", "cli", "docs"][i % 3],
        "adapter": ["snowflake", "duckdb", "bigquery"][i % 3],
        "assignee_login": ["ann", "bob", "cy"][i % 3],
        "areas": "parser",
        "issue_url": f"https://github.com/o/r/issues/{i}",
        "week": f"2026-0{1 + i % 9}-01",
    }
    if col in fixed:
        return fixed[col]
    if col in ("title", "milestone_title"):
        return f"Title {i}"
    if col.startswith("is_"):
        return i % 2 == 0
    if col.startswith("pct"):
        return 40.0 + i
    return float(i + 1)


def _sql_type(value) -> str:
    if isinstance(value, bool):
        return "BOOLEAN"
    if isinstance(value, float):
        return "DOUBLE"
    return "BIGINT" if isinstance(value, int) else "VARCHAR"


def build(path: Path) -> Path:
    schema = yaml.safe_load((REPO_ROOT / "transform/models/dashboard/_schema.yml").read_text())
    con = duckdb.connect(str(path))
    for model in schema["models"]:
        cols = [c["name"] for c in model.get("columns", [])] + EXTRA_COLUMNS.get(model["name"], [])
        if not cols:
            continue
        rows = [[_value(c, i, CATS[i % 4]) for c in cols] for i in range(1 if model["name"] in ONE_ROW else 8)]
        ddl = ", ".join(f"{c} {_sql_type(v)}" for c, v in zip(cols, rows[0], strict=True))
        con.execute(f"create table {model['name']} ({ddl})")
        con.executemany(f"insert into {model['name']} values ({','.join('?' * len(cols))})", rows)
    con.close()
    return path
