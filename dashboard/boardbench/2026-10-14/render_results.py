"""Render a readable, standalone table from BoardBench's YAML report cards.

Run from the repository root with:
    uv run python dashboard/boardbench/2026-10-14/render_results.py
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from html import escape
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
RUBRIC = yaml.safe_load((ROOT / "rubric.yml").read_text())
CRITERIA = {item["id"]: item for item in RUBRIC["criteria"]}
BASELINE = RUBRIC["scoring"]["baseline"]
CARD_LINK = re.compile(r"\[Card\]\(cards/([\w-]+)\.yml\)")
VIEW_LINK = re.compile(r"\[([^]]+)\]\((https://[^)]+)\)")


@dataclass
class Board:
    id: str
    name: str
    url: str
    kind: str
    note: str
    card: dict
    bonus: float
    deductions: float
    failed_gate: bool

    @property
    def score(self) -> float:
        return self.card["score"] * 100


def load_boards() -> list[Board]:
    boards = []
    section = ""
    for line in (ROOT / "scorecard.md").read_text().splitlines():
        if line.startswith("## "):
            section = line[3:]
        elif line.startswith("| Live dashboard |"):
            section = "Live dashboard"
        match = CARD_LINK.search(line)
        if not match:
            continue
        view = VIEW_LINK.search(line)
        if not view:
            raise ValueError(f"Missing dashboard link in {line}")
        parts = line.split("|")
        card_id = match.group(1)
        card = yaml.safe_load((ROOT / "cards" / f"{card_id}.yml").read_text())
        if card["artifact_id"] != card_id:
            raise ValueError(f"Mismatched artifact ID: {card_id}")
        if card["rubric_version"] != RUBRIC["rubric_version"]:
            raise ValueError(f"Mismatched rubric version: {card_id}")
        if card["judge_errors"]:
            raise ValueError(f"Judge errors in {card_id}: {card['judge_errors']}")
        rows = card["rows"]
        if {row["criterion_id"] for row in rows} != CRITERIA.keys():
            raise ValueError(f"Missing or extra criteria in {card_id}")

        excellence = [
            row
            for row in rows
            if CRITERIA[row["criterion_id"]]["polarity"] == "positive" and not CRITERIA[row["criterion_id"]].get("gate")
        ]
        possible = sum(
            CRITERIA[row["criterion_id"]]["points"] for row in excellence if row["verdict"] != "cannot_determine"
        )
        bonus = (100 - BASELINE) * sum(row["points_earned"] for row in excellence) / possible if possible else 0.0
        deductions = -sum(
            row["points_earned"] for row in rows if CRITERIA[row["criterion_id"]]["polarity"] == "negative"
        )
        failed_gate = any(
            criterion.get("gate") and row["verdict"] == ("no" if criterion["polarity"] == "positive" else "yes")
            for row in rows
            for criterion in [CRITERIA[row["criterion_id"]]]
        )
        computed = 0.0 if failed_gate else min(max(BASELINE + bonus - deductions, 0), 100)
        if round(computed / 100, 3) != card["score"]:
            raise ValueError(f"Score does not reconcile for {card_id}: {computed}")

        if card_id == "shaper":
            kind = "Preview"
        elif card_id == "duckdb-wasm-metricflow":
            kind = "Other brief"
        elif section == "Published framework tabs":
            kind = "Snapshot"
        elif section == "Live dashboard":
            kind = "Live"
        else:
            kind = "Alternate"
        boards.append(
            Board(card_id, view.group(1), view.group(2), kind, parts[3].strip(), card, bonus, deductions, failed_gate)
        )
    if len(boards) != 23:
        raise ValueError(f"Expected 23 published views, found {len(boards)}")
    return sorted(boards, key=lambda board: (-board.score, board.name.lower()))


def criterion_table(rows: list[dict], *, compact: bool = False) -> str:
    if not rows:
        return '<p class="empty">None recorded.</p>'
    body = []
    for row in rows:
        criterion = CRITERIA[row["criterion_id"]]
        impact = row["points_earned"]
        if criterion.get("gate"):
            impact_label = "Gate only" if criterion["polarity"] == "positive" else "Gate"
        elif impact < 0:
            impact_label = f"−{abs(impact):g}"
        elif impact > 0:
            impact_label = f"+{impact:g} raw"
        else:
            impact_label = "0"
        if compact:
            verdict = "Defect" if impact < 0 else "Met"
        elif criterion.get("gate"):
            verdict = "Passed" if not (row["verdict"] == "yes" and criterion["polarity"] == "negative") else "Failed"
        else:
            verdict = {
                "yes": "Defect" if criterion["polarity"] == "negative" else "Met",
                "no": "Clear" if criterion["polarity"] == "negative" else "Not met",
                "na": "N/A",
                "cannot_determine": "Unclear",
            }.get(row["verdict"], row["verdict"])
        evidence = escape(row["evidence"] or "No additional evidence recorded.")
        body.append(
            "<tr>"
            f'<td class="criterion"><code>{escape(row["criterion_id"])}</code><span>{escape(criterion["question"])}</span></td>'
            f'<td><span class="verdict">{escape(verdict)}</span></td>'
            f'<td class="number impact">{impact_label}</td>'
            f'<td class="evidence">{evidence}</td>'
            "</tr>"
        )
    return (
        '<div class="checks-wrap"><table class="checks"><thead><tr>'
        "<th>Check</th><th>Result</th><th>Impact</th><th>Evidence</th>"
        "</tr></thead><tbody>" + "".join(body) + "</tbody></table></div>"
    )


def board_detail(board: Board) -> str:
    rows = board.card["rows"]
    defects = sorted((row for row in rows if row["points_earned"] < 0), key=lambda row: row["points_earned"])
    excellence = [row for row in rows if row["points_earned"] > 0 and not CRITERIA[row["criterion_id"]].get("gate")]
    other = [row for row in rows if row not in defects and row not in excellence]
    gate_note = " A failed gate sets the score to zero." if board.failed_gate else ""
    return f"""
    <section class="board-detail" id="{escape(board.id)}">
      <div class="detail-heading"><div><span class="kind">{escape(board.kind)}</span>
        <h2>{escape(board.name)}</h2><p>{escape(board.note)}</p></div>
        <strong class="detail-score">{board.score:.1f}<small> / 100</small></strong></div>
      <p class="math"><strong>{BASELINE}</strong> starting points <span>+</span>
        <strong>{board.bonus:.1f}</strong> excellence bonus <span>−</span>
        <strong>{board.deductions:.1f}</strong> defect deductions
        <span>=</span> <strong>{board.score:.1f}</strong>{gate_note}</p>
        <div class="detail-links"><a href="{escape(board.url, quote=True)}">Open dashboard ↗</a>
        <a href="cards/{escape(board.id, quote=True)}.yml">Raw BoardBench card</a></div>
      <h3>Deductions</h3>{criterion_table(defects, compact=True)}
      <h3>Excellence checks met</h3>{criterion_table(excellence, compact=True)}
      <details><summary>Show the remaining {len(other)} checks, including clear, N/A, and uncertain results</summary>
        {criterion_table(other)}</details>
    </section>"""


def render_rules(boards: list[Board]) -> None:
    """Build a searchable rule catalog and a plain Markdown fallback."""
    categories = RUBRIC["categories"]
    markdown = [
        "# BoardBench rule index",
        "",
        f"Rubric {RUBRIC['rubric_version']} · {len(CRITERIA)} rules · [Searchable rule browser](rules.html) · [Results](results.md)",
        "",
        "**Defect:** a yes subtracts the stated points. **Excellence:** a yes contributes raw points that are scaled into the 0–40 bonus. **Gate:** a failure sets the whole score to zero; its raw points are excluded from the bonus. ‘Triggered’ means a defect found, excellence earned, or gate failed in the captured views.",
        "",
        "| Rule | Category | Kind | Weight | Checked by | Triggered views | Question |",
        "|---|---|---|---:|---|---:|---|",
    ]
    table_rows = []
    details = []
    for criterion in RUBRIC["criteria"]:
        rule_id = criterion["id"]
        gate = bool(criterion.get("gate"))
        kind = "Gate" if gate else "Excellence" if criterion["polarity"] == "positive" else "Defect"
        points = criterion["points"]
        weight = "Pass/fail" if gate else f"+{points}" if points > 0 else f"−{abs(points)}"
        affected = []
        na_count = 0
        unclear_count = 0
        for board in boards:
            row = next(row for row in board.card["rows"] if row["criterion_id"] == rule_id)
            if row["verdict"] == "na":
                na_count += 1
            elif row["verdict"] == "cannot_determine":
                unclear_count += 1
            triggered = (
                row["verdict"] == ("no" if criterion["polarity"] == "positive" else "yes")
                if gate
                else row["verdict"] == "yes"
            )
            if triggered:
                affected.append(board)
        question = criterion["question"]
        category = categories[criterion["category"]]
        markdown.append(
            f"| [{rule_id}](rules.html#rule-{rule_id}) | {criterion['category'].replace('_', ' ')} | "
            f"{kind} | {weight} | {criterion['checker']} | {len(affected)} | {question.replace('|', '\\|')} |"
        )
        table_rows.append(
            f'<tr data-category="{escape(criterion["category"], quote=True)}" '
            f'data-kind="{kind}" data-search="{escape((rule_id + " " + category + " " + question).lower(), quote=True)}">'
            f'<td><a class="id" href="#rule-{escape(rule_id)}">{escape(rule_id)}</a></td>'
            f'<td>{escape(category)}</td><td>{kind}</td><td class="number">{weight}</td>'
            f'<td>{escape(criterion["checker"].title())}</td><td class="number">{len(affected)} / {len(boards)}</td>'
            f"<td>{escape(question)}</td></tr>"
        )
        notes = []
        if criterion.get("how_to_check"):
            notes.append(f"<p><strong>How to check:</strong> {escape(criterion['how_to_check'])}</p>")
        if criterion.get("na_when"):
            notes.append(f"<p><strong>Not applicable when:</strong> {escape(criterion['na_when'])}</p>")
        if criterion.get("needs_brief"):
            notes.append("<p><strong>Requires the issue-health brief.</strong></p>")
        if criterion.get("implies"):
            notes.append(f"<p><strong>Depends on:</strong> {escape(criterion['implies'])}</p>")
        if gate:
            notes.append(
                f"<p><strong>Raw YAML points:</strong> {points:+g}; gate results override the score formula.</p>"
            )
        affected_links = (
            ", ".join(f'<a href="results.html#{escape(board.id)}">{escape(board.name)}</a>' for board in affected)
            or "None in this capture"
        )
        details.append(
            f'<section class="rule" id="rule-{escape(rule_id)}"><div class="rule-head"><span class="id">{escape(rule_id)}</span>'
            f'<span class="pill">{kind}</span><span class="pill">{escape(criterion["checker"].title())}</span>'
            f'<span class="weight">{weight}</span></div><h2>{escape(question)}</h2>'
            f'<p class="category">{escape(category)}</p>{"".join(notes)}'
            f"<p><strong>Triggered in {len(affected)} of {len(boards)} captures:</strong> {affected_links}</p>"
            f'<p class="muted">Not applicable: {na_count} · Unclear: {unclear_count}</p></section>'
        )
    markdown.extend(
        [
            "",
            "The trigger counts describe only the 23 views captured on 14 October 2026. A rule marked N/A or unclear does not count as triggered. [Read how the final score is calculated](results.md).",
            "",
        ]
    )
    (ROOT / "rules.md").write_text("\n".join(markdown))

    options = "".join(
        f'<option value="{escape(key, quote=True)}">{escape(label)}</option>'
        for key, label in categories.items()
        if any(item["category"] == key for item in RUBRIC["criteria"])
    )
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>BoardBench rules · rubric {escape(RUBRIC["rubric_version"])}</title>
<style>
:root {{ color-scheme:light dark; font:16px/1.5 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
--bg:#f6f7f9;--surface:#fff;--text:#1c2936;--muted:#5b6876;--line:#d9dfe5;--accent:#205d9f;--accent-bg:#e8f1fb;--shadow:0 8px 30px rgba(21,37,54,.06); }}
@media (prefers-color-scheme:dark) {{ :root {{ --bg:#101720;--surface:#192431;--text:#e7edf3;--muted:#aab7c3;--line:#364657;--accent:#8fc3fb;--accent-bg:#1c3856;--shadow:none; }} }}
* {{box-sizing:border-box}} body {{margin:0;background:var(--bg);color:var(--text)}} main {{max-width:1300px;margin:auto;padding:32px 24px 90px}}
a {{color:var(--accent)}} h1 {{font-size:clamp(2rem,4vw,3rem);letter-spacing:-.04em;line-height:1.1;margin:6px 0 12px}}
h2 {{font-size:1.18rem;line-height:1.3;margin:8px 0}} p {{margin:8px 0}} .eyebrow {{color:var(--accent);font-weight:800;font-size:.78rem;letter-spacing:.1em;text-transform:uppercase}}
.lede {{max-width:80ch;color:var(--muted)}} .nav {{display:flex;gap:18px;margin:20px 0 26px}} .explain {{background:var(--surface);border:1px solid var(--line);border-radius:13px;padding:16px 20px;box-shadow:var(--shadow);margin:20px 0}}
.controls {{display:flex;flex-wrap:wrap;gap:12px;align-items:end;margin:25px 0 12px}} label {{display:grid;gap:4px;font-size:.83rem;color:var(--muted);font-weight:750}}
input,select {{font:inherit;color:var(--text);background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:9px 11px}} input {{width:min(370px,80vw)}}
#count {{color:var(--muted);margin-left:auto;font-size:.9rem}} .wrap {{overflow:auto;background:var(--surface);border:1px solid var(--line);border-radius:11px}}
table {{width:100%;min-width:980px;border-collapse:collapse}} th,td {{padding:10px 12px;border-bottom:1px solid var(--line);vertical-align:top}} tbody tr:last-child td {{border-bottom:0}}
th {{text-align:left;text-transform:uppercase;letter-spacing:.03em;font-size:.76rem;color:var(--muted)}} tbody tr:hover {{background:var(--accent-bg)}} .number {{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}}
.id {{font-weight:800;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}} .rule {{background:var(--surface);border:1px solid var(--line);border-radius:13px;padding:19px 22px;margin:13px 0;scroll-margin-top:18px;box-shadow:var(--shadow)}}
.rule-head {{display:flex;gap:9px;align-items:center;flex-wrap:wrap}} .pill {{font-size:.74rem;font-weight:700;background:var(--accent-bg);color:var(--accent);padding:2px 9px;border-radius:999px}}
.weight {{margin-left:auto;font-variant-numeric:tabular-nums;font-weight:800}} .category,.muted {{color:var(--muted)}} .category {{font-size:.88rem}} .rule p {{max-width:100ch}}
@media(max-width:700px) {{#count {{margin-left:0;width:100%}}}}
</style></head><body><main>
<div class="eyebrow">BoardBench · rubric {escape(RUBRIC["rubric_version"])}</div><h1>Browse the rules</h1>
<p class="lede">All {len(CRITERIA)} rules used for the 23 dashboard captures on 14 October 2026. Search questions or IDs, filter by category and kind, then select a rule for its guidance and affected dashboards.</p>
<nav class="nav"><a href="results.html">Results table</a><a href="rules.md">Markdown rule list</a><a href="rubric.yml">Raw rubric YAML</a></nav>
<div class="explain"><strong>What a rule does:</strong> A “yes” on a defect subtracts its stated points. A “yes” on excellence contributes to the scaled 0–40 bonus. A gate failure sets the whole score to zero. “Triggered” counts defects found, excellence earned, or gate failures in this capture.</div>
<div class="controls"><label>Search rules<input id="search" type="search" placeholder="Rule ID or words in question"></label>
<label>Category<select id="category"><option value="">All categories</option>{options}</select></label>
<label>Kind<select id="kind"><option value="">All kinds</option><option>Defect</option><option>Excellence</option><option>Gate</option></select></label>
<span id="count" aria-live="polite">{len(CRITERIA)} rules</span></div>
<div class="wrap"><table id="rules"><thead><tr><th>Rule</th><th>Category</th><th>Kind</th><th class="number">Weight</th><th>Checker</th><th class="number">Triggered</th><th>Question</th></tr></thead>
<tbody>{"".join(table_rows)}</tbody></table></div>
<h2>Rule details</h2>{"".join(details)}
</main><script>
const rows=[...document.querySelectorAll('#rules tbody tr')];
const search=document.querySelector('#search'), category=document.querySelector('#category'), kind=document.querySelector('#kind');
function update() {{
  const query=search.value.trim().toLowerCase(); let visible=0;
  for (const row of rows) {{
    const match=(!query||row.dataset.search.includes(query))&&(!category.value||row.dataset.category===category.value)&&(!kind.value||row.dataset.kind===kind.value);
    row.hidden=!match; if(match) visible++;
  }}
  document.querySelector('#count').textContent=`${{visible}} of ${{rows.length}} rules`;
}}
for(const control of [search,category,kind]) control.addEventListener(control===search?'input':'change',update);
</script></body></html>"""
    (ROOT / "rules.html").write_text(html)


