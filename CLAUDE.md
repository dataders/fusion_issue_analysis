# Project: fusion_issue_analysis

End-to-end analytics pipeline for dbt Fusion GitHub issues — `dbt-labs/dbt-core`
issues labeled `engine:v2` (they were transferred there from `dbt-labs/dbt-fusion`).
Extract (dlt) → Transform (dbtf + DuckDB) → Visualize (a bakeoff of dashboard frameworks).

## Commands

```bash
# Extract issues from GitHub
cd extract && uv run python run.py

# Build dbt models (local)
cd transform && dbtf build --profiles-dir . --target dev

# Build dbt models (MotherDuck)
cd transform && dbtf build --profiles-dir . --target prod

# Run tests
cd transform && dbtf test --profiles-dir .

# Check the tile contract (manifest ↔ dbt models ↔ every framework)
uv run --with pytest pytest tests/test_tiles_contract.py

# Serve / export the flagship Prefab dashboard
uv run prefab serve dashboard/prefab/app.py --reload
uv run prefab export dashboard/prefab/app.py -o dashboard/prefab/app.html
```

## Architecture

- `extract/` — dlt pipeline (GitHub GraphQL → parquet or MotherDuck)
- `transform/` — dbt Fusion project (staging → marts → metrics)
- `dashboard/` — Visualization framework bakeoff: `index.html` = neutral tab wrapper; one directory per framework (`prefab/app.py` is the flagship)
- `dashboard/tiles.yml` — **the dashboard contract**: question-driven sections, tiles, models, chart forms, colorblind-validated palette. Every framework renders exactly these tiles. `dashboard/tiles.py` is the shared helper for Python frameworks.
- `data/` — gitignored, local DuckDB + parquet files

## Conventions

- Use `uv` for all Python package management. Never `pip`.
- Use `dbtf` (Fusion engine) for dbt builds, not `dbt-core`.
- Strict static analysis is enabled in `dbt_project.yml` — all models must pass `--static-analysis strict` against the prod (MotherDuck) target.
- Staging models use the `raw_source()` macro to switch between parquet (dev) and MotherDuck tables (prod).
- Labels are normalized once in `stg_issue_labels` (seed `label_map.csv` + `prefix:value` parsing) into `label_dimension`/`label_value`. Never filter on raw `label_name` downstream — dbt-core renames labels (`bug` → `type:bug`, `triage` → `status:triage`).
- Dashboard time windows are anchored to `as_of.as_of_date` (latest activity in the data), never `current_date`, so a stalled extract shows stale-but-correct numbers plus a staleness warning.
- To change a tile: edit `dashboard/tiles.yml` and its model in `transform/models/dashboard/`, then every framework; `tests/test_tiles_contract.py` enforces the sync.
- `MOTHERDUCK_TOKEN` env var controls whether the dashboard reads from MotherDuck or local DuckDB.
- Dashboard-specific semantic SQL belongs in `transform/models/dashboard/`. Avoid one-off dashboard queries under `dashboard/*/queries/` or embedded in framework scripts. Dashboard loaders should select or lightly pivot canonical dbt models; ggsql `VISUALISE` files are chart specs and should query dbt models; Evidence source SQL may be thin `SELECT *` wrappers because Evidence requires source files.

## PR Guidelines

- Use feature branches, never push directly to main.
- Commit messages should explain "why" not "what".
- PRs that change a Prefab dashboard should verify the export works: `uv run prefab export dashboard/app.py -o /tmp/test.html`

## Dashboard

- **Production:** https://dataders.github.io/fusion_issue_analysis/
- **Data in MotherDuck:** `md:fusion_issues` database, `raw_github_core` schema (raw, dbt-core engine:v2) + `main` schema (transformed). `raw_github` is the frozen pre-migration dbt-fusion archive.
- Dashboard auto-deploys on push to main via GitHub Actions.
