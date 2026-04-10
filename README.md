# Fusion Issue Analytics

End-to-end analytics pipeline for [dbt-labs/dbt-fusion](https://github.com/dbt-labs/dbt-fusion) GitHub issues.

**Extract** issues via dlt → **Transform** with dbt Fusion + DuckDB → **Visualize** in Prefab.

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

## Data Details

- **Source**: 1,397 issues, 2,616 comments, 3,309 label assignments, 842 assignees
- **Date range**: May 2025 – present
- **Key metrics**:
  - Median time to close: ~18 days
  - Median time to first response: ~7 days
- **Source tests**: 21 tests covering uniqueness, not-null, referential integrity, and accepted values

## Roadmap

See [open issues](https://github.com/dbt-labs/fusion_issue_analysis/issues) for planned improvements including incremental loads, MotherDuck migration, CI/CD, and production deployment.
