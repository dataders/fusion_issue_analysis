#!/usr/bin/env python
"""Bake the tile contract + every tile model into one self-contained HTML file.

The page (template.html) renders dashboard/tiles.yml generically with Chart.js,
so it gets every tile by construction. Only select and sort happen here; every
metric comes from transform/models/dashboard/. Reuses the mcp-app snapshot
(build_payload) so both frameworks bake identical rows.

Run: uv run python dashboard/chartjs/build.py   ->  dashboard/chartjs/index.html
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "mcp-app"))
from build_data import build_payload  # noqa: E402

OUT_PATH = HERE / "index.html"


def main() -> None:
    payload = json.dumps(build_payload(), separators=(",", ":")).replace("</", "<\\/")
    OUT_PATH.write_text((HERE / "template.html").read_text().replace("__PAYLOAD__", payload))
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
