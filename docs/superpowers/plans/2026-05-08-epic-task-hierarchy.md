# Epic / Task hierarchy modeling — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `is_epic`, `has_epic_parent`, `is_orphan` columns to `fct_issues`; create `fct_epics` and `fct_milestones` marts; add three audit views and an `epic_burndown` model — so the warehouse can answer "is every issue attributed to an epic, and is every epic attributed to a milestone?"

**Architecture:**
- Pull `issueType { name }` and `parent { number, title, issueType { name } }` from GitHub GraphQL.
- Plumb both through `stg_issues` → `fct_issues`.
- Build `fct_epics` (one row per Epic, with child rollups) and `fct_milestones` (one row per milestone, with epic/task counts) on top.
- Layer audit views and per-epic burndown on top of those marts using the same date-spine reconstruction technique already used by `metrics/milestone_burndown.sql`.

**Tech Stack:**
- Python `uv` for the extract (`extract/run.py`)
- dlt for GraphQL→parquet/MotherDuck loading
- dbt Fusion (`dbtf`) over DuckDB / MotherDuck
- `--static-analysis strict` is enforced

**Spec:** `docs/superpowers/specs/2026-05-08-epic-task-hierarchy-design.md`

---

## File map

**Extract:**
- Modify: `extract/github/queries.py` — add `issueType` and `parent` to `ISSUES_QUERY`.

**Staging:**
- Modify: `transform/models/staging/_sources.yml` — declare 4 new raw columns.
- Modify: `transform/models/staging/stg_issues.sql` — passthrough `issue_type`, `parent_number`, `parent_title`, `parent_issue_type`.

**Marts:**
- Modify: `transform/models/marts/fct_issues.sql` — passthrough `issue_type` + 4 milestone fields + 3 parent fields; add `is_epic`, `has_epic_parent`, `is_orphan`; broaden `issue_category`.
- Create: `transform/models/marts/_schema.yml` — declare new columns and tests for `fct_issues`, `fct_epics`, `fct_milestones`.
- Create: `transform/models/marts/fct_epics.sql` — one row per Epic.
- Create: `transform/models/marts/fct_milestones.sql` — one row per milestone with rollups.

**Metrics & audits:**
- Create: `transform/models/metrics/audit_orphan_issues.sql`
- Create: `transform/models/metrics/audit_epics_without_milestone.sql`
- Create: `transform/models/metrics/audit_tasks_without_milestone.sql`
- Create: `transform/models/metrics/epic_burndown.sql`
- Modify: `transform/models/metrics/milestone_burndown.sql` — join `fct_milestones` for `milestone_state`, `is_overdue`, `total_issues`.

**Cross-model integrity:**
- Create: `transform/tests/audit_epics_orphan_count_matches.sql` — singular test that `audit_epics_without_milestone` rowcount equals `count(*) filter (is_orphan_epic)` on `fct_epics`.

**Verification commands** (used throughout):
- Local dev build: `cd transform && dbtf build --profiles-dir . --target dev`
- Prod static-analysis build: `cd transform && dbtf build --profiles-dir . --target prod --static-analysis strict`
- Tests only: `cd transform && dbtf test --profiles-dir . --target dev`
- Single model: `cd transform && dbtf build --profiles-dir . --target dev --select <model_name>`

---

## Task 0: Create feature branch

Per `CLAUDE.md`, never push directly to `main`. Branch first.

- [ ] **Step 1: Create branch**

```bash
git checkout -b feat/epic-task-hierarchy
```

- [ ] **Step 2: Verify clean state**

```bash
git status
```

Expected: `On branch feat/epic-task-hierarchy. nothing to commit, working tree clean.`

---

## Task 1: Pull `issueType` and `parent` from GitHub GraphQL

Both extract changes ship together because they require one extract re-run. The query body is reused for `pullRequests` (via the `%s` template substitution at line 13), where `issueType` and `parent` are not valid fields. Existing convention uses simple inline guarding — verify the same approach works.

**Files:**
- Modify: `extract/github/queries.py:10-95`

- [ ] **Step 1: Inspect existing query reuse pattern**

