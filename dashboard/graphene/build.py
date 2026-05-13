import json
import os
from datetime import date, datetime
from decimal import Decimal
from html import escape
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[2]
GRAPHENE_DIR = ROOT / "dashboard" / "graphene"
TARGET_DB = GRAPHENE_DIR / "fusion_graphene.duckdb"
OUTPUT_HTML = GRAPHENE_DIR / "index.html"


SNAPSHOT_SQL = """
CREATE TABLE summary_kpis AS
SELECT
  opened_4w,
  closed_4w,
  open_issues,
  total_issues,
  rolling_median_close_days,
  pct_responded_48h,
  stale_count
FROM fusion_issues.main.summary_kpis;

CREATE TABLE triage_health AS
SELECT
  total_open,
  pct_labeled,
  pct_assigned,
  pct_milestoned,
  pct_typed,
  unlabeled_count,
  unassigned_count
FROM fusion_issues.main.triage_health;

CREATE TABLE weekly_flow AS
SELECT
  CAST(week AS DATE) AS week,
  opened,
  closed
FROM fusion_issues.main.weekly_flow
ORDER BY week;

CREATE TABLE open_vs_closed_by_category AS
SELECT
  issue_category,
  state,
  n
FROM fusion_issues.main.open_vs_closed_by_category
ORDER BY issue_category, state;

CREATE TABLE response_pctiles AS
SELECT
  CAST(week AS DATE) AS week,
  p25,
  p50,
  p75
FROM fusion_issues.main.response_pctiles
ORDER BY week;

CREATE TABLE community_priorities AS
SELECT
  issue_number,
  title,
  issue_category,
  reactions_total_count,
  comments_total_count,
  age_days,
  'https://github.com/dbt-labs/dbt-fusion/issues/' || CAST(issue_number AS VARCHAR) AS url
FROM fusion_issues.main.community_priorities
ORDER BY reactions_total_count DESC, comments_total_count DESC;
"""


TABLES = (
    "summary_kpis",
    "weekly_flow",
    "open_vs_closed_by_category",
    "response_pctiles",
    "triage_health",
    "community_priorities",
)


def default_source_root() -> Path:
    if ROOT.parent.name == ".worktrees":
        return ROOT.parents[1]
    return ROOT


def duckdb_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def source_root() -> Path:
    return Path(os.environ.get("FUSION_PROJECT_ROOT", default_source_root()))


def source_database() -> str:
    root = source_root()
    source_db = os.environ.get("FUSION_DB", str(root / "data" / "fusion_issues.duckdb"))
    if not source_db.startswith("md:") and not Path(source_db).exists():
        raise SystemExit(
            "Missing source database: "
            f"{source_db}\nSet FUSION_DB=md:fusion_issues or build the local DuckDB database first."
        )
    return source_db


def build_snapshot() -> None:
    source_db = source_database()
    TARGET_DB.unlink(missing_ok=True)
    TARGET_DB.with_suffix(TARGET_DB.suffix + ".wal").unlink(missing_ok=True)

    with duckdb.connect(str(TARGET_DB)) as conn:
        conn.execute(f"SET file_search_path = {duckdb_literal(str(source_root() / 'transform'))}")
        conn.execute(f"ATTACH {duckdb_literal(source_db)} AS fusion_issues (READ_ONLY)")
        conn.execute(SNAPSHOT_SQL)
        conn.execute("DETACH fusion_issues")


