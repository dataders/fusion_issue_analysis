from __future__ import annotations

from html import escape
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "fusion-issue-health.dashboard.sql"
CONFIG = HERE / "shaper.json"
TARGET = HERE / "index.html"
DOCS_URL = "https://taleshape.com/shaper/docs/"
REPO_URL = "https://github.com/taleshape-com/shaper"
SCREENSHOT_URL = "https://taleshape.com/images/session_dashboard.png"
SHAPER_ID_RE = re.compile(r"^-- shaperid:[^\s]+$", re.MULTILINE)


def load_source() -> str:
    sql = SOURCE.read_text()
    if not SHAPER_ID_RE.search(sql):
        raise SystemExit(f"{SOURCE} is missing leading -- shaperid comment")
    return sql


def statement_count(sql: str) -> int:
    return sum(1 for part in sql.split(";") if part.strip())


def render_page(sql: str) -> str:
    escaped_sql = escape(sql.strip())
    statements = statement_count(sql)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Shaper | dbt-fusion Issue Analysis</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: #202124;
      background: #f6f7fb;
    }}
    main {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 34px 20px 56px;
    }}
    header {{
      display: grid;
      grid-template-columns: minmax(0, 1.15fr) minmax(280px, 0.85fr);
      gap: 28px;
      align-items: center;
      margin-bottom: 28px;
    }}
    header > *,
    .body-grid > * {{
      min-width: 0;
    }}
    h1 {{
      margin: 0 0 10px;
      font-size: clamp(2.2rem, 5vw, 4rem);
      line-height: 1;
      letter-spacing: 0;
    }}
    h2 {{
      margin: 0 0 12px;
      font-size: 1.05rem;
    }}
    p {{
      margin: 0;
      line-height: 1.55;
      color: #3f4550;
    }}
    a {{ color: #145ea8; }}
    .eyebrow {{
      margin-bottom: 10px;
      color: #6b4b12;
      font-size: 0.8rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    .hero-text {{
      font-size: 1.08rem;
      max-width: 680px;
    }}
    .hero-image {{
      width: 100%;
      min-width: 0;
      max-width: 100%;
      border: 1px solid #d8dde7;
      border-radius: 8px;
      background: #fff;
      box-shadow: 0 18px 44px rgba(33, 41, 54, 0.14);
    }}
    .actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 18px;
    }}
    .actions a {{
      display: inline-flex;
      min-height: 38px;
      align-items: center;
      padding: 0 13px;
      border: 1px solid #b8c4d8;
      border-radius: 6px;
      background: #fff;
      color: #173c66;
      font-weight: 650;
      text-decoration: none;
    }}
    .panel {{
      min-width: 0;
      border: 1px solid #d8dde7;
      border-radius: 8px;
      background: #fff;
      padding: 18px;
      box-shadow: 0 8px 24px rgba(33, 41, 54, 0.07);
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 16px;
    }}
    .metric {{
      min-width: 0;
      min-height: 96px;
      border: 1px solid #dce2ec;
      border-radius: 8px;
      padding: 14px;
      background: #fbfcff;
    }}
    .metric strong {{
      display: block;
      margin-bottom: 7px;
      font-size: 1.05rem;
    }}
    .metric span {{
      display: block;
      color: #667085;
      font-size: 0.9rem;
      line-height: 1.35;
    }}
    .body-grid {{
      display: grid;
      grid-template-columns: minmax(260px, 0.75fr) minmax(0, 1.25fr);
      gap: 16px;
      align-items: start;
    }}
    ul {{
      margin: 0;
      padding-left: 18px;
      color: #3f4550;
      line-height: 1.55;
    }}
    code {{
      padding: 0.08rem 0.28rem;
      border-radius: 4px;
      background: #eef3ff;
      font-size: 0.93em;
    }}
    pre {{
      max-width: 100%;
      max-height: 620px;
      margin: 0;
      overflow: auto;
      border-radius: 6px;
      background: #111827;
      color: #e9edf7;
      padding: 16px;
      font-size: 0.86rem;
      line-height: 1.45;
      white-space: pre;
    }}
    .small {{
      color: #667085;
      font-size: 0.9rem;
    }}
    @media (max-width: 1050px) {{
      header,
      .body-grid {{
        grid-template-columns: 1fr;
      }}
      .grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
    }}
    @media (max-width: 640px) {{
      header,
      .body-grid,
      .grid {{
        grid-template-columns: 1fr;
      }}
      main {{
        padding: 24px 14px 40px;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <div class="eyebrow">Server-backed SQL dashboard</div>
        <h1>Shaper</h1>
        <p class="hero-text">Open source Shaper joins the bakeoff as a SQL-first DuckDB dashboard. This tab ships the tracked <code>.dashboard.sql</code> source and makes the GitHub Pages limitation explicit: Shaper renders from a live Shaper server, not a static export bundle.</p>
        <div class="actions">
          <a href="fusion-issue-health.dashboard.sql">Dashboard SQL</a>
          <a href="shaper.json">shaper.json</a>
          <a href="{DOCS_URL}" target="_blank" rel="noreferrer">Docs</a>
          <a href="{REPO_URL}" target="_blank" rel="noreferrer">Source</a>
        </div>
      </div>
      <img class="hero-image" src="{SCREENSHOT_URL}" alt="Shaper dashboard screenshot">
    </header>

    <section class="grid" aria-label="Shaper tab facts">
      <div class="metric"><strong>{statements}</strong><span>SQL statements in the tracked Shaper dashboard file.</span></div>
      <div class="metric"><strong>DuckDB</strong><span>Runtime engine expected by Shaper and this repo.</span></div>
      <div class="metric"><strong>dbt marts</strong><span>Queries stay on shared dashboard models.</span></div>
      <div class="metric"><strong>No static export</strong><span>GitHub Pages tab is source preview plus run shape.</span></div>
    </section>

    <section class="body-grid">
      <div class="panel">
        <h2>Bakeoff fit</h2>
        <ul>
          <li>Dashboard is authored as <code>fusion-issue-health.dashboard.sql</code>.</li>
          <li>SQL uses Shaper casts such as <code>::SECTION</code>, <code>::DROPDOWN_MULTI</code>, <code>::LINECHART</code>, and <code>::BARCHART_STACKED</code>.</li>
          <li>Shared semantic layer stays in dbt tables like <code>summary_kpis</code>, <code>cumulative_flow</code>, and <code>open_issues_table</code>.</li>
          <li>Local live rendering starts from <code>dashboard/shaper</code> with Shaper pointed at a DuckDB or MotherDuck-backed database.</li>
        </ul>
        <p class="small">Generated from <code>{SOURCE.name}</code> and <code>{CONFIG.name}</code>.</p>
      </div>
      <div class="panel">
        <h2>Dashboard source</h2>
        <pre><code>{escaped_sql}</code></pre>
      </div>
    </section>
  </main>
</body>
</html>
"""


def main() -> None:
    sql = load_source()
    TARGET.write_text(render_page(sql))
    print(f"Rendered {SOURCE} -> {TARGET}")


if __name__ == "__main__":
    main()
