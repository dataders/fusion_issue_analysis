# Dashboard Queries → dbt Models Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move all dashboard SQL queries from per-framework `queries/` directories (and inline Python/shell scripts) into a new `models/dashboard/` dbt layer; update every dashboard to reference those models by name; define all dashboards as dbt exposures.

**Architecture:** 21 new canonical dbt models live in `transform/models/dashboard/`, materialized as tables on prod (MotherDuck) and views on dev (local DuckDB). Each model wraps an existing mart or metric via `{{ ref() }}`. All dashboard code replaces its SQL with bare `SELECT * FROM <model_name>` strings (or for ggsql, retains the VISUALISE DSL after the SELECT). The existing `queries/` directories are deleted for every framework except ggsql (which must keep `.sql` files for its parser).

**Tech Stack:** dbt Fusion (`dbtf`), DuckDB, MotherDuck, Python (prefab/mviz/marimo), bash (observable data loader), Evidence.dev, Observable Framework, ggsql DSL.

**Reference:** GitHub issue #56 — https://github.com/dbt-labs/fusion_issue_analysis/issues/56

---

## Files Overview

### Create
```
transform/models/dashboard/summary_kpis.sql
transform/models/dashboard/cumulative_flow.sql
transform/models/dashboard/weekly_flow.sql
transform/models/dashboard/bug_velocity.sql
transform/models/dashboard/enh_velocity.sql
transform/models/dashboard/velocity.sql
transform/models/dashboard/response_pctiles.sql
transform/models/dashboard/age_distribution.sql
transform/models/dashboard/close_by_label.sql
transform/models/dashboard/triage_health.sql
transform/models/dashboard/epic_list.sql
transform/models/dashboard/open_issues_table.sql
transform/models/dashboard/assignee_workload.sql
transform/models/dashboard/community_priorities.sql
transform/models/dashboard/leaderboard.sql
transform/models/dashboard/milestone_burndown_weekly.sql
transform/models/dashboard/issues.sql
transform/models/dashboard/open_by_category.sql
transform/models/dashboard/issues_opened_per_week.sql
transform/models/dashboard/open_vs_closed_by_category.sql
transform/models/dashboard/top_authors.sql
transform/models/dashboard/_exposures.yml
```

### Modify
```
transform/dbt_project.yml                          — add dashboard materialization config
dashboard/prefab/app.py                            — replace load_sql() + query files with inline SELECT *
dashboard/prefab/app_myspace.py                    — replace inline SQL with SELECT *
dashboard/mviz/generate_data.py                    — replace load_sql() + query files with inline SELECT *
dashboard/marimo/app.py                            — replace load_sql() + fix hardcoded DB path + add MotherDuck support
dashboard/observable/src/data/summary.json.sh      — replace load_sql() with inline SELECT *; rename column ref
dashboard/evidence/sources/fusion/issues.sql       — replace fct_issues query with SELECT * FROM issues
dashboard/ggsql/queries/01_issues_opened_per_week.sql
dashboard/ggsql/queries/02_open_vs_closed_by_category.sql
dashboard/ggsql/queries/05_top_authors.sql
```

### Delete
```
dashboard/prefab/queries/           (14 .sql files)
dashboard/mviz/queries/             (9 .sql files)
dashboard/marimo/queries/           (6 .sql files)
dashboard/observable/queries/       (5 .sql files)
dashboard/evidence/queries/         (4 .sql files — dead code; page uses inline SQL)
```

---

## Task 1: Configure `models/dashboard/` materialization

**Files:**
- Modify: `transform/dbt_project.yml`

- [ ] **Step 1: Add dashboard layer to dbt_project.yml**

Open `transform/dbt_project.yml`. Under the `models.fusion_issue_analytics` key, add a `dashboard` block matching the existing `marts` and `metrics` pattern:

```yaml
models:
  fusion_issue_analytics:
    +materialized: view
    marts:
      +materialized: "{{ 'table' if target.name == 'prod' else 'view' }}"
    metrics:
      +materialized: "{{ 'table' if target.name == 'prod' else 'view' }}"
    dashboard:
      +materialized: "{{ 'table' if target.name == 'prod' else 'view' }}"
```

- [ ] **Step 2: Verify dbt_project.yml is valid YAML**

```bash
cd transform && dbtf parse --profiles-dir . --target dev
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add transform/dbt_project.yml
git commit -m "Configure dashboard model layer materialization"
```

---

## Task 2: Create KPI and flow models

**Files:**
- Create: `transform/models/dashboard/summary_kpis.sql`
- Create: `transform/models/dashboard/cumulative_flow.sql`
- Create: `transform/models/dashboard/weekly_flow.sql`

- [ ] **Step 1: Create `summary_kpis.sql`**

Source: `dashboard/prefab/queries/summary_kpis.sql` — replace bare table name with `ref()`.

