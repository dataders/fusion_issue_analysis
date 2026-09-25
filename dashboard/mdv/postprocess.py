"""
Post-process the rendered MDV page for the parts of the tile contract MDV v1
cannot express:

  - series colors: MDV colors series with its theme palette, in order of first
    appearance. Each chart's rows are ordered so series appear in tiles.yml
    palette order; this swaps the theme colors for the palette colors.
  - links: table cells holding an issue URL become "#123" links.

Usage: uv run python dashboard/mdv/postprocess.py dashboard/mdv/index.html
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tiles  # noqa: E402

# MDV "minimal" theme chartPalette (packages/mdv-core/src/themes.ts).
MDV_PALETTE = ["#2d6cdf", "#e0b84a", "#3aa675", "#c64a4a"]

# Series colors per chart tile, in the order generate_data.py emits them.
SERIES = {
    "backlog_weekly": [tiles.color("issue_category", c) for c in tiles.categories("issue_category")],
    "weekly_flow": [tiles.color("flow", "opened"), tiles.color("flow", "closed")],
    "response_weekly": [tiles.MANIFEST["palette"]["single_series"]],
}

URL_CELL = re.compile(r"<td>(https://github\.com/[^<]+/issues/(\d+))</td>")


def recolor(segment: str, colors: list[str]) -> str:
    mapping = dict(zip(MDV_PALETTE, colors))
    return re.sub("|".join(map(re.escape, mapping)), lambda m: mapping[m.group(0)], segment)


def main(path: Path) -> None:
    page = path.read_text()
    titles = {html.escape(tiles.tile(tid)["title"], quote=False): tid for tid in SERIES}
    # Split before each tile heading so a chart is recolored with its own tile's palette.
    parts = re.split(r"(?=<h3)", page)
    for i, part in enumerate(parts):
        m = re.match(r"<h3[^>]*>(.*?)</h3>", part)
        if m and m.group(1) in titles:
            parts[i] = recolor(part, SERIES[titles.pop(m.group(1))])
    if titles:
        raise SystemExit(f"postprocess: chart headings not found: {list(titles)}")
    page = URL_CELL.sub(lambda m: f'<td><a href="{m.group(1)}" target="_blank">#{m.group(2)}</a></td>', "".join(parts))
    path.write_text(page)
    print(f"  postprocessed {path}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
