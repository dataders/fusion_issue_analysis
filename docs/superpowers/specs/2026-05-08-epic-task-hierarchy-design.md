# Epic / Task hierarchy modeling

**Date:** 2026-05-08
**Author:** Anders Swanson
**Status:** Draft

## Phase 0 — Plumb `issue_type` end-to-end

The Epic definition relies on `issue_type = 'Task'`. As of writing,
`issue_type` is not yet on `main` — it lives on the unmerged
`feat/categorize-with-issue-type` branch (commits `1db7750d` and
`c2c61666`). Rather than waiting on that branch, this spec absorbs
those changes as Phase 0 so the work is self-contained.

If `grep -r issue_type extract/github/ transform/models/` returns
non-empty when implementation begins, Phase 0 is already done — skip
it. Otherwise, do all of the following before Phase 1:

- **Extract** — add `issueType { name }` to the issue node selection
  in `extract/github/queries.py:ISSUES_QUERY`. The same query body is
  reused for `pullRequests`, where `issueType` is not a valid field.
  Guard with the existing `%s` template substitution pattern (or an
  inline-fragment workaround) so the issues-only field is only
  emitted when the query targets `issues`.
- **Source** — declare `issue_type__name` under the `issues` table in
  `transform/models/staging/_sources.yml`.
- **Staging** — in `stg_issues.sql`, select
  `issue_type__name as issue_type`.
- **Marts** — in `fct_issues.sql`, passthrough `i.issue_type`. Update
  the existing `issue_category` CASE to consider `issue_type`
  alongside the label flags (so issues with native Issue Type but no
  matching label stop falling through to `'other'`). Create
  `transform/models/marts/_schema.yml` if it doesn't exist and
  document the new column.

This Phase 0 mirrors the unmerged branch's intent. After it lands,
Phases 1–3 below proceed unchanged.

## Problem

The current `fct_issues` model knows whether an issue has a label, an
assignee, or a milestone, but it does not know how issues relate to one
another. The dbt-fusion team organizes work as a two-level hierarchy:

- **Epics** — top-level scoping issues, identified in this repo by
  `issue_type = 'Task'` and `'epic'` somewhere in the title (case-insensitive).
- **Tasks** — every other issue that lives under an epic via GitHub's
  native sub-issue / parent-issue relationship.

Without parent-child information in the warehouse we cannot answer:

1. Is a given issue attached to an epic, or is it an orphan?
2. Are there open epics that are not attributed to a milestone?
3. How is each milestone burning down over time, broken out by epic?
4. Are tasks consistently rolling up to epics, and do those epics
   consistently roll up to milestones?

## Definitions

- **Epic.** An issue where `issue_type = 'Task'` and
  `lower(title) LIKE '%epic%'`. Epics are a strict subset of
  Task-typed issues — all Epics are Tasks, but not all Tasks are Epics.
  Note: `is_epic` does not gate on state — both open and closed Epics
  qualify, so historical reporting and burndown can include closed
  Epics.

### Naming reconciliation: `is_epic` vs existing `has_epic`

`fct_issues` currently has `has_epic` (0/1 flag, true when an issue
carries the `EPIC` label) and `issue_category` (string with `'epic'`
as one value). These are **label-based**.

The new `is_epic` is **issue-type + title based** and is the
authoritative epic flag going forward — the dbt-fusion team has moved
off the `EPIC` label and onto native Issue Types with title
conventions. Keep `has_epic` as-is for now (some dashboards may still
read it) but document in `_schema.yml` that `is_epic` is preferred.
Removing `has_epic` is a separate cleanup, out of scope here.
- **`has_epic_parent`.** True when an issue's parent (via GitHub
  sub-issue relation) satisfies the Epic definition above.
- **Task (in this design).** Any open, non-epic issue that has an
  epic parent.
- **Orphan issue.** An open issue that is neither an Epic nor has an
  Epic parent.
- **Orphan epic.** An open Epic that has no milestone attached.

## Architecture overview

Three changes, shipped in a single PR:

1. **Extract** — pull `parent` into the GraphQL issues query so the
   warehouse has the relationship at all.