```sql
with recent_window as (
    select
        count(case when created_at >= current_date - interval '28 days' then 1 end) as opened_4w,
        count(case when closed_at >= current_date - interval '28 days' then 1 end) as closed_4w,
        count(case when state = 'OPEN' then 1 end) as open_issues,
        count(*) as total_issues
    from {{ ref('fct_issues') }} where issue_category != 'epic'
),
rolling_close as (
    select round(median(hours_to_close) / 24, 1) as rolling_median_close_days
    from {{ ref('fct_issues') }}
    where closed_at >= current_date - interval '28 days' and issue_category != 'epic'
),
sla as (
    select
        round(
            count(case when hours_to_first_response <= 48 then 1 end)::float
            / nullif(count(case when hours_to_first_response is not null then 1 end), 0)
            * 100, 0
        ) as pct_responded_48h
    from {{ ref('fct_issues') }}
    where created_at >= current_date - interval '28 days' and issue_category != 'epic'
),
stale as (
    select count(*) as stale_count
    from {{ ref('fct_issues') }}
    where state = 'OPEN' and updated_at < current_date - interval '30 days' and issue_category != 'epic'
)
select * from recent_window cross join rolling_close cross join sla cross join stale
```

- [ ] **Step 2: Create `cumulative_flow.sql`**

Source: `dashboard/prefab/queries/cumulative_flow.sql` (richer version with bug/enh breakdown).

```sql
with weeks as (
    select
        date_trunc('week', created_at)::date as week,
        count(*) as opened,
        count(case when issue_category = 'bug' then 1 end) as bugs_opened,
        count(case when issue_category = 'enhancement' then 1 end) as enhancements_opened
    from {{ ref('fct_issues') }} where issue_category != 'epic'
    group by 1
),
closed_weeks as (
    select
        date_trunc('week', closed_at)::date as week,
        count(*) as closed,
        count(case when issue_category = 'bug' then 1 end) as bugs_closed,
        count(case when issue_category = 'enhancement' then 1 end) as enhancements_closed
    from {{ ref('fct_issues') }} where closed_at is not null and issue_category != 'epic'
    group by 1
),
combined as (
    select
        coalesce(w.week, c.week) as week,
        coalesce(w.opened, 0) as opened,
        coalesce(c.closed, 0) as closed,
        coalesce(w.bugs_opened, 0) as bugs_opened,
        coalesce(c.bugs_closed, 0) as bugs_closed,
        coalesce(w.enhancements_opened, 0) as enh_opened,
        coalesce(c.enhancements_closed, 0) as enh_closed
    from weeks w
    full outer join closed_weeks c on w.week = c.week
)
select
    strftime(week, '%Y-%m-%d') as week,
    sum(opened) over (order by week) as cumulative_opened,
    sum(closed) over (order by week) as cumulative_closed,
    sum(bugs_opened) over (order by week) as cum_bugs_opened,
    sum(bugs_closed) over (order by week) as cum_bugs_closed,
    sum(enh_opened) over (order by week) as cum_enh_opened,
    sum(enh_closed) over (order by week) as cum_enh_closed
from combined
order by week
```

- [ ] **Step 3: Create `weekly_flow.sql`**

Source: `dashboard/marimo/queries/weekly_flow.sql` (non-cumulative; also used by observable and evidence).

```sql
with opened as (
    select date_trunc('week', created_at)::date as week, count(*) as opened
    from {{ ref('fct_issues') }} where issue_category != 'epic'
    group by 1
),
closed as (
    select date_trunc('week', closed_at)::date as week, count(*) as closed
    from {{ ref('fct_issues') }} where closed_at is not null and issue_category != 'epic'
    group by 1
)
select
    strftime(coalesce(o.week, c.week), '%Y-%m-%d') as week,
    coalesce(o.opened, 0) as opened,
    coalesce(c.closed, 0) as closed
from opened o full outer join closed c on o.week = c.week
order by 1
```

- [ ] **Step 4: Build these three models**

```bash
cd transform && dbtf build -s summary_kpis cumulative_flow weekly_flow --profiles-dir . --target dev --static-analysis off
```

Expected: 3 models created successfully, 0 errors.

- [ ] **Step 5: Commit**

```bash
git add transform/models/dashboard/
git commit -m "Add dashboard KPI and flow models"
```

---

## Task 3: Create velocity and response models

**Files:**
- Create: `transform/models/dashboard/bug_velocity.sql`
- Create: `transform/models/dashboard/enh_velocity.sql`
- Create: `transform/models/dashboard/velocity.sql`
- Create: `transform/models/dashboard/response_pctiles.sql`

- [ ] **Step 1: Create `bug_velocity.sql`**

Source: `dashboard/prefab/queries/bug_velocity.sql` (identical in mviz).

```sql
select
    strftime(date_trunc('week', closed_at), '%Y-%m-%d') as week,
    round(median(hours_to_close) / 24, 1) as median_days
from {{ ref('fct_issues') }}
where issue_category = 'bug' and closed_at is not null
group by date_trunc('week', closed_at)
having count(*) >= 3
order by week
```

- [ ] **Step 2: Create `enh_velocity.sql`**

Source: `dashboard/prefab/queries/enh_velocity.sql` (identical in mviz).

```sql
select
    strftime(date_trunc('week', closed_at), '%Y-%m-%d') as week,
    round(median(hours_to_close) / 24, 1) as median_days
from {{ ref('fct_issues') }}
where issue_category = 'enhancement' and closed_at is not null
group by date_trunc('week', closed_at)
having count(*) >= 2
order by week
```

- [ ] **Step 3: Create `velocity.sql`**

Source: `dashboard/marimo/queries/velocity.sql` (identical in observable) — combined bug+enh in one dataset.