Read `extract/github/queries.py:10-95` and `extract/github/helpers.py` lines that use `ISSUES_QUERY % node_type` (around `helpers.py:88`). Confirm `node_type` is one of `"issues"` or `"pullRequests"`.

- [ ] **Step 2: Check whether a previous attempt already added `issueType`**

```bash
grep -n -i "issuetype\|parent" extract/github/queries.py
```

If the file already has `issueType { name }` *and* a `parent { ... }` block, skip to Task 2. Otherwise, continue.

- [ ] **Step 3: Add `issueType` and `parent` to the issue node**

In `extract/github/queries.py:ISSUES_QUERY`, add inside the issue node selection (alongside `state`, `closed`, etc., before the `labels` block at line 32):

```graphql
        issueType { name }
        parent {
          number
          title
          issueType { name }
        }
```

`issueType` and `parent` are only valid on `Issue`, not `PullRequest`. The existing `%s` substitution swaps `issues` for `pullRequests` at the connection level, so the inner fields apply to both. To prevent GraphQL errors when the same body runs against `pullRequests`, wrap both fields in an inline fragment:

```graphql
        ... on Issue {
          issueType { name }
          parent {
            number
            title
            issueType { name }
          }
        }
```

This is the cleanest way to scope issue-only fields in a body shared with `pullRequests`. (Inline fragments on the same type are a no-op syntactically but resolve the field-validity issue.)

- [ ] **Step 4: Manual smoke check of the query**

```bash
cd /Users/dataders/Developer/fusion_issue_analysis
uv run python -c "from extract.github.queries import ISSUES_QUERY; print(ISSUES_QUERY % 'issues')" | head -40
```

Expected: see `... on Issue { issueType { name } parent { ... } }` block in the output. No syntax errors.

- [ ] **Step 5: Commit**

```bash
git add extract/github/queries.py
git commit -m "Pull issueType and parent from GitHub GraphQL

Adds issueType { name } and parent { number, title, issueType { name } }
to ISSUES_QUERY, scoped via inline fragment on Issue so the same query
body still works for pullRequests."
```

---

## Task 2: Declare new raw columns in `_sources.yml`

dlt's GraphQL flattening produces `issue_type__name`, `parent__number`, `parent__title`, `parent__issue_type__name`. Static analysis needs them declared.

**Files:**
- Modify: `transform/models/staging/_sources.yml`

- [ ] **Step 1: Read current `_sources.yml`**

Read `transform/models/staging/_sources.yml` to find the `issues` table block under `raw_github`.

- [ ] **Step 2: Add column declarations**

Under the `issues` table's `columns:` list, add (preserving existing entries):

```yaml
      - name: issue_type__name
        description: GitHub native Issue Type (Bug | Feature | Task | Epic | null)
      - name: parent__number
        description: Parent issue number via GitHub sub-issues
      - name: parent__title
        description: Parent issue title
      - name: parent__issue_type__name
        description: Parent issue's native Issue Type
```

If the `issues` table block does not yet have a `columns:` list, add one. If unsure of the exact YAML shape, model after the `stg_issues` model entry already in this file (which uses `columns:` lists with `name`/`description`).

- [ ] **Step 3: Commit**

```bash
git add transform/models/staging/_sources.yml
git commit -m "Declare issue_type and parent columns on raw_github.issues source"
```

---

## Task 3: Re-run extract to populate the new columns

dlt only writes columns it sees data for. The new columns won't exist until the extract runs once.

**Files:** none changed; this is a data-loading step.

- [ ] **Step 1: Run the extract**

```bash
cd /Users/dataders/Developer/fusion_issue_analysis/extract
uv run python run.py
```

Expected: extract completes without errors. Either a `data/raw/fusion_issues/issues/*.parquet` file is updated, or MotherDuck's `raw_github.issues` is replaced — depending on local config.

- [ ] **Step 2: Verify new columns landed**

For dev (parquet):

```bash
cd /Users/dataders/Developer/fusion_issue_analysis
uv run python -c "import duckdb; con = duckdb.connect(); con.execute(\"select count(*) c, count(issue_type__name) c_type, count(parent__number) c_parent from read_parquet('data/raw/fusion_issues/issues/*.parquet')\"); print(con.fetchall())"
```

