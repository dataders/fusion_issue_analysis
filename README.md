[![Deploy Dashboard](https://github.com/dataders/fusion_issue_analysis/actions/workflows/deploy-dashboard.yml/badge.svg)](https://github.com/dataders/fusion_issue_analysis/actions/workflows/deploy-dashboard.yml)

# Fusion Issue Analytics

Static dashboard bakeoff for dbt v2 issue analytics — [`engine:v2` issues in dbt-labs/dbt-core](https://github.com/dbt-labs/dbt-core/issues?q=label%3Aengine%3Av2).
Every framework renders the same question-driven tile set, defined once in [`dashboard/tiles.yml`](./dashboard/tiles.yml).

Start here:

- Live dashboard: [dashboard-bakeoff.anders.omg.lol](https://dashboard-bakeoff.anders.omg.lol/)
- About, context, and findings: [dashboard-bakeoff.anders.omg.lol/?tab=about](https://dashboard-bakeoff.anders.omg.lol/?tab=about)
- Contributing: [CONTRIBUTING.md](./CONTRIBUTING.md)

Use the searchable framework picker to switch dashboards. **Compare frameworks**
opens two views; **Add third** opens another. Each pane keeps its own filters.
Choose side-by-side or stacked layout (mobile stacks automatically), use **Link
scroll** to keep matching sections and charts aligned despite different heights, and
**Copy comparison link** to share the selected frameworks and layout. Links do not
include filters inside dashboards; live views may show newer data than snapshots.
Linked scrolling follows shared tile IDs or headings in the main scrolling panel,
leaves table scrollbars independent, and falls back to relative page position when
headings do not match. Pages hosted on another origin scroll independently.

## Local Development

Prerequisites:

- [uv](https://docs.astral.sh/uv/)
- [dbtf](https://docs.getdbt.com/docs/cloud/cloud-cli-installation)
- `GITHUB_TOKEN` for extract
- `MOTHERDUCK_TOKEN` for MotherDuck-backed builds

Install dependencies:

```bash
uv sync
```

Common commands:

```bash
make extract
make dbt
make build
make ui-test
make tanstack
make serve
make mcp-app
```

What they do:

- `make extract`: pull GitHub issue data with dlt
- `make dbt`: build shared models in DuckDB
- `make build`: export all dashboard variants
- `make tanstack`: build the TanStack Charts tab from the shared dbt models (requires Node.js 20.19+, 22.12+, or 24+)
- `make ui-test`: run Playwright checks against the generated dashboard exports
- `make serve`: build and open local static wrapper
- `make mcp-app`: build a local MCP Apps proof of concept for agent-hosted dashboard consumption

Dashboard variants include Prefab, ggsql + Vega-Lite, mviz, MDV, Observable, TanStack Charts, Evidence.dev, Marimo, Quarto, DAC, Shaper, and dbt charts. The MCP Apps spike is local-only for now.

## Repo Shape

- `extract/`: GitHub extraction with dlt
- `transform/`: shared dbt models
- `dashboard/`: framework-specific dashboard implementations and static wrapper

See the live about page for the longer write-up.
