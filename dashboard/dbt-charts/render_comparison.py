"""Render width-specific layouts with the real dbt Charts renderer.

Only presentation changes: all chart definitions and dbt queries are inherited
from the canonical board. dbt Charts emits fixed SVG, so these are native layout
variants, not a claim that the renderer supports live browser layout.
"""

from __future__ import annotations

import copy
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def comparison_rows(rows: list, kpi_columns: int, chart_columns: int) -> list:
    result = copy.deepcopy(rows)
    # Keep the board's authored sections and order; regroup only their columns.
    kpis = [chart for row in result[1]["rows"] for chart in row["cols"]]
    result[1]["rows"] = [{"cols": kpis[index : index + kpi_columns]} for index in range(0, len(kpis), kpi_columns)]

    def stack(node):
        if not isinstance(node, dict):
            return
        if chart_columns == 1 and "cols" in node:
            node["rows"] = node.pop("cols")
        for child in node.get("rows", []):
            stack(child)

    for section in result[2:]:
        stack(section)
    return result


def render(output: Path, layouts: list[str] | None = None) -> None:
    source = ROOT / "transform/charts/fusion-issue-health.yml"
    canonical = yaml.safe_load(source.read_text())
    with tempfile.TemporaryDirectory(prefix=".dct-layouts-", dir=ROOT / "transform") as temp:
        for name, width, kpis, charts in (
            ("wide", 1000, 3, 2),
            ("narrow", 600, 2, 1),
            ("mobile", 360, 1, 1),
        ):
            if layouts and name not in layouts:
                continue
            for theme in ("light", "dark"):
                board = Path(temp) / f"{name}-{theme}.yml"
                # dct extends concatenates row lists, so copy the canonical
                # definitions and replace only layout instead of inheriting rows.
                variant = copy.deepcopy(canonical)
                if theme == "dark":
                    variant["extends"] = ["neon"]
                variant.setdefault("style", {})["frame"] = {"width": width, "margin": 24}
                variant["rows"] = comparison_rows(canonical["rows"], kpis, charts)
                board.write_text(yaml.safe_dump(variant, sort_keys=False))
                target = output / f"fusion-issue-health-{theme}-{name}.html"
                subprocess.run(
                    ["uv", "run", "dct", "render", str(board), "--format", "html", "--output", str(target)],
                    cwd=ROOT / "transform",
                    check=True,
                )
                html = target.read_text().replace("<head>", f'<head><meta name="color-scheme" content="only {theme}">')
                target.write_text(html.replace("</body>", '<script src="comparison.js"></script></body>'))


if __name__ == "__main__":
    render(Path(sys.argv[1]).resolve(), sys.argv[2:])
