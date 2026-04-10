# Fusion Issue Analytics Pipeline — Design Spec

## Overview

End-to-end analytics pipeline for `dbt-labs/dbt-fusion` GitHub issues: extract with dlt, transform with dbt Fusion + DuckDB, visualize with Prefab.

## Architecture

```
GitHub API (dbt-labs/dbt-fusion)
        │
        ▼
   dlt pipeline
   (github source)
        │
        ▼
  data/raw/*.parquet
        │
        ▼
  dbtf (Fusion engine)
  + DuckDB adapter
        │
        ▼
  data/fusion_issues.duckdb
        │
        ▼
   Prefab dashboard
```

## 1. Extract Layer

- **Tool**: `dlt` with verified `github` source
- **Target**: `data/raw/` as parquet files
- **Entities**: Issues (with full body), comments, labels, milestones, assignees, reactions
- **Auth**: `SOURCES__GITHUB__ACCESS_TOKEN` or `GITHUB_TOKEN` env var
- **Rate limiting**: Handled natively by dlt with backoff/retry
- **Script**: `extract/run.py` — simple script to configure and run the dlt pipeline

## 2. Transform Layer

### dbt Project Structure

```
transform/
  dbt_project.yml
  profiles.yml          # DuckDB connection → data/fusion_issues.duckdb
  models/
    staging/
      _sources.yml      # parquet sources via read_parquet()
      stg_issues.sql
      stg_issue_comments.sql
      stg_issue_labels.sql
    marts/
      dim_users.sql
      dim_labels.sql
      dim_milestones.sql
      fct_issues.sql
      fct_issue_labels.sql    # bridge table
      fct_issue_comments.sql
    metrics/
      _metrics.yml      # semantic layer definitions
```

### Star Schema

- **fct_issues**: One row per issue. Columns: issue_id, number, title, body, state, author_id, milestone_id, created_at, closed_at, updated_at, comment_count, time_to_close_hours, time_to_first_response_hours
- **fct_issue_labels**: Bridge table (issue_id, label_id)
- **fct_issue_comments**: One row per comment. Columns: comment_id, issue_id, author_id, body, created_at
- **dim_users**: user_id, login, avatar_url
- **dim_labels**: label_id, name, color, description
- **dim_milestones**: milestone_id, title, description, state, due_on, open_issues, closed_issues

### Key Metrics (Semantic Layer)

1. **Milestone burndown**: Open vs closed issues per milestone over time
2. **Time to first response**: Median/P90 time from issue creation to first comment
3. **Bug fix velocity**: Time to close for bug-labeled issues, trended over weeks
4. **Open issue count**: Current open issues, sliceable by milestone/label
5. **Issues opened per week**: Rate of new issue creation

## 3. Visualization Layer

- **Tool**: Prefab (prefab.prefect.io)
- **Connection**: DuckDB file at `data/fusion_issues.duckdb`
- **MVP Dashboard**:
  - Milestone burndown chart (per active milestone)
  - Time to first response trend
  - Bug fix velocity over time
  - Open vs closed issue trend
  - Label distribution

## 4. Future Roadmap (GitHub Issues)

- Incremental/snapshot loads with dlt `merge` write disposition
- MotherDuck migration for hosted sharing
- CI/CD pipeline (GitHub Actions) for scheduled runs
- Additional entities (PRs, discussions, commits)
- Expanded semantic layer metrics
- Prefab dashboard polish and additional views
- Text analysis on issue bodies

## Key Decisions

- **DuckDB path**: `data/fusion_issues.duckdb` — swap to MotherDuck via connection string later
- **Parquet as intermediate**: dlt writes parquet, dbt reads parquet — decouples extract from transform
- **Full issue body**: Captured and carried through to fct_issues for future text analysis
- **dbtf (Fusion)**: Using dbt Cloud CLI with Fusion engine for transforms
