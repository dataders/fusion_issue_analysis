---
title: dbt-fusion Issue Health
---


# dbt-fusion Issue Health · Evidence.dev

Actionable metrics for dbt-labs/dbt-fusion (excludes EPICs)

## Key Metrics

```sql kpis
select
    open_issues,
    closed_4w,
    opened_4w,
    stale_count,
    pct_responded_48h,
    rolling_median_close_days as median_close_days
from summary_kpis
```

<BigValue data={kpis} value="open_issues" title="Open Issues"/>
<BigValue data={kpis} value="closed_4w" title="Closed (4 wk)"/>
<BigValue data={kpis} value="opened_4w" title="Opened (4 wk)"/>
<BigValue data={kpis} value="median_close_days" title="Median Close (4 wk)"/>
<BigValue data={kpis} value="pct_responded_48h" title="48h Response SLA" fmt="0"/>
<BigValue data={kpis} value="stale_count" title="Stale Issues (30d+)"/>

## Cumulative Issue Flow

```sql cumulative_flow
select week, opened, closed from weekly_flow order by week
```

<!-- Evidence AreaChart with y array shows stacked areas; true cumulative requires window
     functions which Evidence does not run — use weekly flow as the closest equivalent.
     Capability gap: cannot show running totals natively. -->

<AreaChart
  data={cumulative_flow}
  x="week"
  y={["opened", "closed"]}
  title="Weekly Opened vs Closed (non-cumulative)"
  subtitle="Note: Evidence cannot compute running totals — showing weekly counts"
/>

## Velocity & Response

```sql velocity
select week, issue_category, median_days from velocity order by week
```

<LineChart
  data={velocity}
  x="week"
  y="median_days"
  series="issue_category"
  title="Median Days to Close: Bugs vs Enhancements"
/>

```sql response_pctiles
select week, p25, p50, p75 from response_pctiles order by week
```

<LineChart
  data={response_pctiles}
  x="week"
  y={["p25", "p50", "p75"]}
  title="Time to First Response (hours)"
/>

## Issue Distribution

```sql age_distribution
select age_bucket, issue_category, issue_count from age_distribution
```

<BarChart
  data={age_distribution}
  x="age_bucket"
  y="issue_count"
  series="issue_category"
  type="stacked"
  title="Open Issue Age by Type"
/>

```sql close_by_label
select label_name, median_days_to_close, closed_count
from close_by_label
order by median_days_to_close desc
```

<BarChart
  data={close_by_label}
  x="label_name"
  y="median_days_to_close"
  swapXY=true
  title="Median Days to Close by Label"
/>

## Triage Health

```sql triage
select pct_labeled, pct_assigned, pct_milestoned, pct_typed from triage_health
```

<BigValue data={triage} value="pct_labeled" title="% Labeled" fmt="0"/>
<BigValue data={triage} value="pct_typed" title="% Typed" fmt="0"/>
<BigValue data={triage} value="pct_assigned" title="% Assigned" fmt="0"/>
<BigValue data={triage} value="pct_milestoned" title="% Milestoned" fmt="0"/>

## Workload & Priorities

```sql assignee_workload
select assignee_login, bugs, enhancements
from assignee_workload
order by bugs + enhancements desc
```

<BarChart
  data={assignee_workload}
  x="assignee_login"
  y={["bugs", "enhancements"]}
  type="stacked"
  swapXY=true
  title="Open Issues by Assignee"
/>

```sql community_priorities
select issue_number, title, issue_category, reactions_total_count, age_days
from community_priorities
order by reactions_total_count desc
limit 15
```

<DataTable data={community_priorities} search=true rows=15 title="Community Priorities"/>
