# Project: fusion_issue_analysis

End-to-end analytics pipeline for dbt-labs/dbt-fusion GitHub issues.
Extract (dlt) → Transform (dbtf + DuckDB) → Visualize (Prefab).

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

# Serve dashboard locally
uv run prefab serve dashboard/app.py --reload

# Export dashboard to static HTML
uv run prefab export dashboard/app.py -o dashboard/index.html
```

## Architecture

- `extract/` — dlt pipeline (GitHub GraphQL → parquet or MotherDuck)
- `transform/` — dbt Fusion project (staging → marts → metrics)
- `dashboard/` — Prefab dashboards (app.py = main, app_myspace.py = nostalgia mode)
- `data/` — gitignored, local DuckDB + parquet files

## Conventions

- Use `uv` for all Python package management. Never `pip`.
- Use `dbtf` (Fusion engine) for dbt builds, not `dbt-core`.
- Strict static analysis is enabled in `dbt_project.yml` — all models must pass `--static-analysis strict` against the prod (MotherDuck) target.
- Staging models use the `raw_source()` macro to switch between parquet (dev) and MotherDuck tables (prod).
- `MOTHERDUCK_TOKEN` env var controls whether the dashboard reads from MotherDuck or local DuckDB.

## PR Guidelines

- **Always include a dashboard preview link in the PR body.** The PR preview workflow deploys a preview to GitHub Pages on every PR. After the workflow runs, a bot comment will appear with the preview URL. Include this in the PR description:
  ```
  ## Dashboard Preview
  🔗 [Preview link](https://dbt-labs.github.io/fusion_issue_analysis/) (auto-posted by CI)
  ```
- Use feature branches, never push directly to main.
- Commit messages should explain "why" not "what".
- PRs that change the dashboard should verify the export works: `uv run prefab export dashboard/app.py -o /tmp/test.html`

## Dashboard

- **Production:** https://dbt-labs.github.io/fusion_issue_analysis/
- **Data in MotherDuck:** `md:fusion_issues` database, `raw_github` schema (raw) + `main` schema (transformed)
- Dashboard auto-deploys on push to main via GitHub Actions.