```sql
select
    strftime(date_trunc('week', closed_at), '%Y-%m-%d') as week,
    issue_category,
    round(median(hours_to_close) / 24.0, 1) as median_days,
    count(*) as n
from {{ ref('fct_issues') }}
where closed_at is not null and issue_category in ('bug', 'enhancement')
group by 1, 2
having count(*) >= 2
order by 1
```

- [ ] **Step 4: Create `response_pctiles.sql`**

Source: `dashboard/prefab/queries/response_pctiles.sql` (identical in mviz).

```sql
select
    strftime(date_trunc('week', created_at), '%Y-%m-%d') as week,
    round(quantile_cont(hours_to_first_response, 0.25), 1) as p25,
    round(quantile_cont(hours_to_first_response, 0.50), 1) as p50,
    round(quantile_cont(hours_to_first_response, 0.75), 1) as p75
from {{ ref('fct_issues') }}
where hours_to_first_response is not null and issue_category != 'epic'
group by date_trunc('week', created_at)
having count(*) >= 3
order by week
```

- [ ] **Step 5: Build these four models**

```bash
cd transform && dbtf build -s bug_velocity enh_velocity velocity response_pctiles --profiles-dir . --target dev --static-analysis off
```

Expected: 4 models created, 0 errors.

- [ ] **Step 6: Commit**

```bash
git add transform/models/dashboard/
git commit -m "Add dashboard velocity and response percentile models"
```

---

## Task 4: Create distribution and label models

**Files:**
- Create: `transform/models/dashboard/age_distribution.sql`
- Create: `transform/models/dashboard/close_by_label.sql`

- [ ] **Step 1: Create `age_distribution.sql`**

Source: `dashboard/prefab/queries/age_distribution.sql` (identical in mviz).

```sql
select
    issue_category,
    case
        when datediff('day', created_at, current_date) <= 7 then '0-7d'
        when datediff('day', created_at, current_date) <= 30 then '8-30d'
        when datediff('day', created_at, current_date) <= 90 then '31-90d'
        when datediff('day', created_at, current_date) <= 180 then '91-180d'
        else '180d+'
    end as age_bucket,
    count(*) as issue_count
from {{ ref('fct_issues') }}
where state = 'OPEN' and issue_category != 'epic'
group by 1, 2
```

- [ ] **Step 2: Create `close_by_label.sql`**

Source: `dashboard/prefab/queries/close_by_label.sql` (identical in mviz).

```sql
select
    l.label_name,
    round(median(f.hours_to_close) / 24, 1) as median_days_to_close,
    count(*) as closed_count
from {{ ref('fct_issues') }} f
inner join {{ ref('fct_issue_labels') }} l on f.issue_dlt_id = l.issue_dlt_id
where f.closed_at is not null and f.issue_category != 'epic'
group by l.label_name
having count(*) >= 10
order by median_days_to_close desc
limit 15
```

- [ ] **Step 3: Build**

```bash
cd transform && dbtf build -s age_distribution close_by_label --profiles-dir . --target dev --static-analysis off
```

Expected: 2 models created, 0 errors.

- [ ] **Step 4: Commit**

```bash
git add transform/models/dashboard/
git commit -m "Add dashboard age distribution and close-by-label models"
```

---

## Task 5: Create triage, epic, and issue models

**Files:**
- Create: `transform/models/dashboard/triage_health.sql`
- Create: `transform/models/dashboard/epic_list.sql`
- Create: `transform/models/dashboard/open_issues_table.sql`
- Create: `transform/models/dashboard/issues.sql`
- Create: `transform/models/dashboard/open_by_category.sql`

- [ ] **Step 1: Create `triage_health.sql`**

Source: `dashboard/prefab/queries/triage_health.sql` — most complete version; superset of marimo/observable/evidence triage queries.

```sql
select
    count(*) as total_open,
    round(count(case when is_labeled then 1 end)::float / count(*) * 100, 0) as pct_labeled,
    round(count(case when is_assigned then 1 end)::float / count(*) * 100, 0) as pct_assigned,
    round(count(case when has_milestone then 1 end)::float / count(*) * 100, 0) as pct_milestoned,
    round(count(case when issue_category != 'other' then 1 end)::float / count(*) * 100, 0) as pct_typed,
    count(case when not is_labeled then 1 end) as unlabeled_count,
    count(case when not is_assigned then 1 end) as unassigned_count
from {{ ref('fct_issues') }}
where state = 'OPEN' and issue_category != 'epic'
```

- [ ] **Step 2: Create `epic_list.sql`**

Source: `dashboard/prefab/queries/epic_list.sql`.

```sql
select
    issue_number,
    title,
    state,
    created_at,
    closed_at,
    reactions_total_count,
    comments_total_count
from {{ ref('fct_issues') }}
where issue_category = 'epic'
order by state desc, issue_number
```

- [ ] **Step 3: Create `open_issues_table.sql`**

Source: `dashboard/prefab/queries/open_issues_table.sql`.

```sql
select
    issue_number as "#",
    title,
    issue_category as type,
    round(datediff('day', created_at, current_date), 0) as age_days,
    reactions_total_count as reactions,
    comments_total_count as comments,
    coalesce(milestone_title, '') as milestone
from {{ ref('fct_issues') }}
where state = 'OPEN' and issue_category != 'epic'
order by created_at asc
limit 50
```

- [ ] **Step 4: Create `issues.sql`**

