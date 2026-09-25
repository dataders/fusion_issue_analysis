#!/usr/bin/env bash
# Shared helper: emit one dashboard model (or the tile contract) as JSON.
# Usage: _loader.sh <model> [--first-row]
#        _loader.sh --contract          # dashboard/tiles.yml as JSON
# Each model is read as `SELECT * FROM <model> ORDER BY <order_by>`, with
# order_by taken from dashboard/tiles.yml. Metric logic lives in dbt.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"

uv --directory "$REPO_ROOT" run python - "$REPO_ROOT" "$@" <<'PYEOF'
import json, math, os, sys
from pathlib import Path

import duckdb
import yaml

repo_root, target, *flags = sys.argv[1:]
manifest = yaml.safe_load((Path(repo_root) / "dashboard" / "tiles.yml").read_text())

if target == "--contract":
    json.dump(manifest, sys.stdout)
    sys.exit()

order_by = {manifest["meta"]["model"]: None}
for section in manifest["sections"]:
    for tile in section["tiles"]:
        order_by[tile["model"]] = tile.get("order_by")
if target not in order_by:
    sys.exit(f"{target} is not a tile model in dashboard/tiles.yml")

if os.environ.get("FUSION_DB"):
    con = duckdb.connect(os.environ["FUSION_DB"], read_only=True)
elif os.environ.get("MOTHERDUCK_TOKEN"):
    con = duckdb.connect("md:fusion_issues")
else:
    con = duckdb.connect(f"{repo_root}/data/fusion_issues.duckdb", read_only=True)

sql = f"SELECT * FROM {target}" + (f" ORDER BY {order_by[target]}" if order_by[target] else "")
rows = con.execute(sql).fetchdf().to_dict("records")

def clean(value):
    if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "item"):  # numpy scalar
        return value.item()
    return value

rows = [{k: clean(v) for k, v in row.items()} for row in rows]
json.dump(rows[0] if "--first-row" in flags else rows, sys.stdout, allow_nan=False)
PYEOF