Expected: `c` > 0, `c_type` > 0 (most issues have a type now), `c_parent` ≥ 0 (at least some sub-issues exist in dbt-fusion).

If `c_type` = 0 or `c_parent` is suspiciously low, the GraphQL change in Task 1 is wrong — back to that task.

- [ ] **Step 3: No commit (data files are gitignored)**

---

## Task 4: Passthrough new columns in `stg_issues`

**Files:**
- Modify: `transform/models/staging/stg_issues.sql`

- [ ] **Step 1: Read current `stg_issues.sql`**

Read `transform/models/staging/stg_issues.sql` lines 1-33. Confirm the `renamed` CTE structure.

- [ ] **Step 2: Add passthroughs**

Inside the `renamed` CTE's select, after the existing `closed_at` column (line 28), add:

```sql
        issue_type__name as issue_type,
        parent__number as parent_number,
        parent__title as parent_title,
        parent__issue_type__name as parent_issue_type
```

- [ ] **Step 3: Build stg_issues alone**

```bash
cd transform && dbtf build --profiles-dir . --target dev --select stg_issues
```

Expected: builds clean. If a column-not-found error fires, the extract didn't actually emit that column — re-check Task 3 step 2 column names exactly (note the double underscores from dlt flattening).

- [ ] **Step 4: Spot-check the data**

```bash
cd /Users/dataders/Developer/fusion_issue_analysis
uv run python -c "import duckdb; con = duckdb.connect('data/fusion_issues.duckdb'); print(con.execute('select issue_type, count(*) from main_staging.stg_issues group by 1 order by 2 desc').fetchall())"
```

(If the schema name differs, adjust — e.g., `dbt_dev.stg_issues`. Run `con.execute(\"show tables\").fetchall()` to find it.)

Expected: a small set of issue_type values like `('Task', N)`, `('Bug', N)`, `('Feature', N)`, `(None, N)`.

- [ ] **Step 5: Commit**

```bash
git add transform/models/staging/stg_issues.sql
git commit -m "Passthrough issue_type and parent fields in stg_issues"
```

---

## Task 5: Add new columns to `fct_issues`

This is the biggest single-file change. Bundles three logically-related additions: `issue_type` + milestone passthroughs (Phase 0), parent passthroughs + `has_epic_parent` (Phase 1), `is_epic` + `is_orphan` (Phase 2).

**Files:**
- Modify: `transform/models/marts/fct_issues.sql`

- [ ] **Step 1: Read current `fct_issues.sql`**

Re-read the file end-to-end. Note the existing structure: `issues` CTE, `first_comments`, `first_non_author_comments`, `issue_labels`, `triage_info`, then the final `select` joining them.

- [ ] **Step 2: Update the final select**

Make these edits to the final `select` (around line 43 onward):

(a) Right before `i.reactions_total_count` (~line 55), add:

```sql
    i.issue_type,
    i.milestone_state,
    i.milestone_due_on,
    i.milestone_created_at,
    i.milestone_closed_at,
    i.parent_number,
    i.parent_title,
    i.parent_issue_type,
```

(b) Replace the `-- classification` block (currently lines 81-86) with the broadened version that considers `issue_type` alongside labels:

```sql
    -- classification
    case
        when il.has_epic = 1 then 'epic'
        when i.issue_type = 'Bug' or il.has_bug = 1 then 'bug'
        when i.issue_type in ('Feature', 'Enhancement') or il.has_enhancement = 1 then 'enhancement'
        when i.issue_type = 'Task' then 'task'
        else 'other'
    end as issue_category,
```

(c) After the existing `has_milestone` line (~line 96, the last column before the `from`), add:

```sql
    ,case
        when i.issue_type = 'Task' and lower(i.title) like '%epic%'
        then true else false
    end as is_epic
    ,case
        when i.parent_issue_type = 'Task' and lower(i.parent_title) like '%epic%'
        then true else false
    end as has_epic_parent
    ,case
        when i.state = 'OPEN'
            and not (i.issue_type = 'Task' and lower(i.title) like '%epic%')
            and not (i.parent_issue_type = 'Task' and lower(i.parent_title) like '%epic%')
        then true else false
    end as is_orphan
```