Source: `dashboard/evidence/queries/issues.sql` — full issue dump used by the Evidence source connector.

```sql
select
    issue_number,
    title,
    state,
    issue_category,
    created_at,
    closed_at,
    hours_to_close,
    hours_to_first_response,
    reactions_total_count,
    comments_total_count,
    milestone_title,
    is_labeled,
    is_assigned,
    has_milestone,
    author_login
from {{ ref('fct_issues') }}
order by issue_number desc
```

- [ ] **Step 5: Create `open_by_category.sql`**

Source: `dashboard/evidence/queries/open_by_category.sql`.

```sql
select
    issue_category,
    count(*) as count
from {{ ref('fct_issues') }}
where state = 'OPEN' and issue_category != 'epic'
group by issue_category
order by count desc
```

- [ ] **Step 6: Build**

```bash
cd transform && dbtf build -s triage_health epic_list open_issues_table issues open_by_category --profiles-dir . --target dev --static-analysis off
```

Expected: 5 models created, 0 errors.

- [ ] **Step 7: Commit**

```bash
git add transform/models/dashboard/
git commit -m "Add dashboard triage, epic, issues, and category models"
```

---

## Task 6: Create workload, community, leaderboard, and burndown models

**Files:**
- Create: `transform/models/dashboard/assignee_workload.sql`
- Create: `transform/models/dashboard/community_priorities.sql`
- Create: `transform/models/dashboard/leaderboard.sql`
- Create: `transform/models/dashboard/milestone_burndown_weekly.sql`

- [ ] **Step 1: Create `assignee_workload.sql`**

Source: `dashboard/prefab/queries/assignee_workload.sql` (identical in mviz and marimo).

```sql
select
    a.assignee_login,
    count(*) as open_issues,
    count(case when f.issue_category = 'bug' then 1 end) as bugs,
    count(case when f.issue_category = 'enhancement' then 1 end) as enhancements
from {{ ref('stg_issue_assignees') }} a
inner join {{ ref('fct_issues') }} f on a.issue_dlt_id = f.issue_dlt_id
where f.state = 'OPEN' and f.issue_category != 'epic'
group by a.assignee_login
order by open_issues desc
limit 15
```

- [ ] **Step 2: Create `community_priorities.sql`**

Source: `dashboard/prefab/queries/community_priorities.sql` — richest version (includes `issue_category`).

```sql
select
    issue_number,
    title,
    issue_category,
    reactions_total_count,
    comments_total_count,
    round(datediff('day', created_at, current_date), 0) as age_days
from {{ ref('fct_issues') }}
where state = 'OPEN' and reactions_total_count > 0 and issue_category != 'epic'
order by reactions_total_count desc
limit 10
```

- [ ] **Step 3: Create `leaderboard.sql`**

Source: `dashboard/prefab/queries/leaderboard.sql`.

```sql
select
    author_login,
    count(*) as issues_closed
from {{ ref('fct_issues') }}
where state = 'CLOSED' and issue_category != 'epic'
group by author_login
order by issues_closed desc
limit 15
```

- [ ] **Step 4: Create `milestone_burndown_weekly.sql`**

Source: `dashboard/prefab/queries/milestone_burndown.sql` — a dashboard-specific filter on top of the existing `milestone_burndown` metric model (weekly granularity, open milestones only).

```sql
select
    strftime(date_day, '%Y-%m-%d') as date_day,
    milestone_title,
    open_at_date
from {{ ref('milestone_burndown') }}
where date_day::date = date_trunc('week', date_day::date)
  and milestone_title in (
      select distinct milestone_title
      from {{ ref('dim_milestones') }}
      where milestone_state = 'OPEN'
  )
order by milestone_title, date_day
```

- [ ] **Step 5: Build**

```bash
cd transform && dbtf build -s assignee_workload community_priorities leaderboard milestone_burndown_weekly --profiles-dir . --target dev --static-analysis off
```

Expected: 4 models created, 0 errors.

- [ ] **Step 6: Commit**

```bash
git add transform/models/dashboard/
git commit -m "Add dashboard workload, community, leaderboard, and burndown models"
```

---

## Task 7: Create ggsql-specific models

**Files:**
- Create: `transform/models/dashboard/issues_opened_per_week.sql`
- Create: `transform/models/dashboard/open_vs_closed_by_category.sql`
- Create: `transform/models/dashboard/top_authors.sql`

Note: ggsql queries 03 (`03_median_hours_to_first_response.sql`) and 04 (`04_bug_fix_velocity.sql`) already reference existing dbt models (`response_time_trends`, `bug_fix_velocity`) — no new models needed for those.

- [ ] **Step 1: Create `issues_opened_per_week.sql`**

Source: SQL portion of `dashboard/ggsql/queries/01_issues_opened_per_week.sql` (strip the `VISUALISE/DRAW/LABEL` clauses).

```sql
select
    date_trunc('week', created_at) as week,
    count(*) as issues_opened
from {{ ref('fct_issues') }}
group by week
order by week
```

- [ ] **Step 2: Create `open_vs_closed_by_category.sql`**

Source: SQL portion of `dashboard/ggsql/queries/02_open_vs_closed_by_category.sql`.

```sql
select
    issue_category,
    state,
    count(*) as n
from {{ ref('fct_issues') }}
group by issue_category, state
```

- [ ] **Step 3: Create `top_authors.sql`**

