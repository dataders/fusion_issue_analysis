[![Deploy Dashboard](https://github.com/dbt-labs/fusion_issue_analysis/actions/workflows/deploy-dashboard.yml/badge.svg)](https://github.com/dbt-labs/fusion_issue_analysis/actions/workflows/deploy-dashboard.yml)

# Fusion Issue Analytics

End-to-end analytics pipeline for [dbt-labs/dbt-fusion](https://github.com/dbt-labs/dbt-fusion) GitHub issues.

**Extract** issues via dlt → **Transform** with dbt Fusion + DuckDB → **Visualize** across six frameworks (Prefab, Evidence.dev, Observable, ggsql + Vega-Lite, mviz, Marimo).

## Architecture

```
GitHub API (dbt-labs/dbt-fusion)
        │
    dlt (GraphQL)
        │
  data/raw/*.parquet          ← gitignored, ~2MB
        │
  dbtf + DuckDB (14 models)
        │
  data/fusion_issues.duckdb   ← gitignored
        │
   Prefab dashboard
```

## Quick Start

### Prerequisites

- [uv](https://docs.astral.sh/uv/) for Python dependency management
- [dbtf](https://docs.getdbt.com/docs/cloud/cloud-cli-installation) (dbt Cloud CLI with Fusion engine)
- A GitHub personal access token with `public_repo` and `read:org` scopes

### 1. Install dependencies

```bash
uv sync
```

### 2. Extract issues from GitHub

```bash
export GITHUB_TOKEN=ghp_your_token_here
cd extract && uv run python run.py
```

This pulls all issues, comments, labels, assignees, and reactions from `dbt-labs/dbt-fusion` into parquet files under `data/raw/`.

### 3. Transform with dbt

```bash
cd transform && dbtf build --profiles-dir .
```

Builds 14 models into a DuckDB database at `data/fusion_issues.duckdb`:

| Layer | Models |
|-------|--------|
| Staging | `stg_issues`, `stg_issue_comments`, `stg_issue_labels`, `stg_issue_assignees` |
| Dimensions | `dim_users`, `dim_labels`, `dim_milestones` |
| Facts | `fct_issues`, `fct_issue_labels`, `fct_issue_comments` |
| Metrics | `milestone_burndown`, `bug_fix_velocity`, `response_time_trends`, `issue_summary` |

Run tests to validate source data:

```bash
dbtf test --profiles-dir .
```

### 4. Launch dashboard

```bash
uv run prefab serve dashboard/app.py --reload
```

Opens at [http://127.0.0.1:5175](http://127.0.0.1:5175) with:

- Summary cards (total issues, open count, median close time, median response time)
- Issues opened vs closed per week
- Bug fix velocity trend (median hours to close for bugs)
- Time to first response trend
- Milestone burndown for active milestones
- Top labels by issue count

### Production (MotherDuck + GitHub Pages)

The dashboard is deployed to GitHub Pages via CI. Data is also materialized in MotherDuck for remote access.

```bash
# Build against MotherDuck (requires MOTHERDUCK_TOKEN env var)
cd transform && dbtf build --profiles-dir . --target prod

# Export static dashboard
uv run prefab export dashboard/app.py -o dashboard/index.html
```

The GitHub Actions workflow (`.github/workflows/deploy-dashboard.yml`) automates extract → build → export → deploy on push to main or manual trigger.

## Data Details

- **Source**: 1,397 issues, 2,616 comments, 3,309 label assignments, 842 assignees
- **Date range**: May 2025 – present
- **Key metrics**:
  - Median time to close: ~18 days
  - Median time to first response: ~7 days
- **Source tests**: 21 tests covering uniqueness, not-null, referential integrity, and accepted values

## Dashboard Framework Bakeoff — Findings

The `dashboard/` directory hosts six implementations of the same issue-health dashboard
(Prefab, Prefab MySpace, ggsql + Vega-Lite, mviz, Observable Framework, Evidence.dev,
Marimo). Each one renders from the same DuckDB/MotherDuck tables but makes different
choices about how SQL, charts, layout, and build artifacts compose.

This section captures what we learned — the stack decomposition, per-framework
layer picks, capability coverage, and a weighted scoring rubric for choosing one
over another in future projects.

### The static dashboard stack

Every "framework" here is really a set of picks across seven layers. Pick the
query/transport layers first; the rest cascades.

| # | Layer                | What it does                           | Options seen                                                                   |
|---|----------------------|----------------------------------------|--------------------------------------------------------------------------------|
| 1 | Query engine         | Runs SQL against warehouse/file        | DuckDB (Py), DuckDB-WASM (browser), Snowflake/BQ HTTP                          |
| 2 | Query authoring      | Where SQL lives                        | dbt models, `.sql` files, MD fences, Python strings, SQL-extension             |
| 3 | Data transport       | Rows → browser                         | Baked JSON at build, Parquet + WASM at view, in-memory Python                  |
| 4 | Chart grammar        | Declarative viz language               | Vega-Lite, Observable Plot, ECharts, plotly, custom React components           |
| 5 | Chart runtime        | Renders pixels                         | vega-embed, Plot JS, ECharts JS, plotly.js, React                              |
| 6 | Layout / composition | Dashboard structure                    | MD + CSS grid, component primitives, notebook cells, hand-stitched HTML        |
| 7 | Authoring DSL + build| How you write + export it              | Python → HTML, Node SSG (Vite/Svelte), MD + JS SSG, JSON + script, `marimo export` |

### Per-framework layer picks

| Tool                   | ① Query              | ② Authoring               | ③ Transport              | ④ Grammar                | ⑤ Runtime       | ⑥ Layout               | ⑦ DSL + build              |
|------------------------|----------------------|---------------------------|--------------------------|--------------------------|-----------------|------------------------|----------------------------|
| **Prefab**             | DuckDB Py            | `.sql` files              | baked Python dicts       | custom React components  | React           | Prefab Row/Column      | Python → `prefab export`   |
| **Evidence.dev**       | **DuckDB-WASM**      | MD ```sql fences          | Parquet shipped to client | ECharts                 | ECharts JS      | Svelte + MD            | MD + Svelte → Vite SSG     |
| **Observable Framework** | pluggable loaders  | loader scripts (any lang) | `FileAttachment` baked   | Observable Plot          | Plot JS + D3    | MD + CSS grid          | MD + JS → Node SSG         |
| **ggsql + Vega-Lite**  | DuckDB Py            | SQL + `VISUALISE…DRAW`    | baked Vega-Lite specs    | Vega-Lite                | vega-embed      | hand-stitched HTML     | custom Python `build.py`   |
| **mviz**               | external generator   | JSON spec files           | pre-built JSON           | mviz presets (Vega-Lite) | vega-embed      | MD + grid fences       | `build.sh`                 |
| **Marimo**             | DuckDB Py            | `.sql` loaded in cells    | in-memory DataFrames     | plotly (or any)          | plotly.js       | `mo.hstack` / `vstack` | Python cells → `marimo export` |

Three observations fall out of this grid:

1. **Only Evidence pushes the query engine to the browser.** Everyone else bakes
   rows at build time. That single choice is why Evidence scales to large data
   and gets live filters for free — and why its Svelte-based build is the one
   with the most moving parts.
2. **Vega-Lite is reused twice** (ggsql, mviz). Observable Plot and ECharts each
   appear once. Prefab is the only tool with a bespoke chart grammar — its biggest
   lock-in risk.
3. **Layers ①–③ are the interesting ones.** Layers ④–⑦ mostly follow from the
   grammar choice. When picking a tool, compare query/transport first.

### Capability coverage (what actually rendered)

| Capability                                      | Prefab | Marimo          | Observable            | Evidence                                         | ggsql                                          | mviz                                |
|-------------------------------------------------|--------|-----------------|-----------------------|--------------------------------------------------|------------------------------------------------|-------------------------------------|
| True cumulative area chart                      | ✓      | ✓               | ✓                     | ✗ (weekly only — no window fns in page SQL)      | ✓                                              | ✓                                   |
| Multi-series percentile bands (p25/p50/p75)     | ✓      | ✓               | ✓                     | ✓                                                | partial (p50 only; no multi-line from one DRAW)| ✓                                   |
| Stacked bar with category fill                  | ✓      | ✓               | ✓                     | ✓                                                | ✓                                              | ✓                                   |
| Horizontal bar                                  | ✓      | ✓               | ✓                     | ✓ (`swapXY=true`)                                | ✓ (y/x swap in VISUALISE)                      | ✗ (vertical only)                   |
| Sortable/searchable data table                  | ✓      | ✗               | ✗                     | ✓                                                | ✗                                              | ✓                                   |
| Interactive filters/dropdowns                   | ✗      | ✓ (Plotly native)| partial (Inputs)     | ✗                                                | ✗                                              | ✗                                   |
| Milestone burndown / EPICs list                 | ✓      | ✗               | ✗                     | ✗                                                | ✗                                              | ✗                                   |
| Chart-type control                              | full   | full            | full                  | limited (AreaChart/BarChart/LineChart)           | full (DRAW clause)                             | limited (area/bar/line/table/big_value) |

Gaps worth flagging:

- **Evidence** cannot do true cumulative charts from page SQL — no window-function
  support in markdown code blocks. Window functions have to move to source `.sql`
  files, which couples the dbt layer to the page.
- **ggsql** can only show one `y`-series per `DRAW` line in the straightforward
  form; the percentile-bands chart degrades to p50 only.
- **mviz** has no horizontal-bar support — `close_by_label` and `assignee_workload`
  render vertically and get crowded.
- **Marimo** is the most interactive without a server, and now matches Prefab's
  coverage — the one gap is sortable tables (Marimo uses raw DataFrames).

### Scoring rubric

Scored 1–5 across 14 axes, then weighted for *this* repo's constraints: static
HTML artifact, GitHub Pages PR preview, Python-first team, agent-authored chart
specs. Weights applied:

| Axis                         | Weight | Reason                                               |
|------------------------------|--------|------------------------------------------------------|
| Deploy artifact fit          | ×3     | Must drop into GitHub Pages PR preview               |
| AI-gen fitness / diffability | ×3     | Agents author the chart specs                        |
| Runtime deps                 | ×2     | Python-only beats adding Node                        |
| Build simplicity             | ×2     | One command beats many                               |
| Data binding ergonomics      | ×2     | Per-chart friction compounds                         |
| Authoring accessibility      | ×1     |                                                      |
| Composition / layout         | ×1     |                                                      |
| Interactivity ceiling        | ×1     | Static is the goal; reactivity is bonus              |
| Chart grammar flexibility    | ×1     |                                                      |
| Theming                      | ×1     |                                                      |
| Ecosystem maturity           | ×1     | Internal tools tolerated                             |
| Data source connectivity     | ×1     |                                                      |
| Scalability (data×charts×team) | ×1   |                                                      |

### Weighted totals (max = 90)

| Tool                    | Weighted | Notes                                                       |
|-------------------------|----------|-------------------------------------------------------------|
| **mviz**                | **68**   | Best AI-gen fitness; capped by preset library               |
| **Prefab**              | **65**   | Python-native, cohesive look; custom-grammar lock-in        |
| **ggsql + Vega-Lite**   | **62**   | SQL-as-chart; weak on layout and upstream stability         |
| Marimo                  | 58       | Reactive exploration, awkward as dashboard artifact         |
| Evidence.dev            | 55       | WASM query engine wins on data scale; Node toolchain hurts  |
| Observable Framework    | 54       | Highest interactivity ceiling; JS tax for Python team       |

> Raw totals (unweighted) flip Evidence and Observable to 1st/2nd — their Node
> toolchain and lower AI-gen fitness penalize them *for this repo's constraints*,
> not abstractly.

### Key differentiators — what each tool can do that others cannot

| Tool                    | Unique capability                                                                                                        |
|-------------------------|--------------------------------------------------------------------------------------------------------------------------|
| **Prefab**              | Milestone burndown + EPICs list (only framework to render it); `serve` mode for live data refresh during development      |
| **Evidence.dev**        | SQL runs **in the browser** (DuckDB-WASM) — no bake step, no server; analyst-native authoring (MD + SQL, zero Python)    |
| **Observable Framework**| Pluggable **data loaders** in any language (shell, Python, Rust — anything that writes stdout); full Observable reactive cell graph |
| **ggsql + Vega-Lite**   | The SQL clause **is** the chart — `VISUALISE … DRAW` makes query and visualization a single artifact with no separate authoring layer |
| **mviz**                | JSON spec files = best AI-agent generation target; chart specs are pure data (diff-friendly, no code, no imports)         |
| **Marimo**              | Reactive Python **compute graph** — cells re-execute automatically on dependency change; exports to static HTML OR runs as live notebook |

### Decision guide for future projects

| If you need…                                              | Pick                    |
|-----------------------------------------------------------|-------------------------|
| Agent-authored, spec-diffable, static                     | mviz                    |
| Python-first, design-system feel, KPI + charts            | Prefab                  |
| "SQL is the chart" — one query, one figure                | ggsql                   |
| Investigation > presentation                              | Marimo                  |
| Analyst-authored BI site with filters and polish          | Evidence.dev            |
| Rich interactivity + bespoke viz (you accept Node)        | Observable Framework    |
| Full reactive Python app (not static)                     | Streamlit / Dash / Shiny |

## Roadmap

See [open issues](https://github.com/dbt-labs/fusion_issue_analysis/issues) for planned improvements including incremental loads, MotherDuck migration, CI/CD, and production deployment.