(`is_epic` and `has_epic_parent` are repeated inline inside `is_orphan` rather than referenced because DuckDB's strict static analyzer rejects forward column references in the same select list.)

- [ ] **Step 3: Build fct_issues alone**

```bash
cd transform && dbtf build --profiles-dir . --target dev --select fct_issues
```

Expected: builds clean.

- [ ] **Step 4: Spot-check epic detection**

```bash
cd /Users/dataders/Developer/fusion_issue_analysis
uv run python -c "import duckdb; con = duckdb.connect('data/fusion_issues.duckdb'); rows = con.execute(\"select issue_number, title, issue_type, is_epic from main_marts.fct_issues where is_epic order by issue_number limit 10\").fetchall(); [print(r) for r in rows]"
```

Expected: 5–20+ rows, each with `issue_type='Task'` and 'epic' (case-insensitive) somewhere in the title.

- [ ] **Step 5: Spot-check orphans**

```bash
uv run python -c "import duckdb; con = duckdb.connect('data/fusion_issues.duckdb'); print(con.execute('select count(*) total, sum(is_orphan::int) orphans, sum(is_epic::int) epics, sum(has_epic_parent::int) tasks_w_epic from main_marts.fct_issues').fetchall())"
```

Expected: orphans + epics + tasks_w_epic ≈ open issues; orphans should be a non-zero but not majority count.

- [ ] **Step 6: Commit**

```bash
git add transform/models/marts/fct_issues.sql
git commit -m "Add is_epic, has_epic_parent, is_orphan to fct_issues

Also passes through issue_type, milestone_state/due_on/created_at/closed_at,
and parent_* fields. Broadens issue_category to consider native Issue Type
alongside the EPIC/bug/enhancement labels."
```

---

## Task 6: Create `marts/_schema.yml` with tests for `fct_issues`

This file does not exist yet. Create it scoped to the new columns plus the existing fct_issues primary key.

**Files:**
- Create: `transform/models/marts/_schema.yml`

- [ ] **Step 1: Create the file**

```yaml
version: 2

models:
  - name: fct_issues
    description: One row per GitHub issue from dbt-labs/dbt-fusion, enriched with derived metrics, classification, and parent relationship.
    columns:
      - name: issue_dlt_id
        tests:
          - unique
          - not_null
      - name: issue_number
        tests:
          - unique
          - not_null
      - name: issue_type
        description: GitHub native Issue Type (Bug | Feature | Task | Epic | null)
      - name: is_epic
        description: True when issue_type = 'Task' and 'epic' appears in title (authoritative epic flag; preferred over the legacy label-based has_epic).
        tests:
          - not_null
      - name: has_epic_parent
        description: True when this issue's parent is an epic (parent_issue_type = 'Task' and 'epic' in parent_title).
        tests:
          - not_null
      - name: is_orphan
        description: Open issue that is neither an epic nor has an epic parent.
        tests:
          - not_null
      - name: parent_number
        description: GitHub sub-issue parent's issue number, if any.
        tests:
          - relationships:
              arguments:
                to: ref('fct_issues')
                field: issue_number
              config:
                where: "parent_number is not null"
                severity: warn  # parent may be cross-repo or pre-extract; warn rather than block
```

- [ ] **Step 2: Run tests**

```bash
cd transform && dbtf test --profiles-dir . --target dev --select fct_issues
```

Expected: all tests pass. The `parent_number` relationships test specifically validates that every non-null parent_number resolves to an `issue_number` in `fct_issues`. If it fails, you have cross-repo parents (rare for dbt-fusion); investigate before proceeding.

- [ ] **Step 3: Commit**

```bash
git add transform/models/marts/_schema.yml
git commit -m "Add _schema.yml with tests for new fct_issues columns"
```

---

## Task 7: Create `fct_epics`

**Files:**
- Create: `transform/models/marts/fct_epics.sql`
- Modify: `transform/models/marts/_schema.yml`

- [ ] **Step 1: Write `fct_epics.sql`**

```sql
with epics as (
    select * from {{ ref('fct_issues') }}
    where is_epic
),

child_rollup as (
    select
        parent_number as epic_number,
        count(*)                                    as child_total,
        count(*) filter (where state = 'OPEN')      as child_open,
        count(*) filter (where state = 'CLOSED')    as child_closed
    from {{ ref('fct_issues') }}
    where parent_number is not null
    group by parent_number
)

select
    e.issue_number          as epic_number,
    e.issue_url             as epic_url,
    e.title,
    e.state,
    e.created_at,
    e.closed_at,
    e.milestone_number,
    e.milestone_title,
    e.milestone_state,
    e.milestone_due_on,

    coalesce(c.child_total,  0) as child_total,
    coalesce(c.child_open,   0) as child_open,
    coalesce(c.child_closed, 0) as child_closed,
    case
        when coalesce(c.child_total, 0) = 0 then null
        else c.child_closed::float / c.child_total
    end                         as pct_complete,

    e.milestone_number is not null      as has_milestone,
    case
        when e.state = 'OPEN' and e.milestone_number is null
        then true else false
    end                                 as is_orphan_epic
from epics e
left join child_rollup c
    on e.issue_number = c.epic_number
```

- [ ] **Step 2: Build `fct_epics`**

```bash
cd transform && dbtf build --profiles-dir . --target dev --select fct_epics
```

Expected: builds clean.

- [ ] **Step 3: Add tests to `_schema.yml`**

Append to `transform/models/marts/_schema.yml`:

```yaml
  - name: fct_epics
    description: One row per Epic (Task-typed issue with 'epic' in title), enriched with child counts and milestone attribution.
    columns:
      - name: epic_number
        tests:
          - unique
          - not_null
      - name: child_total
        tests:
          - not_null
      - name: is_orphan_epic
        description: Open epic with no milestone attached.
        tests:
          - not_null
```

- [ ] **Step 4: Run tests**

```bash
cd transform && dbtf test --profiles-dir . --target dev --select fct_epics
```

Expected: pass.

- [ ] **Step 5: Spot-check a known epic**

```bash
cd /Users/dataders/Developer/fusion_issue_analysis
uv run python -c "import duckdb; con = duckdb.connect('data/fusion_issues.duckdb'); rows = con.execute('select epic_number, title, child_total, child_open, child_closed, pct_complete, has_milestone from main_marts.fct_epics order by child_total desc limit 5').fetchall(); [print(r) for r in rows]"
```

Expected: a few epics with sensible child counts; `child_open + child_closed = child_total`.

- [ ] **Step 6: Commit**

```bash
git add transform/models/marts/fct_epics.sql transform/models/marts/_schema.yml
git commit -m "Add fct_epics mart

One row per Epic with child rollups (open/closed/total/pct_complete),
milestone attribution, and is_orphan_epic flag for the audit layer."
```

---

## Task 8: Create `fct_milestones`

**Files:**
- Create: `transform/models/marts/fct_milestones.sql`
- Modify: `transform/models/marts/_schema.yml`

- [ ] **Step 1: Write `fct_milestones.sql`**

```sql
with milestones as (
    select * from {{ ref('dim_milestones') }}
),

issue_rollup as (
    select
        milestone_number,
        count(*)                                  as total_issues,
        count(*) filter (where state = 'OPEN')    as total_open,
        count(*) filter (where state = 'CLOSED')  as total_closed,
        count(*) filter (where is_epic)           as epic_count,
        count(*) filter (where has_epic_parent)   as task_count
    from {{ ref('fct_issues') }}
    where milestone_number is not null
    group by milestone_number
)

select
    m.milestone_number,
    m.milestone_title,
    m.milestone_state,
    m.milestone_due_on,
    m.milestone_created_at,
    m.milestone_closed_at,

    coalesce(r.total_issues,  0) as total_issues,
    coalesce(r.total_open,    0) as total_open,
    coalesce(r.total_closed,  0) as total_closed,
    coalesce(r.epic_count,    0) as epic_count,
    coalesce(r.task_count,    0) as task_count,

    case
        when coalesce(r.total_issues, 0) = 0 then null
        else r.total_closed::float / r.total_issues
    end                          as pct_complete,

    case
        when m.milestone_state = 'OPEN'
            and m.milestone_due_on is not null
            and m.milestone_due_on < current_date
        then true else false
    end                          as is_overdue
from milestones m
left join issue_rollup r
    on m.milestone_number = r.milestone_number
```

- [ ] **Step 2: Build `fct_milestones`**

```bash
cd transform && dbtf build --profiles-dir . --target dev --select fct_milestones
```

Expected: builds clean.

- [ ] **Step 3: Add tests to `_schema.yml`**

Append:

```yaml
  - name: fct_milestones
    description: One row per milestone with rollup of issues, epics, tasks, and overdue flag.
    columns:
      - name: milestone_number
        tests:
          - unique
          - not_null
      - name: total_issues
        tests:
          - not_null
```

- [ ] **Step 4: Run tests**

```bash
cd transform && dbtf test --profiles-dir . --target dev --select fct_milestones
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add transform/models/marts/fct_milestones.sql transform/models/marts/_schema.yml
git commit -m "Add fct_milestones mart with epic/task rollups and is_overdue"
```

---

## Task 9: Audit views

Three thin filters. Build all three together since they share shape.

**Files:**
- Create: `transform/models/metrics/audit_orphan_issues.sql`
- Create: `transform/models/metrics/audit_epics_without_milestone.sql`
- Create: `transform/models/metrics/audit_tasks_without_milestone.sql`

- [ ] **Step 1: Write `audit_orphan_issues.sql`**

```sql
select
    issue_number,
    issue_url,
    title,
    issue_type,
    state,
    created_at,
    (current_date - created_at::date) as age_days
from {{ ref('fct_issues') }}
where is_orphan
order by created_at
```

- [ ] **Step 2: Write `audit_epics_without_milestone.sql`**

```sql
select
    epic_number,
    epic_url,
    title,
    state,
    created_at,
    child_total,
    child_open
from {{ ref('fct_epics') }}
where is_orphan_epic
order by created_at
```

- [ ] **Step 3: Write `audit_tasks_without_milestone.sql`**

```sql
select
    issue_number,
    issue_url,
    title,
    issue_type,
    parent_number,
    parent_title,
    state,
    created_at
from {{ ref('fct_issues') }}
where state = 'OPEN'
  and has_epic_parent
  and milestone_number is null
order by created_at
```

- [ ] **Step 4: Build all three**

```bash
cd transform && dbtf build --profiles-dir . --target dev --select audit_orphan_issues audit_epics_without_milestone audit_tasks_without_milestone
```

Expected: all three build clean.

- [ ] **Step 5: Spot-check counts**

```bash
cd /Users/dataders/Developer/fusion_issue_analysis
uv run python -c "import duckdb; con = duckdb.connect('data/fusion_issues.duckdb'); print('orphan_issues:', con.execute('select count(*) from main_metrics.audit_orphan_issues').fetchone()); print('orphan_epics:', con.execute('select count(*) from main_metrics.audit_epics_without_milestone').fetchone()); print('tasks_no_milestone:', con.execute('select count(*) from main_metrics.audit_tasks_without_milestone').fetchone())"
```

Expected: three counts; non-zero is normal — these audits exist precisely to surface real gaps.

- [ ] **Step 6: Commit**

```bash
git add transform/models/metrics/audit_orphan_issues.sql transform/models/metrics/audit_epics_without_milestone.sql transform/models/metrics/audit_tasks_without_milestone.sql
git commit -m "Add three audit views: orphan issues, orphan epics, tasks without milestone"
```

---

## Task 10: Cross-model integrity test

A singular SQL test that fails when `audit_epics_without_milestone` and `fct_epics.is_orphan_epic` disagree. dbt singular tests pass when the SELECT returns zero rows.

**Files:**
- Create: `transform/tests/audit_epics_orphan_count_matches.sql`

- [ ] **Step 1: Write the test**

```sql
-- Fails when audit_epics_without_milestone rowcount disagrees with
-- fct_epics.is_orphan_epic — i.e. the audit and the fact mart are
-- out of sync.
with audit_n as (
    select count(*) as n from {{ ref('audit_epics_without_milestone') }}
),
fact_n as (
    select count(*) as n from {{ ref('fct_epics') }} where is_orphan_epic
)
select 'mismatch' as failure, audit_n.n as audit_rowcount, fact_n.n as fact_rowcount
from audit_n cross join fact_n
where audit_n.n != fact_n.n
```

- [ ] **Step 2: Run the test**

```bash
cd transform && dbtf test --profiles-dir . --target dev --select audit_epics_orphan_count_matches
```

Expected: pass (returns 0 rows).

- [ ] **Step 3: Commit**

```bash
git add transform/tests/audit_epics_orphan_count_matches.sql
git commit -m "Add singular test linking audit_epics_without_milestone to fct_epics.is_orphan_epic"
```

---

## Task 11: `epic_burndown`

Mirrors the date-spine technique already in `metrics/milestone_burndown.sql`. DuckDB-specific dialect (`generate_series` with `bigint`, `datediff`) is intentional and consistent with the existing burndown model.

**Files:**
- Create: `transform/models/metrics/epic_burndown.sql`

- [ ] **Step 1: Write the model**

```sql
with epic_children as (
    select
        e.epic_number,
        e.title          as epic_title,
        i.issue_number,
        i.created_at,
        i.closed_at
    from {{ ref('fct_epics') }} e
    join {{ ref('fct_issues') }} i
        on i.parent_number = e.epic_number
),

date_spine as (
    select
        ((select min(created_at::date) from epic_children) + (i || ' days')::interval)::date as date_day
    from generate_series(
        0::bigint,
        (select datediff('day', min(created_at::date), current_date)::bigint from epic_children)
    ) as t(i)
),

epics as (
    select distinct epic_number, epic_title from epic_children
)

select
    d.date_day,
    e.epic_number,
    e.epic_title,
    count(case when ec.created_at::date <= d.date_day then 1 end) as cumulative_opened,
    count(case when ec.closed_at::date  <= d.date_day then 1 end) as cumulative_closed,
    count(case when ec.created_at::date <= d.date_day then 1 end)
      - count(case when ec.closed_at::date <= d.date_day then 1 end) as open_at_date
from date_spine d
cross join epics e
left join epic_children ec
    on ec.epic_number = e.epic_number
group by d.date_day, e.epic_number, e.epic_title
```

- [ ] **Step 2: Build**

```bash
cd transform && dbtf build --profiles-dir . --target dev --select epic_burndown
```

Expected: clean. If `generate_series` errors with a type mismatch, see the comment block in `milestone_burndown.sql` lines 18-21 — dbt-fusion strict static analysis only registers the bigint overload.

- [ ] **Step 3: Spot-check**

```bash
cd /Users/dataders/Developer/fusion_issue_analysis
uv run python -c "
import duckdb
con = duckdb.connect('data/fusion_issues.duckdb')
# Most recent date for one epic should equal that epic's child_open in fct_epics.
row = con.execute('''
    with latest as (
        select epic_number, max(date_day) d from main_metrics.epic_burndown group by 1
    )
    select b.epic_number, b.open_at_date, e.child_open
    from latest l
    join main_metrics.epic_burndown b on b.epic_number = l.epic_number and b.date_day = l.d
    join main_marts.fct_epics e on e.epic_number = b.epic_number
    where b.open_at_date != e.child_open
    limit 5
''').fetchall()
print('mismatches:', row)
"
```

Expected: empty list (latest-day burndown matches `fct_epics.child_open`).

- [ ] **Step 4: Commit**

```bash
git add transform/models/metrics/epic_burndown.sql
git commit -m "Add epic_burndown reconstructing per-epic open/closed counts over time"
```

---

## Task 12: Extend `milestone_burndown`

Add a left join to `fct_milestones` to surface `milestone_state`, `is_overdue`, and `total_issues` alongside the existing reconstructed counts.

**Files:**
- Modify: `transform/models/metrics/milestone_burndown.sql`

- [ ] **Step 1: Read the current model**

Read `transform/models/metrics/milestone_burndown.sql` end-to-end. The final select is `select * from burndown where cumulative_opened > 0 order by milestone_title, date_day`.

- [ ] **Step 2: Add the join**

Replace the final select with:

```sql
select
    b.*,
    fm.milestone_state,
    fm.is_overdue,
    fm.total_issues
from burndown b
left join {{ ref('fct_milestones') }} fm
    on b.milestone_title = fm.milestone_title
where b.cumulative_opened > 0
order by b.milestone_title, b.date_day
```

(`burndown` keys on `milestone_title` because that's how the existing model joins; `fct_milestones` is keyed on `milestone_number` but `milestone_title` is unique enough for this reporting layer. If duplicates surface, switch the join to `milestone_number` after extending the `burndown` CTE to carry it.)

- [ ] **Step 3: Build**

```bash
cd transform && dbtf build --profiles-dir . --target dev --select milestone_burndown
```

Expected: clean.

- [ ] **Step 4: Commit**

```bash
git add transform/models/metrics/milestone_burndown.sql
git commit -m "Extend milestone_burndown with milestone_state, is_overdue, total_issues"
```

---

## Task 13: Full prod-target build with strict static analysis

Project policy: every model must pass `--static-analysis strict` against the prod (MotherDuck) target. This is the ship gate.

**Files:** none changed.

- [ ] **Step 1: Run prod build**

```bash
cd transform && dbtf build --profiles-dir . --target prod --static-analysis strict
```

Requires `MOTHERDUCK_TOKEN` env var to be set. Expected: every model builds and every test passes.

If a model fails static analysis but works in dev, the most common culprits are:
- Forward column references in the same select list (resolved by inlining — see Task 5 step 2c).
- `generate_series` int-vs-bigint issues (already worked around in `milestone_burndown.sql` and `epic_burndown.sql`).

- [ ] **Step 2: Run tests one more time as belt-and-suspenders**

```bash
cd transform && dbtf test --profiles-dir . --target prod
```

Expected: all pass.

- [ ] **Step 3: No commit — verification only**

---

## Task 14: Open the PR

**Files:** none changed.

- [ ] **Step 1: Push**

```bash
git push -u origin feat/epic-task-hierarchy
```

- [ ] **Step 2: Open PR**

```bash
gh pr create --title "Add epic/task hierarchy modeling" --body "$(cat <<'EOF'
## Summary
- Pull `issueType` and `parent` from GitHub GraphQL; plumb both through staging into `fct_issues`.
- Add `is_epic`, `has_epic_parent`, `is_orphan` to `fct_issues`.
- Add `fct_epics` and `fct_milestones` marts on top.
- Add three audit views (orphan issues, epics without milestones, tasks without milestones), an `epic_burndown` model, and extend `milestone_burndown` with milestone metadata.

Spec: `docs/superpowers/specs/2026-05-08-epic-task-hierarchy-design.md`

## Test plan
- [ ] `dbtf build --target dev` clean
- [ ] `dbtf build --target prod --static-analysis strict` clean
- [ ] `dbtf test` clean (audits expected to be non-zero — that's signal, not failure)
- [ ] Spot-check `fct_epics`: pick a known epic, confirm child counts
- [ ] Spot-check `audit_orphan_issues`: confirm a known orphan appears
- [ ] Spot-check `epic_burndown`: latest-day `open_at_date` equals `fct_epics.child_open`

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 3: Confirm with user**

Surface the PR URL and stop. Do not merge — leave that to the user.

---

## Glossary of project conventions used in this plan

- **`dbtf`** — dbt Fusion CLI binary (Rust engine). Use this, not `dbt-core`.
- **Static analysis strict** — set in `transform/dbt_project.yml` flags. Failures here block prod build; works around DuckDB type coercion gaps that don't show up at runtime.
- **`raw_source` macro** — `transform/macros/raw_source.sql`. Switches between local parquet and MotherDuck; not touched here, but referenced by `stg_issues`.
- **`feature branches, never push directly to main`** — from `CLAUDE.md`.