2. **Staging + marts** — expose parent fields, add `is_epic` and
   `has_epic_parent` to `fct_issues`, build new `fct_epics` and
   `fct_milestones` marts.
3. **Audits + burndown** — three small audit models that surface the
   integrity questions above; one new `epic_burndown` model alongside
   the existing `milestone_burndown`.

```
extract/github/queries.py       (Phase 1)
  └── ISSUES_QUERY: + parent { number, title, issueType { name } }

transform/models/staging/
  ├── stg_issues.sql            (Phase 2: passthrough parent_*)
  └── _sources.yml              (Phase 1: declare new raw columns)

transform/models/marts/
  ├── fct_issues.sql            (Phase 2: + is_epic, has_epic_parent, is_orphan)
  ├── fct_epics.sql             (Phase 2: NEW)
  ├── fct_milestones.sql        (Phase 2: NEW)
  └── _schema.yml               (Phase 2: tests + docs for new columns/models)

transform/models/metrics/
  ├── milestone_burndown.sql    (Phase 3: extend with fct_milestones join)
  ├── epic_burndown.sql         (Phase 3: NEW)
  ├── audit_orphan_issues.sql   (Phase 3: NEW)
  ├── audit_epics_without_milestone.sql    (Phase 3: NEW)
  └── audit_tasks_without_milestone.sql    (Phase 3: NEW)
```

## Phase 1 — Extract change

### GraphQL

Add to the issue node selection in
`extract/github/queries.py:ISSUES_QUERY`:

```graphql
parent {
  number
  title
  issueType { name }
}
```

`parent` is a scalar 1:1 relationship on `Issue`. dlt's GraphQL flattening
maps this to three new top-level columns on the `issues` resource:

- `parent__number` (int, nullable)
- `parent__title` (string, nullable)
- `parent__issue_type__name` (string, nullable)

No new dlt resource is needed — children-of-an-issue can be reconstructed
in dbt by reverse-joining `fct_issues` on its own `parent_number`.

### Source declaration

Add the three columns to `transform/models/staging/_sources.yml` under
the `issues` table so static analysis sees them.

### Sanity / non-goals

- We are not extracting `subIssues` from GraphQL. Reverse-join on
  `parent_number` is sufficient and avoids redundant data.
- We do not handle cross-repository parent links. The dbt-fusion repo
  does not appear to use them; if `parent_number` ever fails to join
  in `fct_issues`, the audit surface should make that visible (see
  Test plan).
- This change does not require a backfill — dlt's next run will pick
  up parent relationships on all issues it loads.

## Phase 2 — Staging and marts

### `stg_issues`

Add three passthrough columns:

```sql
parent__number       as parent_number,
parent__title        as parent_title,
parent__issue_type__name as parent_issue_type,
```

### `fct_issues` — new columns

The prereq branch already exposes `issue_type` (passthrough from
`stg_issues`). On top of that, this spec adds:

```sql
-- Epic identity (issue_type + title; authoritative going forward)
case
  when issue_type = 'Task' and lower(title) like '%epic%'
  then true else false
end as is_epic,

-- Parent relationship (passthroughs from stg_issues)
parent_number,
parent_title,
parent_issue_type,
case
  when parent_issue_type = 'Task' and lower(parent_title) like '%epic%'
  then true else false
end as has_epic_parent,

-- Orphan flag — open work that doesn't roll up to an epic
case
  when state = 'OPEN' and not is_epic and not has_epic_parent
  then true else false
end as is_orphan
```

`fct_issues` should also expose enriched milestone columns so
downstream marts (`fct_epics`, audits, burndown) don't need to
re-join `dim_milestones`. Add these passthroughs:

```sql
i.milestone_state,
i.milestone_due_on,
i.milestone_created_at,
i.milestone_closed_at,
```

(`stg_issues` already selects all four from the source.)

### `fct_epics` (new)

**Grain:** one row per Epic.

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
    e.milestone_due_on,

    coalesce(c.child_total,  0) as child_total,
    coalesce(c.child_open,   0) as child_open,
    coalesce(c.child_closed, 0) as child_closed,
    case
        when coalesce(c.child_total, 0) = 0 then null
        else c.child_closed::float / c.child_total
    end                         as pct_complete,

    e.milestone_number is not null      as has_milestone,
    e.state = 'OPEN'
        and e.milestone_number is null  as is_orphan_epic
