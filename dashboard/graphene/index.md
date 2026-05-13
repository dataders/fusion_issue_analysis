---
title: Fusion Issue Health
layout: dashboard
---

```gsql kpis
from summary_kpis
select *
```

<Row>
  <BigValue data=kpis value=open_issues title="Open issues" />
  <BigValue data=kpis value=opened_4w title="Opened, 4w" />
  <BigValue data=kpis value=closed_4w title="Closed, 4w" />
  <BigValue data=kpis value=pct_responded_48h title="Responded <=48h" />
</Row>

```gsql weekly
from weekly_flow
select week, opened, closed
order by week
```

<AreaChart
  data=weekly
  x=week
  y="opened, closed"
  title="Weekly issue flow"
  height=260px
/>

```gsql categories
from open_vs_closed_by_category
select distinct issue_category
order by issue_category
```

<Dropdown
  title="Issue category"
  name=category
  data=categories
  value=issue_category
  defaultValue="bug"
/>

```gsql state_by_category
from open_vs_closed_by_category
where issue_category = $category
select state, n
order by state
```

```gsql all_categories
from open_vs_closed_by_category
select issue_category, state, n
order by issue_category, state
```

<BarChart
  data=state_by_category
  x=state
  y=n
  title="Selected category open vs. closed"
  height=260px
/>

<BarChart
  data=all_categories
  x=issue_category
  y=n
  splitBy=state
  arrange=group
  title="All categories overview"
  height=260px
/>

```gsql response
from response_pctiles
select week, p25, p50, p75
order by week
```

<LineChart
  data=response
  x=week
  y="p25, p50, p75"
  title="Hours to first response"
  height=260px
/>

```gsql triage
from triage_health
select *
```

<Row>
  <BigValue data=triage value=pct_labeled title="Labeled" />
  <BigValue data=triage value=pct_typed title="Typed" />
  <BigValue data=triage value=pct_assigned title="Assigned" />
  <BigValue data=triage value=pct_milestoned title="Milestoned" />
</Row>

```gsql priorities
from community_priorities
select
  issue_number,
  title,
  issue_category,
  reactions_total_count,
  comments_total_count,
  age_days,
  url
order by reactions_total_count desc, comments_total_count desc
```

<Table
  data=priorities
  title="Community-prioritized open issues"
  rows=10
  compact=true
  rowLines=true
  link=url
  showLinkCol=false
>
  <Column id=issue_number title="#" />
  <Column id=title wrap=true />
  <Column id=issue_category title="Type" />
  <Column id=reactions_total_count title="Reactions" align=right />
  <Column id=comments_total_count title="Comments" align=right />
  <Column id=age_days title="Age days" align=right />
</Table>
