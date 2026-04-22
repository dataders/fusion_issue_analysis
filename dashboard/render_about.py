from pathlib import Path
import markdown


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "about.md"
TARGET = ROOT / "about.html"


def render() -> str:
    source_text = SOURCE.read_text()
    body = markdown.markdown(
        source_text,
        extensions=["tables", "sane_lists"],
        output_format="html5",
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>About | dbt-fusion Issue Analysis</title>
  <style>
    * {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      line-height: 1.65;
      color: #181818;
      background: #fafafa;
    }}

    main {{
      max-width: 780px;
      margin: 0 auto;
      padding: 40px 20px 64px;
    }}

    p,
    ul,
    ol,
    table {{
      margin: 0 0 16px;
    }}

    h1,
    h2 {{
      line-height: 1.2;
      margin: 0 0 12px;
      color: #111;
    }}

    h1 {{
      font-size: clamp(2rem, 4vw, 2.8rem);
      margin-bottom: 18px;
    }}

    h2 {{
      margin-top: 32px;
      font-size: 1.2rem;
    }}

    .links {{
      font-size: 0.95rem;
      margin-bottom: 24px;
      color: #555;
    }}

    h1 + p {{
      font-size: 1.05rem;
      color: #333;
    }}

    a {{
      color: #0f5c56;
    }}

    code {{
      padding: 0.1rem 0.3rem;
      border-radius: 4px;
      background: #efefef;
      font-size: 0.94em;
    }}

    ul,
    ol {{
      padding-left: 20px;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.95rem;
    }}

    th,
    td {{
      padding: 10px 8px;
      border-bottom: 1px solid #ddd;
      text-align: left;
      vertical-align: top;
    }}

    th {{
      font-weight: 600;
    }}
  </style>
</head>
<body>
  <main>
    <!-- Generated from dashboard/about.md. Do not edit dashboard/about.html directly. -->
    {body}
  </main>
</body>
</html>
"""


def main() -> None:
    TARGET.write_text(render())
    print(f"Rendered {SOURCE} -> {TARGET}")


if __name__ == "__main__":
    main()
