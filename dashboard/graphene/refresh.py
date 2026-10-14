"""Refresh the genuine Graphene standalone export from local dbt models.

Graphene's CLI can only export Cloud reports. The checked-in export already
contains its renderer, compiled page, and SQL for each result. Re-run that SQL
and replace the embedded result cache; never render a substitute dashboard.

Run after the local dbt build: uv run python dashboard/graphene/refresh.py
"""

from __future__ import annotations

import argparse
import json
import math
import re
import time
from contextlib import chdir
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_HTML = Path(__file__).with_name("index.html")
MARKER = re.compile(r"window\.\$GRAPHENE_STANDALONE\s*=\s*")
OLD_CALLOUT = (
    '<div class="callout"><strong><!></strong> open issues are unassigned. '
    'The chart below shows the 15 busiest assignees.</div>'
)
EMPTY_CALLOUT = '<div hidden><strong><!></strong></div>'
OLD_NOTE = (
    "This is a static HTML export of a Graphene page. For live pages, "
    "use Graphene's local dev server, or Graphene Cloud."
)


def extract_payload(html: str) -> tuple[dict, int, int]:
    matches = list(MARKER.finditer(html))
    if len(matches) != 1:
        raise ValueError("Expected exactly one Graphene standalone payload")
    start = matches[0].end()
    payload, length = json.JSONDecoder().raw_decode(html[start:])
    if not isinstance(payload.get("code"), str) or not isinstance(payload.get("data"), dict):
        raise ValueError("Graphene payload is missing compiled page or query results")
    return payload, start, start + length


def json_value(value):
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        value = float(value)
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Non-finite number in Graphene result")
    return value


def refresh(source: Path, output: Path) -> int:
    html = output.read_text()
    payload, start, end = extract_payload(html)
    run_at = int(time.time() * 1000)
    source = source.resolve()
    with chdir(ROOT / "transform"), duckdb.connect(str(source), read_only=True) as connection:
        meta = connection.execute("select as_of_date from dashboard_meta").fetchone()
        if not meta or meta[0] is None:
            raise ValueError("Local dashboard metadata is missing its data date")
        for result in payload["data"].values():
            sql = result["sql"]
            statements = connection.extract_statements(sql)
            if len(statements) != 1 or statements[0].type != duckdb.StatementType.SELECT:
                raise ValueError("Graphene export contains a non-SELECT query")
            cursor = connection.execute(sql)
            columns = [column[0] for column in cursor.description]
            if columns != [field["name"] for field in result["fields"]]:
                raise ValueError(f"Graphene result schema changed: {columns}")
            result["rows"] = [
                dict(zip(columns, (json_value(value) for value in row), strict=True))
                for row in cursor.fetchall()
            ]
            result["sql"] = sql
            result["runAt"] = run_at

    code = payload["code"]
    # Keep the compiled Svelte node skeleton and sibling offsets intact while
    # removing the obsolete callout and its Value component. The dormant query
    # is retained so the original result-cache keys still match the runtime.
    code = code.replace(OLD_CALLOUT, EMPTY_CALLOUT)
    code = code.replace("Value(node_42, { data: 'unassigned', column: 'total' });", "")
    if "open issues are unassigned" in code or "data: 'unassigned'" in code:
        raise ValueError("Graphene's old unassigned callout could not be removed")
    note = f"Static Graphene export · Data as of {meta[0]} · Refreshed from local dbt models."
    code = code.replace(OLD_NOTE, note)
    code = re.sub(r"Static Graphene export · Data as of [^<`]*? · Refreshed from local dbt models\.", note, code)
    payload["code"] = code
    serialized = json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    # Data can include issue titles containing HTML. Never let a title terminate
    # the script element that holds this JSON object.
    serialized = serialized.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    updated = html[:start] + serialized + html[end:]
    extract_payload(updated)
    output.write_text(updated)
    return len(payload["data"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", type=Path, default=ROOT / "data/fusion_issues.duckdb")
    parser.add_argument("--output", type=Path, default=DEFAULT_HTML)
    args = parser.parse_args()
    count = refresh(args.source, args.output)
    print(f"Refreshed {count} Graphene queries in {args.output}")


if __name__ == "__main__":
    main()
