from __future__ import annotations

from html import escape
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "fusion-issue-health.dashboard.sql"
TARGET = HERE / "index.html"
SHAPER_ID_RE = re.compile(r"^-- shaperid:[^\s]+$", re.MULTILINE)


def load_source() -> str:
    sql = SOURCE.read_text()
    if not SHAPER_ID_RE.search(sql):
        raise SystemExit(f"{SOURCE} is missing leading -- shaperid comment")
    return sql


def statement_count(sql: str) -> int:
    return sum(1 for part in sql.split(";") if part.strip())


def render_page(sql: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Shaper | dbt-fusion Issue Analysis</title>
  <style>
    :root {{
      --shaper-background-color: #fff;
      --shaper-background-color-secondary: #f6f7fb;
      --shaper-dark-mode-background-color: #3a3b48;
      --shaper-dark-mode-background-color-secondary: #424453;
      --shaper-dark-mode-background-color-alternate: #585a72;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: #202124;
      background: #fff;
    }}
    main {{
      max-width: 1400px;
      margin: 0 auto;
      padding: 24px 20px 56px;
    }}
    .disclaimer {{
      background: #eff6ff;
      border: 1px solid #bfdbfe;
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 24px;
      font-size: 0.95rem;
      line-height: 1.5;
      color: #1e40af;
    }}
    .disclaimer a {{
      color: #2563eb;
      text-decoration: underline;
      font-weight: 500;
    }}
    #dashboard-container {{
      width: 100%;
      min-height: 900px;
      overflow: hidden;
    }}
  </style>
</head>
<body>
  <main>
    <div class="disclaimer">
      This dashboard is not static. Instead we embed <a href="https://dbt.taleshape.cloud/view/j66rhu7ey1h1dve95hcnypuk" target="_blank" rel="noreferrer">this dashboard</a> with the Shaper JS SDK. Shaper then queries data directly from Motherduck. The dashboard definition is managed as code in the repository and is deployed automatically via the Github Action.
    </div>
    <div id="dashboard-container"></div>
  </main>
  <script src="https://dbt.taleshape.cloud/embed/shaper.js"></script>
  <script>
    const dashboard = shaper.dashboard({{
      container: document.getElementById("dashboard-container"),
      dashboardId: "j66rhu7ey1h1dve95hcnypuk",
    }});
  </script>
</body>
</html>
"""



def main() -> None:
    sql = load_source()
    TARGET.write_text(render_page(sql))
    print(f"Rendered {SOURCE} -> {TARGET}")


if __name__ == "__main__":
    main()