Source: SQL portion of `dashboard/ggsql/queries/05_top_authors.sql`.

```sql
select
    author_login,
    count(*) as issues_opened
from {{ ref('fct_issues') }}
where author_login is not null
group by author_login
order by issues_opened desc
limit 15
```

- [ ] **Step 4: Build**

```bash
cd transform && dbtf build -s issues_opened_per_week open_vs_closed_by_category top_authors --profiles-dir . --target dev --static-analysis off
```

Expected: 3 models created, 0 errors.

- [ ] **Step 5: Commit**

```bash
git add transform/models/dashboard/
git commit -m "Add ggsql-specific dashboard models"
```

---

## Task 8: Full dashboard layer build + static analysis

- [ ] **Step 1: Build all 21 dashboard models with static analysis**

```bash
cd transform && dbtf build -s "models/dashboard/*" --profiles-dir . --target dev --static-analysis strict
```

Expected: 21 models, 0 errors. If static analysis flags issues, fix the specific model before continuing.

- [ ] **Step 2: Run existing tests to confirm nothing broke**

```bash
cd transform && dbtf test --profiles-dir . --target dev
```

Expected: all tests pass.

- [ ] **Step 3: Commit if any fixes were made during static analysis**

```bash
git add transform/models/dashboard/
git commit -m "Fix static analysis issues in dashboard models"
```

---

## Task 9: Add exposures

**Files:**
- Create: `transform/models/dashboard/_exposures.yml`

- [ ] **Step 1: Create `_exposures.yml`**

```yaml
version: 2

exposures:
  - name: prefab_issue_health
    type: dashboard
    maturity: high
    url: https://dbt-labs.github.io/fusion_issue_analysis/
    description: Primary Prefab dashboard — dbt-fusion issue health metrics
    depends_on:
      - ref('summary_kpis')
      - ref('cumulative_flow')
      - ref('age_distribution')
      - ref('response_pctiles')
      - ref('bug_velocity')
      - ref('enh_velocity')
      - ref('close_by_label')
      - ref('triage_health')
      - ref('epic_list')
      - ref('assignee_workload')
      - ref('community_priorities')
      - ref('open_issues_table')
      - ref('leaderboard')
      - ref('milestone_burndown_weekly')
    owner:
      email: anders.swanson@dbtlabs.com

  - name: prefab_myspace
    type: dashboard
    maturity: low
    description: Prefab MySpace-themed dashboard (bakeoff)
    depends_on:
      - ref('summary_kpis')
      - ref('cumulative_flow')
      - ref('response_pctiles')
      - ref('community_priorities')
      - ref('assignee_workload')
    owner:
      email: anders.swanson@dbtlabs.com

  - name: mviz_dashboard
    type: dashboard
    maturity: low
    description: mviz + Vega-Lite dashboard (bakeoff)
    depends_on:
      - ref('summary_kpis')
      - ref('cumulative_flow')
      - ref('bug_velocity')
      - ref('enh_velocity')
      - ref('response_pctiles')
      - ref('age_distribution')
      - ref('close_by_label')
      - ref('assignee_workload')
      - ref('community_priorities')
    owner:
      email: anders.swanson@dbtlabs.com

  - name: marimo_dashboard
    type: dashboard
    maturity: low
    description: Marimo dashboard (bakeoff)
    depends_on:
      - ref('summary_kpis')
      - ref('velocity')
      - ref('weekly_flow')
      - ref('triage_health')
      - ref('community_priorities')
      - ref('assignee_workload')
    owner:
      email: anders.swanson@dbtlabs.com

  - name: observable_dashboard
    type: dashboard
    maturity: low
    description: Observable Framework dashboard (bakeoff)
    depends_on:
      - ref('summary_kpis')
      - ref('velocity')
      - ref('weekly_flow')
      - ref('triage_health')
      - ref('community_priorities')
    owner:
      email: anders.swanson@dbtlabs.com

  - name: evidence_dashboard
    type: dashboard
    maturity: low
    description: Evidence.dev dashboard (bakeoff)
    depends_on:
      - ref('issues')
      - ref('open_by_category')
      - ref('triage_health')
      - ref('weekly_flow')
    owner:
      email: anders.swanson@dbtlabs.com

  - name: ggsql_dashboard
    type: dashboard
    maturity: low
    description: ggsql + Vega-Lite dashboard (bakeoff)
    depends_on:
      - ref('issues_opened_per_week')
      - ref('open_vs_closed_by_category')
      - ref('response_time_trends')
      - ref('bug_fix_velocity')
      - ref('top_authors')
    owner:
      email: anders.swanson@dbtlabs.com
```

- [ ] **Step 2: Verify dbt parses exposures**

```bash
cd transform && dbtf parse --profiles-dir . --target dev
```

Expected: no errors, 7 exposures registered.

- [ ] **Step 3: Commit**

```bash
git add transform/models/dashboard/_exposures.yml
git commit -m "Add dbt exposures for all dashboard frameworks"
```

---

## Task 10: Update prefab `app.py`

**Files:**
- Modify: `dashboard/prefab/app.py`

The current app.py uses a `load_sql(name)` helper that reads from `dashboard/prefab/queries/<name>.sql`. Replace every `load_sql("x")` call with the inline string `"SELECT * FROM x"`. Remove the `load_sql` helper, `QUERIES_DIR` constant, and `HERE` constant. The `query()` function and DB path logic stay unchanged.