def normalize_value(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        as_int = int(value)
        return as_int if value == as_int else float(value)
    return value


def fetch_rows(conn: duckdb.DuckDBPyConnection, table: str) -> list[dict]:
    result = conn.execute(f"SELECT * FROM {table}")
    columns = [description[0] for description in result.description]
    return [
        {column: normalize_value(value) for column, value in zip(columns, row)}
        for row in result.fetchall()
    ]


def load_snapshot_data() -> dict[str, list[dict]]:
    with duckdb.connect(str(TARGET_DB), read_only=True) as conn:
        return {table: fetch_rows(conn, table) for table in TABLES}


def json_script(data: dict[str, list[dict]]) -> str:
    payload = json.dumps(data, ensure_ascii=True).replace("</", "<\\/")
    return f"<script>window.__GRAPHENE_DATA__ = {payload};</script>"


def render_static_page(data: dict[str, list[dict]]) -> str:
    kpis = data.get("summary_kpis", [{}])[0]
    title = "Graphene"
    subtitle = "Fusion Issue Health"
    open_issues = escape(str(kpis.get("open_issues", "")))
    opened_4w = escape(str(kpis.get("opened_4w", "")))
    closed_4w = escape(str(kpis.get("closed_4w", "")))
    responded = escape(str(kpis.get("pct_responded_48h", "")))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} - {subtitle}</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #111827;
      --muted: #64748b;
      --line: #d7dde5;
      --panel: #f8fafc;
      --orange: #cb7a55;
      --green: #86a98f;
      --purple: #8973a8;
      --blue: #5b84a5;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: #fff;
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 32px 28px 44px;
    }}
    header {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 20px;
      align-items: start;
      margin-bottom: 26px;
    }}
    h1 {{
      margin: 0;
      font-size: 30px;
      line-height: 1.15;
      letter-spacing: 0;
    }}
    h2 {{
      margin: 30px 0 12px;
      font-size: 16px;
      line-height: 1.3;
      letter-spacing: 0;
    }}
    p {{
      margin: 8px 0 0;
      color: var(--muted);
      line-height: 1.45;
    }}
    .note {{
      max-width: 460px;
      padding: 12px 14px;
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 6px;
      font-size: 13px;
      color: #334155;
    }}
    .note a {{ color: #1f5f88; }}
    .kpis {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 18px;
      margin-bottom: 24px;
    }}
    .kpi {{
      border-top: 1px solid var(--line);
      padding-top: 12px;
    }}
    .kpi-label {{
      color: #8b95a5;
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }}
    .kpi-value {{
      margin-top: 4px;
      font-size: 28px;
      font-weight: 750;
      line-height: 1;
    }}
    .toolbar {{
      margin: 24px 0 4px;
      display: flex;
      align-items: end;
      gap: 16px;
    }}
    label {{
      display: grid;
      gap: 6px;
      font-size: 12px;
      font-weight: 650;
      color: #334155;
    }}
    select {{
      width: 220px;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      padding: 9px 36px 9px 11px;
      background: #fff;
      color: var(--ink);
      font: inherit;
    }}
    .chart {{
      width: 100%;
      min-height: 260px;
      border-bottom: 1px solid #e5e7eb;
    }}
    .legend {{
      display: flex;
      gap: 12px;
      align-items: center;
      margin: 0 0 6px;
      color: #475569;
      font-size: 13px;
    }}
    .legend span::before {{
      content: "";
      display: inline-block;
      width: 8px;
      height: 8px;
      margin-right: 5px;
      border-radius: 50%;
      background: currentColor;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    th, td {{
      padding: 9px 10px;
      border-bottom: 1px solid #e5e7eb;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      color: #475569;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    td.num, th.num {{ text-align: right; }}
    a {{ color: #1f5f88; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    @media (max-width: 800px) {{
      main {{ padding: 22px 16px 34px; }}
      header {{ grid-template-columns: 1fr; }}
      .kpis {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      select {{ width: 100%; }}
      .toolbar {{ display: block; }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>
      <p class="note">
        This tab uses the public Graphene CLI, <code>graphene/index.md</code>, and GSQL model files.
        Graphene does not currently ship a static Pages export, so this production tab renders a static Pages export from the same modeled dashboard tables.
      </p>
    </header>

    <section class="kpis" aria-label="Summary metrics">
      <div class="kpi"><div class="kpi-label">Open issues</div><div class="kpi-value">{open_issues}</div></div>
      <div class="kpi"><div class="kpi-label">Opened, 4w</div><div class="kpi-value">{opened_4w}</div></div>
      <div class="kpi"><div class="kpi-label">Closed, 4w</div><div class="kpi-value">{closed_4w}</div></div>
      <div class="kpi"><div class="kpi-label">Responded &lt;=48h</div><div class="kpi-value">{responded}%</div></div>
    </section>

    <h2>Weekly issue flow</h2>
    <div class="legend"><span style="color: var(--orange)">opened</span><span style="color: var(--green)">closed</span></div>
    <svg id="weekly-flow" class="chart" role="img" aria-label="Weekly issue flow"></svg>

    <div class="toolbar">
      <label>Issue category<select id="category"></select></label>
    </div>
    <h2>Selected category open vs. closed</h2>
    <svg id="selected-category" class="chart" role="img" aria-label="Selected category open vs closed"></svg>

    <h2>All categories overview</h2>
    <div class="legend"><span style="color: var(--orange)">closed</span><span style="color: var(--green)">open</span></div>
    <svg id="all-categories" class="chart" role="img" aria-label="All categories open vs closed"></svg>

    <h2>Hours to first response</h2>
    <div class="legend"><span style="color: var(--orange)">p25</span><span style="color: var(--green)">p50</span><span style="color: var(--purple)">p75</span></div>
    <svg id="response" class="chart" role="img" aria-label="Hours to first response"></svg>

    <section class="kpis" aria-label="Triage metrics" id="triage-kpis"></section>

    <h2>Community-prioritized open issues</h2>
    <div id="priorities"></div>
  </main>
  {json_script(data)}
  <script>
    const data = window.__GRAPHENE_DATA__;
    const colors = {{ opened: '#cb7a55', closed: '#86a98f', p25: '#cb7a55', p50: '#86a98f', p75: '#8973a8', blue: '#5b84a5' }};
    const fmt = value => Number.isFinite(Number(value)) ? Number(value).toLocaleString() : String(value ?? '');

    function clear(node) {{
      while (node.firstChild) node.removeChild(node.firstChild);
    }}

    function svgEl(name, attrs = {{}}) {{
      const el = document.createElementNS('http://www.w3.org/2000/svg', name);
      for (const [key, value] of Object.entries(attrs)) el.setAttribute(key, value);
      return el;
    }}

    function dimensions(svg) {{
      const width = svg.clientWidth || 900;
      const height = 260;
      svg.setAttribute('viewBox', `0 0 ${{width}} ${{height}}`);
      return {{ width, height, left: 38, right: 16, top: 14, bottom: 28 }};
    }}

    function scales(rows, keys, box) {{
      const max = Math.max(1, ...rows.flatMap(row => keys.map(key => Number(row[key]) || 0)));
      const innerWidth = box.width - box.left - box.right;
      const innerHeight = box.height - box.top - box.bottom;
      return {{
        x: index => box.left + (rows.length <= 1 ? innerWidth / 2 : index * innerWidth / (rows.length - 1)),
        y: value => box.top + innerHeight - (Number(value) || 0) * innerHeight / max,
        max,
      }};
    }}

    function drawGrid(svg, box, max) {{
      const innerHeight = box.height - box.top - box.bottom;
      for (let i = 0; i <= 4; i++) {{
        const y = box.top + innerHeight * i / 4;
        svg.appendChild(svgEl('line', {{ x1: box.left, x2: box.width - box.right, y1: y, y2: y, stroke: '#e5e7eb' }}));
        const label = Math.round(max * (4 - i) / 4);
        const text = svgEl('text', {{ x: box.left - 8, y: y + 4, 'text-anchor': 'end', fill: '#94a3b8', 'font-size': '11' }});
        text.textContent = fmt(label);
        svg.appendChild(text);
      }}
    }}

    function lineChart(id, rows, keys, palette) {{
      const svg = document.getElementById(id);
      clear(svg);
      const box = dimensions(svg);
      const scale = scales(rows, keys, box);
      drawGrid(svg, box, scale.max);
      keys.forEach((key, idx) => {{
        const points = rows.map((row, index) => `${{scale.x(index)}},${{scale.y(row[key])}}`).join(' ');
        svg.appendChild(svgEl('polyline', {{
          points,
          fill: 'none',
          stroke: palette[idx],
          'stroke-width': 2,
          'stroke-linejoin': 'round',
          'stroke-linecap': 'round',
        }}));
      }});
      rows.filter((_, index) => index % Math.max(1, Math.ceil(rows.length / 6)) === 0).forEach(row => {{
        const idx = rows.indexOf(row);
        const text = svgEl('text', {{ x: scale.x(idx), y: box.height - 8, 'text-anchor': 'middle', fill: '#94a3b8', 'font-size': '11' }});
        text.textContent = String(row.week).slice(0, 7);
        svg.appendChild(text);
      }});
    }}

    function groupedBars(id, rows, groupKey, seriesKey, valueKey) {{
      const svg = document.getElementById(id);
      clear(svg);
      const box = dimensions(svg);
      const groups = [...new Set(rows.map(row => row[groupKey]))];
      const series = [...new Set(rows.map(row => row[seriesKey]))].sort();
      const max = Math.max(1, ...rows.map(row => Number(row[valueKey]) || 0));
      drawGrid(svg, box, max);
      const innerWidth = box.width - box.left - box.right;
      const innerHeight = box.height - box.top - box.bottom;
      const groupWidth = innerWidth / Math.max(1, groups.length);
      const barWidth = Math.max(8, groupWidth / (series.length + 1.4));
      groups.forEach((group, groupIndex) => {{
        series.forEach((state, seriesIndex) => {{
          const row = rows.find(item => item[groupKey] === group && item[seriesKey] === state);
          const value = Number(row?.[valueKey]) || 0;
          const x = box.left + groupIndex * groupWidth + 10 + seriesIndex * barWidth;
          const h = value * innerHeight / max;
          const y = box.top + innerHeight - h;
          svg.appendChild(svgEl('rect', {{
            x,
            y,
            width: barWidth * 0.82,
            height: h,
            rx: 3,
            fill: state === 'OPEN' ? colors.closed : colors.opened,
          }}));
        }});
        const text = svgEl('text', {{ x: box.left + groupIndex * groupWidth + groupWidth / 2, y: box.height - 8, 'text-anchor': 'middle', fill: '#94a3b8', 'font-size': '11' }});
        text.textContent = group;
        svg.appendChild(text);
      }});
    }}

    function selectedBars(category) {{
      const rows = data.open_vs_closed_by_category.filter(row => row.issue_category === category);
      groupedBars('selected-category', rows, 'state', 'state', 'n');
    }}

    function renderCategoryControl() {{
      const select = document.getElementById('category');
      const categories = [...new Set(data.open_vs_closed_by_category.map(row => row.issue_category))].sort();
      categories.forEach(category => {{
        const option = document.createElement('option');
        option.value = category;
        option.textContent = category;
        select.appendChild(option);
      }});
      select.value = categories.includes('bug') ? 'bug' : categories[0];
      select.addEventListener('change', () => selectedBars(select.value));
      selectedBars(select.value);
    }}

    function renderTriage() {{
      const row = data.triage_health[0] || {{}};
      const target = document.getElementById('triage-kpis');
      target.innerHTML = ['pct_labeled', 'pct_typed', 'pct_assigned', 'pct_milestoned'].map(key => {{
        const label = key.replace('pct_', '').replace('milestoned', 'milestoned');
        return `<div class="kpi"><div class="kpi-label">${{label}}</div><div class="kpi-value">${{fmt(row[key])}}%</div></div>`;
      }}).join('');
    }}

    function renderPriorities() {{
      const rows = data.community_priorities || [];
      document.getElementById('priorities').innerHTML = `<table>
        <thead><tr><th>#</th><th>Title</th><th>Type</th><th class="num">Reactions</th><th class="num">Comments</th><th class="num">Age days</th></tr></thead>
        <tbody>${{rows.map(row => `<tr>
          <td><a href="${{row.url}}">${{row.issue_number}}</a></td>
          <td>${{escapeHtml(row.title)}}</td>
          <td>${{row.issue_category}}</td>
          <td class="num">${{fmt(row.reactions_total_count)}}</td>
          <td class="num">${{fmt(row.comments_total_count)}}</td>
          <td class="num">${{fmt(row.age_days)}}</td>
        </tr>`).join('')}}</tbody>
      </table>`;
    }}

    function escapeHtml(value) {{
      const div = document.createElement('div');
      div.textContent = String(value ?? '');
      return div.innerHTML;
    }}

    lineChart('weekly-flow', data.weekly_flow, ['opened', 'closed'], [colors.opened, colors.closed]);
    renderCategoryControl();
    groupedBars('all-categories', data.open_vs_closed_by_category, 'issue_category', 'state', 'n');
    lineChart('response', data.response_pctiles, ['p25', 'p50', 'p75'], [colors.p25, colors.p50, colors.p75]);
    renderTriage();
    renderPriorities();
    window.addEventListener('resize', () => {{
      lineChart('weekly-flow', data.weekly_flow, ['opened', 'closed'], [colors.opened, colors.closed]);
      selectedBars(document.getElementById('category').value);
      groupedBars('all-categories', data.open_vs_closed_by_category, 'issue_category', 'state', 'n');
      lineChart('response', data.response_pctiles, ['p25', 'p50', 'p75'], [colors.p25, colors.p50, colors.p75]);
    }});
  </script>
</body>
</html>
"""


def main() -> None:
    build_snapshot()
    data = load_snapshot_data()
    OUTPUT_HTML.write_text(render_static_page(data))
    print(f"Rendered {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