from epics e
left join child_rollup c
    on e.issue_number = c.epic_number
```

### `fct_milestones` (new)

**Grain:** one row per milestone. Coexists with `dim_milestones` —
`dim_milestones` remains the conformed dimension; `fct_milestones`
adds aggregates.

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

    m.milestone_state = 'OPEN'
        and m.milestone_due_on is not null
        and m.milestone_due_on < current_date as is_overdue
from milestones m
left join issue_rollup r
    on m.milestone_number = r.milestone_number
```

## Phase 3 — Audits and burndown

### Audit models

All three live in `transform/models/metrics/` and follow the same
shape: a thin filter on `fct_issues` / `fct_epics` that returns the
"violating" rows. Empty result = clean state.

- **`audit_orphan_issues`** — `select … from fct_issues where is_orphan`.
  Columns: issue_number, title, issue_type, created_at,
  `current_date - created_at::date` as age_days.
- **`audit_epics_without_milestone`** — `select … from fct_epics where is_orphan_epic`.
- **`audit_tasks_without_milestone`** — open issues where
  `has_epic_parent = true AND milestone_number IS NULL`.

Sanity test: `audit_epics_without_milestone` row count should equal
`count(*) filter (where is_orphan_epic)` from `fct_epics`. Encode as
a `dbt_utils.equal_rowcount` test or equivalent.

### `epic_burndown` (new)

Same date-spine + cumulative-open/closed technique already used by
`metrics/milestone_burndown.sql`, but pivoted on the epic's children.

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

### `milestone_burndown` extension

Add a left join to `fct_milestones` to surface `milestone_state`,
`is_overdue`, and `total_issues` alongside the existing reconstructed
counts. No re-architecture.

## Tests

In `_schema.yml`:

- `fct_issues.is_epic` — not null.
- `fct_issues.has_epic_parent` — not null.
- `fct_issues.is_orphan` — not null.
- `fct_issues.parent_number` — `relationships` test to
  `ref('fct_issues')` field `issue_number`, scoped to rows where
  `parent_number is not null` (this is the cross-repo / data-quality
  guardrail: a parent_number that does not match an issue in the
  warehouse means either cross-repo or a bug).
- `fct_epics.epic_number` — unique, not null.
- `fct_milestones.milestone_number` — unique, not null.
- Audit models — `dbt_utils.equal_rowcount` to `0` configured as
  `severity: warn` so audits surface in CI logs without breaking the
  build (failing audits are signal, not bugs in the pipeline).

All new models must pass
`dbtf build --profiles-dir . --target prod --static-analysis strict`
per project convention.

## Test plan

- [ ] Run extract against dbt-fusion; confirm `parent__number`,
      `parent__title`, `parent__issue_type__name` populated for at
      least some issues.
- [ ] `dbtf build --target dev` clean.
- [ ] `dbtf build --target prod --static-analysis strict` clean.
- [ ] `dbtf test` clean (audit warnings allowed).
- [ ] Spot-check `fct_epics`: pick one known epic, verify
      `child_total` / `child_open` / `child_closed` match the count of
      issues whose `parent_number` equals it.
- [ ] Spot-check `audit_orphan_issues`: pick a known orphan, confirm
      it appears.
- [ ] Spot-check `audit_epics_without_milestone`: confirm at least one
      known orphan epic appears (or zero, with rationale).
- [ ] `epic_burndown`: pick one epic, eyeball that
      `cumulative_opened - cumulative_closed = open_at_date` for the
      latest date and matches `child_open` in `fct_epics`.

## Non-goals

- No dlt snapshot strategy. Burndown is reconstructed from
  `created_at` / `closed_at`; if an issue is reopened, the historical
  reconstruction will be inaccurate for the period between close and
  reopen. Acceptable for current use.
- No cross-repository parent handling. Surfaced via the
  `relationships` test on `parent_number`.
- No backfill of historical issues beyond what dlt's next run pulls.
- No changes to dashboards in this PR — that is a follow-up once the
  marts are stable.