Also note: the `milestone_burndown` query becomes `"SELECT * FROM milestone_burndown_weekly"` (the new model name).

- [ ] **Step 1: Update the top of `app.py`**

Remove these lines:
```python
HERE = os.path.dirname(os.path.abspath(__file__))
QUERIES_DIR = os.path.join(HERE, "queries")


def load_sql(name: str) -> str:
    with open(os.path.join(QUERIES_DIR, f"{name}.sql")) as f:
        return f.read()
```

- [ ] **Step 2: Replace all `load_sql(...)` calls**

Replace each `query(load_sql("name"))` call in the data-loading section (lines 54–128) with `query("SELECT * FROM name")`:

```python
summary_cards = query("SELECT * FROM summary_kpis")[0]
cumulative_flow = query("SELECT * FROM cumulative_flow")
age_dist = query("SELECT * FROM age_distribution")
response_pctiles = query("SELECT * FROM response_pctiles")
bug_velocity = query("SELECT * FROM bug_velocity")
enh_velocity = query("SELECT * FROM enh_velocity")
close_by_label = query("SELECT * FROM close_by_label")
triage = query("SELECT * FROM triage_health")[0]
epic_list = query("SELECT * FROM epic_list")
assignee_workload = query("SELECT * FROM assignee_workload")
community_priorities = query("SELECT * FROM community_priorities")
burndown_data = query("SELECT * FROM milestone_burndown_weekly")
open_issues_table = query("SELECT * FROM open_issues_table")
leaderboard = query("SELECT * FROM leaderboard")
```

- [ ] **Step 3: Verify the dashboard exports without errors**

```bash
uv run prefab export dashboard/prefab/app.py -o /tmp/prefab_test.html
```

Expected: `/tmp/prefab_test.html` created with no Python errors. Open in browser to spot-check charts load.

- [ ] **Step 4: Commit**

```bash
git add dashboard/prefab/app.py
git commit -m "prefab app.py: SELECT * from dbt dashboard models"
```

---

## Task 11: Update prefab `app_myspace.py`

**Files:**
- Modify: `dashboard/prefab/app_myspace.py`

`app_myspace.py` already has inline SQL (no `load_sql` helper). Replace each SQL string with `"SELECT * FROM <model_name>"`.

