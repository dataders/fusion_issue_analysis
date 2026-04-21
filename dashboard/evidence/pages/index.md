---
title: dbt-fusion Issue Health
---

# dbt-fusion Issue Health · Evidence.dev

```sql open_summary
select
    count(case when state = 'OPEN' and issue_category != 'epic' then 1 end)                                                          as open_issues,
    count(case when closed_at >= current_date - interval '28 days' and issue_category != 'epic' then 1 end)                          as closed_4w,
    count(case when created_at >= current_date - interval '28 days' and issue_category != 'epic' then 1 end)                         as opened_4w,
    count(case when state = 'OPEN' and updated_at < current_date - interval '30 days' and issue_category != 'epic' then 1 end)       as stale_count,
    round(median(case when closed_at >= current_date - interval '28 days' then hours_to_close end) / 24.0, 1)                        as median_close_days
from issues
```

<BigValue data={open_summary} value="open_issues" title="Open Issues"/>
<BigValue data={open_summary} value="closed_4w" title="Closed (4 wk)"/>
<BigValue data={open_summary} value="opened_4w" title="Opened (4 wk)"/>
<BigValue data={open_summary} value="stale_count" title="Stale (30d+)"/>
<BigValue data={open_summary} value="median_close_days" title="Median Close Days (4 wk)"/>

## Weekly Issue Flow

```sql weekly_flow
with opened as (
    select date_trunc('week', created_at)::date as week, count(*) as opened
    from issues where issue_category != 'epic'
    group by 1
),
closed as (
    select date_trunc('week', closed_at)::date as week, count(*) as closed
    from issues where closed_at is not null and issue_category != 'epic'
    group by 1
)
select
    strftime(coalesce(o.week, c.week), '%Y-%m-%d') as week,
    coalesce(o.opened, 0) as opened,
    coalesce(c.closed, 0) as closed
from opened o full outer join closed c on o.week = c.week
order by 1
```

<AreaChart
  data={weekly_flow}
  x="week"
  y={["opened", "closed"]}
  title="Opened vs Closed per Week"
/>

## Resolution Velocity

```sql velocity
select
    strftime(date_trunc('week', closed_at), '%Y-%m-%d') as week,
    issue_category,
    round(median(hours_to_close) / 24.0, 1) as median_days
from issues
where closed_at is not null and issue_category in ('bug', 'enhancement')
group by 1, 2
having count(*) >= 2
order by 1
```

<LineChart
  data={velocity}
  x="week"
  y="median_days"
  series="issue_category"
  title="Median Days to Close: Bug vs Enhancement"
/>

## Issue Categories (Open)

```sql by_category
select issue_category, count(*) as count
from issues
where state = 'OPEN' and issue_category != 'epic'
group by 1
order by 2 desc
```

<BarChart data={by_category} x="issue_category" y="count" title="Open Issues by Category"/>

## Triage Health

```sql triage
select
    round(sum(is_labeled::int) * 100.0 / count(*), 0) as pct_labeled,
    round(sum(is_assigned::int) * 100.0 / count(*), 0) as pct_assigned,
    round(sum(has_milestone::int) * 100.0 / count(*), 0) as pct_milestoned
from issues
where state = 'OPEN' and issue_category != 'epic'
```

<BigValue data={triage} value="pct_labeled" title="% Labeled" fmt="0"/>
<BigValue data={triage} value="pct_assigned" title="% Assigned" fmt="0"/>
<BigValue data={triage} value="pct_milestoned" title="% In Milestone" fmt="0"/>

## Top Community Priorities

```sql top_issues
select
    issue_number,
    title,
    issue_category,
    reactions_total_count,
    round(datediff('day', created_at, current_date), 0) as age_days
from issues
where state = 'OPEN' and reactions_total_count > 0 and issue_category != 'epic'
order by reactions_total_count desc
limit 15
```

<DataTable data={top_issues} search=true rows=15/>

## Issue Detail

```sql open_issues_detail
select
    issue_number,
    title,
    issue_category,
    strftime(created_at, '%Y-%m-%d') as created_date,
    reactions_total_count,
    comments_total_count,
    coalesce(milestone_title, '') as milestone
from issues
where state = 'OPEN' and issue_category != 'epic'
order by reactions_total_count desc, created_at asc
```

<DataTable data={open_issues_detail} search=true rows=20/>
