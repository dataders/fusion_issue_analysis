---
title: dbt Fusion issue health
description: Open engine:v2 issues in dbt-labs/dbt-core (epics excluded unless noted)
---

<!-- Tiles, order and palette follow dashboard/tiles.yml. Sources are thin
     `select * from <model>` files (generate_sources.py); pages only select,
     order (tiles.yml order_by), rename and format. -->

```sql meta
select
    strftime(as_of_date, '%Y-%m-%d') as as_of,
    days_stale,
    source_repo,
    source_label,
    days_stale > 3 as is_stale  -- tiles.yml meta.stale_after_days
from fusion.dashboard_meta
```

Open engine:v2 issues in dbt-labs/dbt-core (epics excluded unless noted)

{#if meta[0].is_stale}
<Alert status="warning">
Data as of {meta[0].as_of} · {meta[0].source_repo} · label {meta[0].source_label} · ⚠ {meta[0].days_stale} days old — the extract may have stopped
</Alert>
{:else}
<p class="text-sm text-gray-500">Data as of {meta[0].as_of} · {meta[0].source_repo} · label {meta[0].source_label}</p>
{/if}

## Where do things stand?

```sql kpis
-- headline_kpis formatted per tiles.yml kpis: '—' for nulls, explicit sign on backlog change.
-- Evidence caches integers as doubles, so trim a trailing '.0' when printing.
select
    coalesce(regexp_replace(open_issues::varchar, '\.0$', ''), '—') as open_issues,
    coalesce(case when backlog_change_28d >= 0 then '+' else '' end
        || regexp_replace(backlog_change_28d::varchar, '\.0$', ''), '—') || ' in 28 days' as open_issues_context,
    coalesce(regexp_replace(opened_28d::varchar, '\.0$', ''), '—')
        || ' / ' || coalesce(regexp_replace(closed_28d::varchar, '\.0$', ''), '—') as opened_closed,
    coalesce(regexp_replace(awaiting_triage::varchar, '\.0$', ''), '—') as awaiting_triage,
    'median age ' || coalesce(regexp_replace(awaiting_triage_median_age_days::varchar, '\.0$', ''), '—')
        || ' days' as awaiting_triage_context,
    coalesce(regexp_replace(pct_responded_48h_28d::varchar, '\.0$', '') || '%', '—') as responded_48h,
    'median first reply ' || coalesce(regexp_replace(median_hours_to_first_response_28d::varchar, '\.0$', ''), '—')
        || ' h' as responded_48h_context,
    coalesce(regexp_replace(median_days_to_close_28d::varchar, '\.0$', ''), '—') as median_days_to_close,
    coalesce(regexp_replace(open_customer_reported::varchar, '\.0$', ''), '—') as customer_reported,
    coalesce(regexp_replace(open_hard_blockers::varchar, '\.0$', ''), '—') || ' hard blockers' as customer_reported_context
from fusion.headline_kpis
```

<div class="grid grid-cols-2 sm:grid-cols-3 gap-3 my-4">
  <div class="border rounded-md p-3"><div class="text-xs text-gray-500">Open issues</div><div class="text-2xl font-semibold">{kpis[0].open_issues}</div><div class="text-xs text-gray-500">{kpis[0].open_issues_context}</div></div>
  <div class="border rounded-md p-3"><div class="text-xs text-gray-500">Opened / closed (28d)</div><div class="text-2xl font-semibold">{kpis[0].opened_closed}</div></div>
  <div class="border rounded-md p-3"><div class="text-xs text-gray-500">Awaiting triage</div><div class="text-2xl font-semibold">{kpis[0].awaiting_triage}</div><div class="text-xs text-gray-500">{kpis[0].awaiting_triage_context}</div></div>
  <div class="border rounded-md p-3"><div class="text-xs text-gray-500">Answered within 48h (28d)</div><div class="text-2xl font-semibold">{kpis[0].responded_48h}</div><div class="text-xs text-gray-500">{kpis[0].responded_48h_context}</div></div>
  <div class="border rounded-md p-3"><div class="text-xs text-gray-500">Median days to close (28d)</div><div class="text-2xl font-semibold">{kpis[0].median_days_to_close}</div></div>
  <div class="border rounded-md p-3"><div class="text-xs text-gray-500">Customer-reported open</div><div class="text-2xl font-semibold">{kpis[0].customer_reported}</div><div class="text-xs text-gray-500">{kpis[0].customer_reported_context}</div></div>
</div>

## Is the backlog shrinking?

```sql backlog_weekly
select
    week::date as week,
    upper(issue_category[1]) || issue_category[2:] as issue_type,
    open_issues
from fusion.backlog_weekly
order by week
```

<AreaChart
  data={backlog_weekly}
  x=week
  y=open_issues
  series=issue_type
  type=stacked
  seriesOrder={['Feature', 'Bug', 'Task', 'Other']}
  seriesColors={{Feature: '#2a78d6', Bug: '#eb6834', Task: '#1baf7a', Other: '#898781'}}
  title="Open issues over time"
  subtitle="Open at the end of each week, by type"
  yAxisTitle="Open issues"
/>

```sql weekly_flow
select week::date as week, opened as "Opened", closed as "Closed", net_change
from fusion.weekly_flow
order by week
```

<BarChart
  data={weekly_flow}
  x=week
  y={['Opened', 'Closed']}
  type=grouped
  seriesColors={{Opened: '#eb6834', Closed: '#2a78d6'}}
  title="Opened vs closed per week"
  subtitle="Complete weeks; when closed > opened the backlog shrank"
  yAxisTitle="Issues"
/>

## Are we keeping up with triage?

```sql triage_pipeline
select status_label, age_bucket, issue_count
from fusion.triage_pipeline
order by status_order, age_bucket_order
```

<BarChart
  data={triage_pipeline}
  x=status_label
  y=issue_count
  series=age_bucket
  type=stacked
  swapXY=true
  sort=false
  seriesOrder={['0-7d', '8-30d', '31-90d', '91-180d', '180d+']}
  seriesColors={{'0-7d': '#b7d3f6', '8-30d': '#86b6ef', '31-90d': '#5598e7', '91-180d': '#256abf', '180d+': '#104281'}}
  title="Open issues by triage status and age"
  subtitle="How much is waiting, and for how long"
  yAxisTitle="Open issues"
/>

```sql response_weekly
select week::date as week, pct_responded_48h, issues_opened, responded_48h, median_hours_to_first_response
from fusion.response_weekly
order by week
```

<LineChart
  data={response_weekly}
  x=week
  y=pct_responded_48h
  yMin=0
  yMax=100
  yFmt='0"%"'
  lineColor="#2a78d6"
  markers=true
  title="New issues answered within 48 hours"
  subtitle="By week opened; unanswered issues count as misses"
  yAxisTitle="% answered within 48h"
/>

```sql triage_queue
select issue_number, title, issue_category, age_days, days_idle, reactions, comments, is_customer_reported, issue_url
from fusion.triage_queue
order by age_days desc
```

<DataTable data={triage_queue} link=issue_url rows=15 search=true title="Triage queue — oldest first" subtitle="Open issues still labeled status:triage">
  <Column id=issue_number title="#" fmt=id/>
  <Column id=title title="Title" wrap=true/>
  <Column id=issue_category title="Type"/>
  <Column id=age_days title="Age (days)"/>
  <Column id=days_idle title="Idle (days)"/>
  <Column id=reactions title="Reactions"/>
  <Column id=comments title="Comments"/>
  <Column id=is_customer_reported title="Customer"/>
</DataTable>

## Where is the work?

```sql open_by_area
select area, upper(issue_category[1]) || issue_category[2:] as issue_type, issue_count
from fusion.open_by_area
order by area_total desc, area
```

<BarChart
  data={open_by_area}
  x=area
  y=issue_count
  series=issue_type
  type=stacked
  swapXY=true
  sort=false
  seriesOrder={['Feature', 'Bug', 'Task', 'Other']}
  seriesColors={{Feature: '#2a78d6', Bug: '#eb6834', Task: '#1baf7a', Other: '#898781'}}
  title="Open issues by area"
  subtitle="Issues with several areas count in each"
  yAxisTitle="Open issues"
/>

```sql open_by_adapter
select adapter, upper(issue_category[1]) || issue_category[2:] as issue_type, issue_count
from fusion.open_by_adapter
order by adapter_total desc, adapter
```

<BarChart
  data={open_by_adapter}
  x=adapter
  y=issue_count
  series=issue_type
  type=stacked
  swapXY=true
  sort=false
  seriesOrder={['Feature', 'Bug', 'Task', 'Other']}
  seriesColors={{Feature: '#2a78d6', Bug: '#eb6834', Task: '#1baf7a', Other: '#898781'}}
  title="Open issues by adapter"
  subtitle="(none) = adapter-agnostic"
  yAxisTitle="Open issues"
/>

## How close are the epics?

```sql epic_progress
select epic_number, title, child_closed, child_total, pct_complete, milestone_title, issue_url
from fusion.epic_progress
order by pct_complete desc, child_open, epic_number
```

<DataTable data={epic_progress} link=issue_url rows=15 title="Open epics by % of sub-issues closed" subtitle="Top of the list can be closed out soon">
  <Column id=epic_number title="#" fmt=id/>
  <Column id=title title="Epic" wrap=true/>
  <Column id=child_closed title="Closed"/>
  <Column id=child_total title="Sub-issues"/>
  <Column id=pct_complete title="% complete" contentType=bar barColor="#2a78d6" fmt='0"%"'/>
  <Column id=milestone_title title="Milestone"/>
</DataTable>

## What should we work on, and who is on it?

```sql top_requested
select issue_number, title, issue_category, areas, triage_status, reactions, comments, age_days, is_customer_reported, issue_url
from fusion.top_requested
order by reactions desc, comments desc
```

<DataTable data={top_requested} link=issue_url rows=25 title="Most-requested open issues" subtitle="Ranked by reactions, then comments">
  <Column id=issue_number title="#" fmt=id/>
  <Column id=title title="Title" wrap=true/>
  <Column id=issue_category title="Type"/>
  <Column id=areas title="Areas"/>
  <Column id=triage_status title="Triage"/>
  <Column id=reactions title="Reactions"/>
  <Column id=comments title="Comments"/>
  <Column id=age_days title="Age (days)"/>
  <Column id=is_customer_reported title="Customer"/>
</DataTable>

```sql assignee_workload
select assignee_login, upper(issue_category[1]) || issue_category[2:] as issue_type, issue_count
from fusion.assignee_workload
order by assignee_total desc, assignee_login
```

<BarChart
  data={assignee_workload}
  x=assignee_login
  y=issue_count
  series=issue_type
  type=stacked
  swapXY=true
  sort=false
  seriesOrder={['Feature', 'Bug', 'Task', 'Other']}
  seriesColors={{Feature: '#2a78d6', Bug: '#eb6834', Task: '#1baf7a', Other: '#898781'}}
  title="Open issues by assignee"
  subtitle="Top 15, including unassigned"
  yAxisTitle="Open issues"
/>