The queries it uses: `summary_kpis` (the large multi-CTE block), `cumulative_flow` (simpler version — use the canonical `cumulative_flow` which is a superset), `response_pctiles` (p50 only used, but `response_pctiles` returns p25/p50/p75 — that's fine), `community_priorities`, `assignee_workload`.

- [ ] **Step 1: Replace inline SQL blocks**

Find each `query("""...""")` call and replace with the appropriate `query("SELECT * FROM <model>")`:

```python
summary_cards = query("SELECT * FROM summary_kpis")[0]

cumulative_flow = query("SELECT * FROM cumulative_flow")

response_pctiles = query("SELECT * FROM response_pctiles")

community_priorities = query("SELECT * FROM community_priorities")

assignee_workload = query("SELECT * FROM assignee_workload")
```

- [ ] **Step 2: Verify export**

```bash
uv run prefab export dashboard/prefab/app_myspace.py -o /tmp/myspace_test.html
```

Expected: no errors, HTML file created.

- [ ] **Step 3: Commit**

```bash
git add dashboard/prefab/app_myspace.py
git commit -m "prefab app_myspace.py: SELECT * from dbt dashboard models"
```

---

## Task 12: Update mviz `generate_data.py`

**Files:**
- Modify: `dashboard/mviz/generate_data.py`

Same pattern as prefab: remove `load_sql` helper + `QUERIES_DIR`, replace all `load_sql("name")` calls with inline `"SELECT * FROM name"` strings.

MViz uses: `summary` → `summary_kpis`, `cumulative_flow`, `bug_velocity`, `enh_velocity`, `response_pctiles`, `age_distribution`, `close_by_label`, `assignee_workload`, `community_priorities`.

- [ ] **Step 1: Remove the `load_sql` helper and `QUERIES_DIR`**

Remove these lines:
```python
HERE = os.path.dirname(__file__)
DATA_DIR = os.path.join(HERE, "data")
QUERIES_DIR = os.path.join(HERE, "queries")
...
def load_sql(name: str) -> str:
    with open(os.path.join(QUERIES_DIR, f"{name}.sql")) as f:
        return f.read()
```

Keep `DATA_DIR` (still needed for JSON output).

- [ ] **Step 2: Replace all `load_sql("name")` calls**

```python
summary = query(con, "SELECT * FROM summary_kpis")[0]
# ...
write_json("cumulative_flow.json", query(con, "SELECT * FROM cumulative_flow"))
write_json("response_pctiles.json", query(con, "SELECT * FROM response_pctiles"))
write_json("close_by_label.json", query(con, "SELECT * FROM close_by_label"))
write_json("assignee_workload.json", query(con, "SELECT * FROM assignee_workload"))
write_json("community_priorities.json", query(con, "SELECT * FROM community_priorities"))
```

For the velocity merge block, replace the two `load_sql` calls:
```python
bug_velocity = query(con, "SELECT * FROM bug_velocity")
enh_velocity = query(con, "SELECT * FROM enh_velocity")
```

For age distribution:
```python
age_dist = query(con, "SELECT * FROM age_distribution")
```

For the KPI split out from summary:
```python
summary = query(con, "SELECT * FROM summary_kpis")[0]
net_flow = summary["closed_4w"] - summary["opened_4w"]
median_close = summary["rolling_median_close_days"]   # NOTE: column renamed from median_close_days
sla_pct = summary["pct_responded_48h"]
```

- [ ] **Step 3: Verify**

```bash
uv run python3 dashboard/mviz/generate_data.py
```

Expected: JSON files written to `dashboard/mviz/data/`, no errors.

- [ ] **Step 4: Commit**

```bash
git add dashboard/mviz/generate_data.py
git commit -m "mviz generate_data.py: SELECT * from dbt dashboard models"
```

---

## Task 13: Update marimo `app.py`

**Files:**
- Modify: `dashboard/marimo/app.py`

Marimo has two issues to fix:
1. Hardcoded DB path (`'/Users/dataders/Developer/fusion_issue_analysis/data/fusion_issues.duckdb'`) — must use env var pattern matching other dashboards.
2. `load_sql()` helper reading from `queries/` — replace with inline SQL strings.
3. Column name: `summary['median_close_days']` → `summary['rolling_median_close_days']`.

- [ ] **Step 1: Replace the DB connection cell**

Replace the cell containing the hardcoded path and `load_sql` helper with two cells. The first cell sets up the DB path (note: `os` is already imported in the first cell of `app.py` — if not, add `import os` here):

```python
@app.cell
def _():
    import os
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    DB_PATH = "md:fusion_issues" if os.environ.get("MOTHERDUCK_TOKEN") else os.path.join(PROJECT_ROOT, "data", "fusion_issues.duckdb")
    return (DB_PATH, PROJECT_ROOT)

@app.cell
def _(DB_PATH, PROJECT_ROOT, duckdb):
    def query(sql):
        con = duckdb.connect(DB_PATH, read_only=True)
        if not DB_PATH.startswith("md:"):
            con.execute(f"SET file_search_path = '{PROJECT_ROOT}/transform'")
        df = con.execute(sql).fetchdf()
        con.close()
        return df
    summary = query("SELECT * FROM summary_kpis").iloc[0]
    return query, summary
```

- [ ] **Step 2: Update all remaining `load_sql` calls**

Replace each `query(load_sql("name"))` throughout the file:

```python
flow_df = query("SELECT * FROM weekly_flow")
vel_df = query("SELECT * FROM velocity")
triage = query("SELECT * FROM triage_health").iloc[0]
top = query("SELECT * FROM community_priorities")
workload = query("SELECT * FROM assignee_workload")
```

- [ ] **Step 3: Fix the column name reference**

Find `summary['median_close_days']` and change to `summary['rolling_median_close_days']`.

- [ ] **Step 4: Remove the dead `load_sql` cell entirely**

Delete the `@app.cell` block that defines `load_sql` and `_QUERIES_DIR`.

- [ ] **Step 5: Verify**

```bash
cd /path/to/repo && uv run marimo run dashboard/marimo/app.py
```

Expected: app starts without errors, charts display data.

- [ ] **Step 6: Commit**

```bash
git add dashboard/marimo/app.py
git commit -m "marimo app.py: SELECT * from dbt models; fix hardcoded DB path"
```

---

## Task 14: Update observable data loader

**Files:**
- Modify: `dashboard/observable/src/data/summary.json.sh`

The data loader uses a Python heredoc with `load_sql()`. Replace with inline SQL strings. Also rename the `median_close_days` key since `summary_kpis` returns `rolling_median_close_days` — the JS template in `src/index.md` uses `summary.median_close_days`, so either rename in the loader output or update the template. Update the template (cleaner than aliasing in the loader).

- [ ] **Step 1: Replace the Python heredoc in `summary.json.sh`**

```bash
uv --directory "$REPO_ROOT" run python3 - <<'PYEOF'
import sys, json, duckdb, os
REPO_ROOT = os.environ['REPO_ROOT']

if os.environ.get("MOTHERDUCK_TOKEN"):
    DB_PATH = "md:fusion_issues"
else:
    DB_PATH = f'{REPO_ROOT}/data/fusion_issues.duckdb'

con = duckdb.connect(DB_PATH, read_only=True)
if not DB_PATH.startswith("md:"):
    con.execute(f"SET file_search_path = '{REPO_ROOT}/transform'")

summary = con.execute("SELECT * FROM summary_kpis").fetchdf().to_dict('records')[0]
flow    = con.execute("SELECT * FROM weekly_flow").fetchdf().to_dict('records')
velocity = con.execute("SELECT * FROM velocity").fetchdf().to_dict('records')
triage  = con.execute("SELECT * FROM triage_health").fetchdf().to_dict('records')[0]
top_issues = con.execute("SELECT * FROM community_priorities").fetchdf().to_dict('records')

json.dump({"summary": summary, "flow": flow, "velocity": velocity, "triage": triage, "top_issues": top_issues}, sys.stdout)
PYEOF
```

- [ ] **Step 2: Update `src/index.md` column references**

In `dashboard/observable/src/index.md`, find all references to `summary.median_close_days` and replace with `summary.rolling_median_close_days`. Also check for any `top_issues` column references that differ from `community_priorities` schema (e.g., `reactions_total_count` is present in the model).

- [ ] **Step 3: Verify the data loader runs**

```bash
cd dashboard/observable && bash src/data/summary.json.sh > /tmp/obs_test.json
```

Expected: valid JSON written to stdout with `summary`, `flow`, `velocity`, `triage`, `top_issues` keys.

- [ ] **Step 4: Commit**

```bash
git add dashboard/observable/src/data/summary.json.sh dashboard/observable/src/index.md
git commit -m "observable: SELECT * from dbt models; fix MotherDuck support"
```

---

## Task 15: Update Evidence source connector

**Files:**
- Modify: `dashboard/evidence/sources/fusion/issues.sql`

Evidence's `pages/index.md` uses inline SQL querying `from issues`, which is the source defined by `sources/fusion/issues.sql`. Update that source file to pull from the new dbt `issues` model.

- [ ] **Step 1: Replace `sources/fusion/issues.sql`**

```sql
SELECT * FROM issues
```

- [ ] **Step 2: Verify Evidence builds**

```bash
cd dashboard/evidence && npm run build 2>&1 | tail -20
```

Expected: build succeeds. If there are column-not-found errors in `pages/index.md` inline SQL, the `issues` dbt model may be missing a column — check `transform/models/dashboard/issues.sql` and add any needed columns.

- [ ] **Step 3: Commit**

```bash
git add dashboard/evidence/sources/fusion/issues.sql
git commit -m "evidence: source issues table from dbt issues model"
```

---

## Task 16: Update ggsql query files

**Files:**
- Modify: `dashboard/ggsql/queries/01_issues_opened_per_week.sql`
- Modify: `dashboard/ggsql/queries/02_open_vs_closed_by_category.sql`
- Modify: `dashboard/ggsql/queries/05_top_authors.sql`

ggsql parses `.sql` files for `VISUALISE/DRAW/LABEL` DSL clauses. Replace the SQL portion with `SELECT * FROM <model>` while keeping the DSL clauses unchanged. Queries 03 and 04 already reference existing dbt models — leave them untouched.

- [ ] **Step 1: Update `01_issues_opened_per_week.sql`**

```sql
-- title: Issues opened per week
-- blurb: Weekly count of newly-opened Fusion issues.
SELECT * FROM issues_opened_per_week
VISUALISE week AS x, issues_opened AS y
DRAW line
LABEL title => 'Issues opened per week'
```

- [ ] **Step 2: Update `02_open_vs_closed_by_category.sql`**

```sql
-- title: Open vs closed by category
-- blurb: Composition of current backlog by derived issue_category.
SELECT * FROM open_vs_closed_by_category
VISUALISE issue_category AS x, n AS y, state AS fill
DRAW bar
LABEL title => 'Issues by category and state'
```

- [ ] **Step 3: Update `05_top_authors.sql`**

```sql
-- title: Top authors by issues opened
-- blurb: Heaviest issue-reporters across the project.
SELECT * FROM top_authors
VISUALISE author_login AS y, issues_opened AS x
DRAW bar
LABEL title => 'Top 15 issue authors'
```

- [ ] **Step 4: Verify ggsql builds**

```bash
cd /path/to/repo && uv run python3 dashboard/ggsql/build.py
```

Expected: `dashboard/ggsql/index.html` written with 5 charts, no errors.

- [ ] **Step 5: Commit**

```bash
git add dashboard/ggsql/queries/
git commit -m "ggsql: SELECT * from dbt models for queries 01, 02, 05"
```

---

## Task 17: Delete all `queries/` directories

All `queries/` directories for Python/JS frameworks are now dead code. The ggsql `queries/` directory is already updated (not deleted).

- [ ] **Step 1: Delete query directories**

```bash
rm -rf dashboard/prefab/queries/
rm -rf dashboard/mviz/queries/
rm -rf dashboard/marimo/queries/
rm -rf dashboard/observable/queries/
rm -rf dashboard/evidence/queries/
```

- [ ] **Step 2: Verify nothing references the deleted paths**

```bash
grep -r "queries/" dashboard/ --include="*.py" --include="*.sh" --include="*.md" --include="*.js"
```

Expected: only references in `dashboard/ggsql/` (which we kept) or none.

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "Delete dead queries/ directories — all SQL lives in dbt"
```

---

## Task 18: Final integration check and PR

- [ ] **Step 1: Full dbt build including static analysis**

```bash
cd transform && dbtf build --profiles-dir . --target dev --static-analysis strict
```

Expected: all models build, 0 errors.

- [ ] **Step 2: Export prefab dashboards (CI requirement)**

```bash
uv run prefab export dashboard/prefab/app.py -o /tmp/final_app.html
uv run prefab export dashboard/prefab/app_myspace.py -o /tmp/final_myspace.html
```

Expected: both export without errors.

- [ ] **Step 3: Run full dbt test suite**

```bash
cd transform && dbtf test --profiles-dir . --target dev
```

Expected: all tests pass.

- [ ] **Step 4: Push branch and open PR**

```bash
git push -u origin feat/dashboard-bakeoff
```

Open PR against `main`. Include the dashboard preview link in the body per CLAUDE.md conventions:

```
## Dashboard Preview
🔗 [Preview link](https://dbt-labs.github.io/fusion_issue_analysis/) (auto-posted by CI)

Closes #56
```