def main() -> None:
    boards = load_boards()
    render_rules(boards)
    rows = []
    markdown = [
        "# BoardBench results table",
        "",
        "Captured 14 October 2026. [Interactive report with criterion evidence](results.html) · [Browse the rules](rules.md) · [Scorecard and capture notes](scorecard.md)",
        "",
        "**Score = 60 starting points + scaled excellence bonus − defect deductions**, capped at 0–100. A failed delivery or whole-page gate sets the score to zero. Negative values mean a defect was found; they are changes to the score, not negative final scores. The raw `DEL-01` `+10` in YAML is a gate marker and is excluded from the formula.",
        "",
        "For example, dbt charts is **60 + 14.5 − 12 = 62.5**; the captured Mosaic page is **60 + 9.7 − 64 = 5.7**. Values are rounded to one decimal for display.",
        "",
        "| Rank | Dashboard | Type | Start | Excellence bonus | Defect deductions | Score / 100 | Largest deductions |",
        "|---:|---|---|---:|---:|---:|---:|---|",
    ]
    for rank, board in enumerate(boards, 1):
        defects = sorted(
            (row for row in board.card["rows"] if row["points_earned"] < 0), key=lambda row: row["points_earned"]
        )
        top = (
            ", ".join(f"{row['criterion_id']} (−{abs(row['points_earned']):g})" for row in defects[:2])
            or "No deductions"
        )
        markdown.append(
            f"| {rank} | [{board.name}]({board.url}) ([details](results.html#{board.id})) | {board.kind} | {BASELINE} | "
            f"+{board.bonus:.1f} | −{board.deductions:.1f} | **{board.score:.1f}** | {top} |"
        )
        searchable = " ".join(row["criterion_id"] for row in defects)
        rows.append(
            f'<tr data-kind="{escape(board.kind, quote=True)}" data-name="{escape(board.name.lower(), quote=True)}" '
            f'data-search="{escape(searchable.lower(), quote=True)}" '
            f'data-score="{board.score:.1f}" data-bonus="{board.bonus:.3f}" data-deductions="{board.deductions:.1f}">'
            f'<td class="number muted">{rank}</td>'
            f'<td><a class="board-link" href="#{escape(board.id, quote=True)}">{escape(board.name)}</a></td>'
            f'<td><span class="kind">{escape(board.kind)}</span></td>'
            f'<td class="number">{BASELINE}</td>'
            f'<td class="number bonus">+{board.bonus:.1f}</td>'
            f'<td class="number deduction">−{board.deductions:.1f}</td>'
            f'<td class="number"><strong class="score">{board.score:.1f}</strong></td>'
            f'<td class="top-defects">{escape(top)}</td></tr>'
        )

    markdown.extend(
        [
            "",
            "Each score comes from one OpenAI judge sample plus program checks. Scores a few points apart should be treated as close. Shaper is a source/run preview, and MetricFlow uses a different brief; neither is directly comparable with the rendered issue-health views. Numerical correctness was not checked against reference values. The [raw cards](cards/) retain every BoardBench verdict and vote.",
            "",
        ]
    )
    (ROOT / "results.md").write_text("\n".join(markdown))

    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>BoardBench results · dbt v2 dashboard bakeoff</title>
