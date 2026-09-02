"""Materialize dbt Charts query models into a standalone DuckDB database."""

from __future__ import annotations

import argparse
import os
import re
import tempfile
from pathlib import Path

import duckdb
import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CHART = ROOT / "transform" / "charts" / "fusion-issue-health.yml"
DEFAULT_OUTPUT = ROOT / "data" / "serve" / "fusion_issues.duckdb"
MODEL_QUERY = re.compile(
    r"^\s*select\s+\*\s+from\s+fusion_issues\.main\.([a-zA-Z_][a-zA-Z0-9_]*)\s*$",
    re.IGNORECASE,
)


def chart_models(chart_path: Path) -> list[str]:
    chart = yaml.safe_load(chart_path.read_text())
    models = []
    for query in chart["queries"].values():
        match = MODEL_QUERY.match(query["sql"])
        if not match:
            raise ValueError(f"dbt Charts query is not a direct dbt model read: {query['sql']}")
        models.append(match.group(1))
    return sorted(set(models))


def build(source: str, output: Path, chart_path: Path = DEFAULT_CHART) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    models = chart_models(chart_path)

    with tempfile.TemporaryDirectory(prefix="dbt-charts-", dir=output.parent) as tmpdir:
        next_db = Path(tmpdir) / "fusion_issues.duckdb"
        # Dev views contain paths relative to transform/, where dbt created them.
        os.chdir(ROOT / "transform")
        with duckdb.connect(source) as connection:
            connection.execute(f"ATTACH '{next_db.as_posix()}' AS serve")
            connection.execute("CREATE SCHEMA IF NOT EXISTS serve.main")
            for model in models:
                connection.execute(
                    f'CREATE TABLE serve.main."{model}" AS '
                    f'SELECT * FROM main."{model}"'
                )
        os.replace(next_db, output)

    print(f"Built {output} with {len(models)} dbt model tables from {source}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        default=os.environ.get("FUSION_DB", str(ROOT / "data" / "fusion_issues.duckdb")),
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--chart", type=Path, default=DEFAULT_CHART)
    args = parser.parse_args()
    build(args.source, args.output, args.chart)


if __name__ == "__main__":
    main()
