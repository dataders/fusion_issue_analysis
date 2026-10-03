# Glyf

[Glyf](https://glyfdata.com) (`glyf-core` on PyPI) is a code-first build step: charts are
[ggsql](https://ggsql.org) files using `{{ ref('model') }}`, dashboards are YAML, and `glyf build`
renders a self-contained static site (Altair charts, PNG/SVG artifacts).

```bash
uv run dashboard/glyf/build.py        # -> dashboard/glyf/build/site/
uv run glyf serve --project-dir dashboard/glyf   # preview
```

## How it's wired

- `visualisations/*.ggsql` — one per tile; each selects from a `transform/models/dashboard/` model.
- `dashboards/fusion_issue_health.yml` — sections mirror `dashboard/tiles.yml`; `dashboards/macros.py` adds the freshness banner.
- `build.py` — Glyf wants a dbt `manifest.json` and a DuckDB file, but CI has no dbt build. So it copies the
  tile models from `FUSION_DB` / MotherDuck / local DuckDB into `target/glyf.duckdb` and writes a minimal
  manifest from `tiles.yml`. `dbt_project.yml` is a stub for Glyf's project-root check.

## Deviations from the tile contract

- **Palette:** Glyf has no custom color scale, so charts use its default theme, not the colorblind-validated palette.
- **Horizontal stacked bars** (area / adapter / assignee) are vertical stacked bars; Glyf's `bar` has no orientation option, and x categories sort alphabetically, not by total.
- **Tables** have no link column, so `issue_url` isn't shown.
- **KPIs** are six native `kpi` tiles; "Open issues" gets Glyf's built-in delta vs 28 days ago instead of the "+N in 28 days" text. Per-KPI context text isn't reproduced.
- The freshness banner lands in Glyf's "Overview" summary block, with a warning alert when stale.
- Charts load Vega from a CDN in the browser (PNG fallbacks are built alongside).