<style>
:root {{ color-scheme: light dark; font: 16px/1.5 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --bg:#f6f7f9; --surface:#fff; --text:#1c2936; --muted:#5b6876; --line:#d9dfe5;
  --accent:#205d9f; --accent-bg:#e8f1fb; --good:#226b45; --bad:#a33d3d; --bad-bg:#faeeee;
  --shadow:0 8px 30px rgba(21,37,54,.06); }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#101720; --surface:#192431; --text:#e7edf3; --muted:#aab7c3;
  --line:#364657; --accent:#8fc3fb; --accent-bg:#1c3856; --good:#8fd7ae; --bad:#ffaaa9;
  --bad-bg:#4a292e; --shadow:none; }} }}
* {{ box-sizing:border-box; }} body {{ margin:0; background:var(--bg); color:var(--text); }}
a {{ color:var(--accent); }} a:hover {{ text-decoration-thickness:2px; }}
main {{ max-width:1440px; margin:auto; padding:32px 24px 96px; }}
header {{ margin-bottom:28px; }} .eyebrow {{ color:var(--accent); font-size:.78rem; font-weight:800; letter-spacing:.11em; text-transform:uppercase; }}
h1 {{ font-size:clamp(2rem,4vw,3.2rem); letter-spacing:-.04em; line-height:1.1; margin:.25rem 0 .65rem; }}
h2 {{ font-size:1.55rem; letter-spacing:-.025em; margin:.4rem 0; }} h3 {{ font-size:1.05rem; margin:28px 0 10px; }}
p {{ margin:.45rem 0; }} .lede {{ max-width:75ch; color:var(--muted); }}
.overview {{ display:grid; grid-template-columns:minmax(280px,1.25fr) repeat(2,minmax(190px,.65fr)); gap:14px; margin:24px 0 34px; }}
.panel, .board-detail {{ background:var(--surface); border:1px solid var(--line); border-radius:14px; box-shadow:var(--shadow); }}
.panel {{ padding:18px 21px; }} .panel h2 {{ font-size:1rem; margin:0 0 7px; }} .panel p {{ color:var(--muted); font-size:.92rem; }}
.formula {{ font-weight:750; font-variant-numeric:tabular-nums; font-size:1.15rem; }}
.formula .plus {{ color:var(--good); }} .formula .minus {{ color:var(--bad); }}
.controls {{ display:flex; flex-wrap:wrap; gap:12px; align-items:end; margin:8px 0 12px; }}
.controls label {{ display:grid; gap:4px; color:var(--muted); font-size:.82rem; font-weight:700; }}
input, select {{ font:inherit; color:var(--text); background:var(--surface); border:1px solid var(--line); border-radius:8px; padding:9px 11px; }}
input {{ width:min(360px,80vw); }} #count {{ color:var(--muted); margin-left:auto; font-size:.9rem; }}
.table-wrap, .checks-wrap {{ overflow:auto; border:1px solid var(--line); border-radius:11px; background:var(--surface); }}
table {{ border-collapse:collapse; width:100%; }} th, td {{ padding:11px 13px; border-bottom:1px solid var(--line); vertical-align:top; }}
tbody tr:last-child td {{ border-bottom:0; }} tbody tr:hover {{ background:var(--accent-bg); }}
th {{ text-align:left; white-space:nowrap; color:var(--muted); background:var(--surface); font-size:.76rem; font-weight:800; text-transform:uppercase; letter-spacing:.035em; }}
.results th {{ position:sticky; top:0; z-index:1; }} th button {{ all:unset; cursor:pointer; }} th button:focus-visible {{ outline:2px solid var(--accent); }}
.results {{ min-width:1000px; }} .number {{ text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }}
.board-link {{ font-weight:750; text-decoration:none; white-space:nowrap; }} .board-link:hover {{ text-decoration:underline; }}
.kind {{ display:inline-block; white-space:nowrap; font-size:.75rem; font-weight:750; border-radius:999px; padding:2px 9px; background:var(--accent-bg); color:var(--accent); }}
.bonus {{ color:var(--good); }} .deduction {{ color:var(--bad); }} .score {{ font-size:1.1rem; }}
.muted, .top-defects {{ color:var(--muted); }} .top-defects {{ font-size:.88rem; }}
.help {{ color:var(--muted); font-size:.88rem; margin:10px 0 30px; }}
.board-detail {{ padding:24px; margin:18px 0; scroll-margin-top:16px; }} .detail-heading {{ display:flex; justify-content:space-between; gap:20px; }}
.detail-heading p {{ color:var(--muted); max-width:85ch; }} .detail-score {{ white-space:nowrap; font-size:2rem; font-variant-numeric:tabular-nums; }}
.detail-score small {{ font-size:.75rem; color:var(--muted); }} .math {{ padding:11px 14px; background:var(--accent-bg); border-radius:9px; font-variant-numeric:tabular-nums; }}
.math span {{ padding:0 6px; }} .detail-links {{ display:flex; gap:18px; font-size:.88rem; }}
.checks {{ min-width:900px; font-size:.88rem; }} .checks .criterion {{ width:35%; }} .criterion code {{ font-size:.8rem; font-weight:800; margin-right:8px; }}
.criterion span {{ color:var(--text); }} .checks .evidence {{ width:45%; color:var(--muted); }} .checks .impact {{ font-weight:750; }}
.verdict {{ white-space:nowrap; }} details {{ margin-top:24px; }} summary {{ cursor:pointer; font-weight:750; margin-bottom:12px; }}
.empty {{ color:var(--muted); font-style:italic; }} footer {{ color:var(--muted); font-size:.86rem; margin-top:38px; }}
@media (max-width:850px) {{ .overview {{ grid-template-columns:1fr; }} .detail-heading {{ flex-direction:column; gap:0; }} #count {{ margin-left:0; width:100%; }} }}
</style></head><body><main>
<header><div class="eyebrow">BoardBench · rubric {escape(RUBRIC["rubric_version"])}</div>
<h1>Dashboard results</h1>
<p class="lede">23 views of the dbt v2 issue dashboard bakeoff, captured 14 October 2026. Each was scored from its saved screenshot, page text, and console metadata by one OpenAI judge sample. Scores describe that capture, not the current deployed page.</p>
<p><a href="rules.html">Browse all {len(CRITERIA)} scoring rules →</a></p></header>
<div class="overview">
  <div class="panel"><h2>How the score works</h2><div class="formula">60 starting points <span class="plus">+ excellence</span> <span class="minus">− defects</span> = score</div>
    <p>A “yes” on a defect subtracts its stated points. Excellence checks are scaled into a bonus of up to 40. The result is capped at 0–100; a failed delivery or whole-page gate sets it to 0.</p></div>
  <div class="panel"><h2>Why YAML shows +10 for delivery</h2><p><code>DEL-01</code> is a pass/fail gate. Its raw <strong>+10</strong> is excluded from the final formula. The table below shows the actual scaled bonus.</p></div>
  <div class="panel"><h2>Read the rankings carefully</h2><p>Scores a few points apart are close. Shaper is a preview page; MetricFlow uses a different brief. Neither is directly comparable with the rendered issue-health views.</p></div>
</div>
<h2>Compare all views</h2>
<div class="controls"><label>Find a dashboard<input id="search" type="search" placeholder="Name or deduction ID"></label>
  <label>View type<select id="kind"><option value="">All types</option><option>Snapshot</option><option>Live</option><option>Alternate</option><option>Preview</option><option>Other brief</option></select></label>
  <span id="count" aria-live="polite">23 views</span></div>
<div class="table-wrap"><table class="results" id="results"><thead><tr>
  <th>Rank</th><th><button data-sort="name">Dashboard ↕</button></th><th>Type</th><th class="number">Start</th>
  <th class="number"><button data-sort="bonus">Bonus ↕</button></th><th class="number"><button data-sort="deductions">Deductions ↕</button></th>
  <th class="number"><button data-sort="score">Score / 100 ↕</button></th><th>Largest deductions</th>
</tr></thead><tbody>{"".join(rows)}</tbody></table></div>
<p class="help">Deductions are displayed as negative changes to the score. Select a dashboard name for every scored deduction, earned excellence check, and the judge’s evidence.</p>
<h2>Report cards</h2>{"".join(board_detail(board) for board in boards)}
<footer>Source: <a href="scorecard.md">scorecard and capture notes</a> · <a href="rules.html">browse all rules</a> · <a href="rubric.yml">rubric 2.8.0</a> ·
  <a href="brief.md">issue-health brief</a>. One judge sample means the stored agreement value is not independent reviewer agreement. Numerical correctness was not checked against reference values.</footer>
</main><script>
const body = document.querySelector('#results tbody');
const rows = Array.from(body.rows);
const search = document.querySelector('#search');
const kind = document.querySelector('#kind');
let sortBy = 'score';
let descending = true;
function update() {{
  const query = search.value.trim().toLowerCase();
  const type = kind.value;
  const sorted = [...rows].sort((a, b) => {{
    const av = a.dataset[sortBy], bv = b.dataset[sortBy];
    const difference = sortBy === 'name' ? av.localeCompare(bv) : Number(av) - Number(bv);
    return (descending ? -1 : 1) * difference || a.dataset.name.localeCompare(b.dataset.name);
  }});
  body.replaceChildren(...sorted);
  let visible = 0;
  for (const row of rows) {{
    const match = (!type || row.dataset.kind === type) && (!query || row.textContent.toLowerCase().includes(query) || row.dataset.search.includes(query));
    row.hidden = !match;
    if (match) visible++;
  }}
  document.querySelector('#count').textContent = `${{visible}} of ${{rows.length}} views`;
}}
for (const button of document.querySelectorAll('[data-sort]')) button.addEventListener('click', () => {{
  const next = button.dataset.sort;
  descending = next === sortBy ? !descending : next !== 'name';
  sortBy = next;
  update();
}});
search.addEventListener('input', update);
kind.addEventListener('change', update);
</script></body></html>"""
    (ROOT / "results.html").write_text(html)
    print(f"Rendered {len(boards)} cards to results.md/results.html and {len(CRITERIA)} rules to rules.md/rules.html")


if __name__ == "__main__":
    main()
