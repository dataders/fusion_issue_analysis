"""Build the static BoardBench report index and every dated report snapshot.

Run from the repository root with ``uv run python dashboard/boardbench/build.py``.
The scored YAML cards are inputs; this command makes their HTML and Markdown
views reproducible during CI without making paid judge calls.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUTS = ("results.html", "results.md", "rules.html", "rules.md")


def main() -> None:
    snapshots = sorted(
        (path for path in ROOT.iterdir() if path.is_dir() and (path / "render_results.py").is_file()),
        key=lambda path: path.name,
        reverse=True,
    )
    if not snapshots:
        raise RuntimeError("No dated BoardBench snapshots found")

    for snapshot in snapshots:
        date.fromisoformat(snapshot.name)
        subprocess.run([sys.executable, str(snapshot / "render_results.py")], check=True)
        missing = [name for name in OUTPUTS if not (snapshot / name).is_file()]
        if missing:
            raise RuntimeError(f"{snapshot.name}: missing report files: {missing}")

    latest = snapshots[0]
    links = "".join(
        f"<li><strong>{escape(snapshot.name)}</strong> — "
        f'<a href="{escape(snapshot.name)}/results.html">Results</a> · '
        f'<a href="{escape(snapshot.name)}/rules.html">Rules</a></li>'
        for snapshot in snapshots
    )
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>BoardBench · dashboard bakeoff</title>
<style>
:root{{color-scheme:light dark;font:16px/1.5 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
--bg:#f6f7f9;--surface:#fff;--text:#1c2936;--muted:#5b6876;--line:#d9dfe5;--accent:#205d9f}}
@media(prefers-color-scheme:dark){{:root{{--bg:#101720;--surface:#192431;--text:#e7edf3;--muted:#aab7c3;--line:#364657;--accent:#8fc3fb}}}}
body{{margin:0;background:var(--bg);color:var(--text)}}main{{max-width:820px;margin:8vh auto;padding:24px}}
section{{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:28px}}
h1{{font-size:clamp(2rem,5vw,3rem);letter-spacing:-.04em;line-height:1.1;margin:.2em 0}}
.eyebrow{{color:var(--accent);font-weight:800;text-transform:uppercase;letter-spacing:.1em;font-size:.78rem}}
p{{color:var(--muted)}}a{{color:var(--accent)}}.primary{{display:inline-block;background:var(--accent);color:var(--surface);padding:10px 15px;border-radius:8px;text-decoration:none;font-weight:750;margin:8px 8px 8px 0}}
li{{padding:5px 0}}
</style></head><body><main><section>
<div class="eyebrow">Dashboard bakeoff</div><h1>BoardBench</h1>
<p>Browse scored dashboard captures and the exact rubric behind them. Results describe their capture date; dashboard deployments do not rejudge the pages.</p>
<p><a class="primary" href="{escape(latest.name)}/results.html">Latest results</a>
<a class="primary" href="{escape(latest.name)}/rules.html">Browse rules</a></p>
<h2>Available evaluations</h2><ul>{links}</ul>
<p><a href="../index.html">← Dashboard bakeoff</a></p>
</section></main></body></html>"""
    (ROOT / "index.html").write_text(html)
    print(f"BoardBench index: {len(snapshots)} snapshot(s), latest {latest.name}")


if __name__ == "__main__":
    main()
