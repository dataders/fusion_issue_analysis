---
layout: dashboard
---

# dbt v2 Issue Health

<style>
.static-note {
  margin: 4px 0 20px;
  padding: 8px 12px;
  background: rgba(28, 25, 23, 0.05);
  border-radius: 4px;
  font-size: 13px;
  line-height: 1.5;
  color: #57534e;
}
</style>

<div class="static-note">
  This is a static HTML export of a Graphene page. For live pages, use Graphene's local dev server, or Graphene Cloud.
</div>

<Row>
  <BigValue data=fct_issues value=open_issues title="Open issues" />
  <BigValue data=fct_issues value=opened_28d title="Opened (28d)" />
  <BigValue data=fct_issues value=closed_28d title="Closed (28d)" />
  <BigValue data=fct_issues value=median_days_to_close title="Median days to close" />
  <BigValue data=fct_issues value=answered_48h_rate title="Answered within 48h" />
</Row>

## Is the backlog shrinking?

```gsql backlog
with events as (
  from fct_issues
  select created_week as week, issue_category, count(*) as delta
  where is_work_item
  union all
  from fct_issues
  select closed_week as week, issue_category, -count(*) as delta
  where is_work_item and closed_at is not null
),
weekly as (
  select week,
    sum(case when issue_category = 'feature' then delta else 0 end) as feature,
    sum(case when issue_category = 'bug' then delta else 0 end) as bug,
    sum(case when issue_category = 'task' then delta else 0 end) as task,
    sum(case when issue_category = 'other' then delta else 0 end) as other
  from events
  group by week
)
select week,
  sum(feature) over (order by week) as feature,
  sum(bug) over (order by week) as bug,
  sum(task) over (order by week) as task,
  sum(other) over (order by week) as other
from weekly
order by week
```

```gsql backlog_recent
select * from backlog where week >= current_date - interval 52 week order by week
```

```gsql flow
select week, sum(opened) as opened, sum(closed) as closed
from (
  from fct_issues
  select created_week as week, opened as opened, 0 as closed
  where created_week >= current_date - interval 26 week and created_week < date_trunc('week', current_date)
  union all
  from fct_issues
  select closed_week as week, 0 as opened, closed as closed
  where closed_week >= current_date - interval 26 week and closed_week < date_trunc('week', current_date)
)
group by week
order by week
```

<Row>
  <ECharts data=backlog_recent height=320px>
    title: {text: 'Open issues by type'},
    color: ['#3D6B7E', '#C87F5A', '#87A68C', '#8E7AA0'],
    legend: {top: 0},
    grid: {top: 12},
    series: [
      {name: 'Feature', type: 'line', stack: 'open', areaStyle: {}, showSymbol: false, encode: {x: 'week', y: 'feature'}},
      {name: 'Bug', type: 'line', stack: 'open', areaStyle: {}, showSymbol: false, encode: {x: 'week', y: 'bug'}},
      {name: 'Task', type: 'line', stack: 'open', areaStyle: {}, showSymbol: false, encode: {x: 'week', y: 'task'}},
      {name: 'Other', type: 'line', stack: 'open', areaStyle: {}, showSymbol: false, encode: {x: 'week', y: 'other'}},
    ]
  </ECharts>
  <ECharts data=flow height=320px>
    title: {text: 'Opened vs. closed per week'},
    color: ['#C87F5A', '#3D6B7E'],
    legend: {top: 0},
    grid: {top: 12},
    series: [
      {name: 'Opened', type: 'bar', encode: {x: 'week', y: 'opened'}},
      {name: 'Closed', type: 'bar', encode: {x: 'week', y: 'closed'}},
    ]
  </ECharts>
</Row>

## Are we keeping up with triage?

```gsql triage
from fct_issues
select triage_label, triage_order,
  sum(case when is_open and is_work_item and age_bucket_order = 1 then 1 else 0 end) as d0_7,
  sum(case when is_open and is_work_item and age_bucket_order = 2 then 1 else 0 end) as d8_30,
  sum(case when is_open and is_work_item and age_bucket_order = 3 then 1 else 0 end) as d31_90,
  sum(case when is_open and is_work_item and age_bucket_order = 4 then 1 else 0 end) as d91_180,
  sum(case when is_open and is_work_item and age_bucket_order = 5 then 1 else 0 end) as d180_plus,
  open_issues
having open_issues > 0
order by triage_order desc
```

```gsql response
from fct_issues
select created_week as week, answered_48h_rate * 100 as pct_answered
where is_work_item and created_week >= current_date - interval 26 week and created_at < current_date - interval 2 day
order by week
```

<Row>
  <ECharts data=triage height=320px>
    title: {text: 'Open issues by triage status and age'},
    color: ['#D3E3E8', '#A6C5CF', '#5B8F9E', '#3D6B7E', '#22404E'],
    legend: {top: 0},
    grid: {left: 130, top: 12},
    yAxis: {type: 'category'},
    series: [
      {name: '0-7d', type: 'bar', stack: 'age', encode: {x: 'd0_7', y: 'triage_label'}},
      {name: '8-30d', type: 'bar', stack: 'age', encode: {x: 'd8_30', y: 'triage_label'}},
      {name: '31-90d', type: 'bar', stack: 'age', encode: {x: 'd31_90', y: 'triage_label'}},
      {name: '91-180d', type: 'bar', stack: 'age', encode: {x: 'd91_180', y: 'triage_label'}},
      {name: '180d+', type: 'bar', stack: 'age', encode: {x: 'd180_plus', y: 'triage_label'}},
    ]
  </ECharts>
  <ECharts data=response height=320px>
    title: {text: 'New issues answered within 48h (%)'},
    color: ['#3D6B7E'],
    grid: {top: 12},
    series: [{type: 'line', encode: {x: 'week', y: 'pct_answered'}}]
  </ECharts>
</Row>

```gsql triage_queue
from fct_issues
select cast(issue_number as varchar) as issue, title, issue_type, age_days, days_idle, reactions_total_count as reactions, comments_total_count as comments, customer_reported, issue_url
where is_open and is_work_item and triage_status = 'awaiting_triage'
order by age_days desc
limit 15
```

<Table data=triage_queue title="Triage queue, oldest first" link=issue_url showLinkCol=false rows=15 compact=true>
  <Column id=issue title="Issue" />
  <Column id=title title="Title" />
  <Column id=issue_type title="Type" />
  <Column id=age_days title="Age" />
  <Column id=days_idle title="Days Idle" />
  <Column id=reactions title="Reactions" />
  <Column id=comments title="Comments" />
  <Column id=customer_reported title="Customer" />
</Table>

## Where is the work?

```gsql areas
from fct_issue_labels
select label_title as area, issue.open_features, issue.open_bugs, issue.open_tasks, issue.open_other, issue.open_issues
where label_dimension = 'area'
having issue.open_issues > 0
order by issue.open_issues
```

```gsql adapters
from fct_issue_labels
select label_title as adapter, issue.open_features, issue.open_bugs, issue.open_tasks, issue.open_other, issue.open_issues
where label_dimension = 'adapter'
having issue.open_issues > 0
order by issue.open_issues
```

```gsql top_requested
from fct_issues
select cast(issue_number as varchar) as issue, title, issue_type, triage_label, age_days, reactions_total_count as reactions, comments_total_count as comments, customer_reported, issue_url
where is_open and is_work_item
order by reactions desc, comments desc
limit 15
```

<Row>
  <ECharts data=areas height=360px>
    title: {text: 'Open issues by area'},
    color: ['#3D6B7E', '#C87F5A', '#87A68C', '#8E7AA0'],
    legend: {top: 0},
    grid: {left: 110, top: 12},
    yAxis: {type: 'category'},
    series: [
      {name: 'Feature', type: 'bar', stack: 't', encode: {x: 'open_features', y: 'area', sort: 'open_issues asc'}},
      {name: 'Bug', type: 'bar', stack: 't', encode: {x: 'open_bugs', y: 'area', sort: 'open_issues asc'}},
      {name: 'Task', type: 'bar', stack: 't', encode: {x: 'open_tasks', y: 'area', sort: 'open_issues asc'}},
      {name: 'Other', type: 'bar', stack: 't', encode: {x: 'open_other', y: 'area', sort: 'open_issues asc'}},
    ]
  </ECharts>
  <ECharts data=adapters height=360px>
    title: {text: 'Open issues by adapter'},
    color: ['#3D6B7E', '#C87F5A', '#87A68C', '#8E7AA0'],
    legend: {top: 0},
    grid: {left: 110, top: 12},
    yAxis: {type: 'category'},
    series: [
      {name: 'Feature', type: 'bar', stack: 't', encode: {x: 'open_features', y: 'adapter', sort: 'open_issues asc'}},
      {name: 'Bug', type: 'bar', stack: 't', encode: {x: 'open_bugs', y: 'adapter', sort: 'open_issues asc'}},
      {name: 'Task', type: 'bar', stack: 't', encode: {x: 'open_tasks', y: 'adapter', sort: 'open_issues asc'}},
      {name: 'Other', type: 'bar', stack: 't', encode: {x: 'open_other', y: 'adapter', sort: 'open_issues asc'}},
    ]
  </ECharts>
</Row>

## How close are the epics?

```gsql epics
from epic_progress
select cast(epic_number as varchar) as epic, title, child_closed, child_total, pct_complete, issue_url
where pct_complete < 100
order by pct_complete desc, child_open, epic_number
limit 15
```

<Table data=epics title="Open epics by share of sub-issues closed" link=issue_url showLinkCol=false rows=15 compact=true>
  <Column id=epic title="Epic" />
  <Column id=title title="Title" />
  <Column id=child_closed title="Closed" />
  <Column id=child_total title="Total" />
  <Column id=pct_complete title="Complete (%)" contentType=bar barColor="#3D6B7E" />
</Table>

## What should we work on, and who is on it?

```gsql assignees
from assignee_workload
select assignee, features, bugs, tasks, other, total
where assignee_login <> '(unassigned)'
order by total desc
limit 15
```

```gsql unassigned
from assignee_workload
select total
where assignee_login = '(unassigned)'
```

<div class="callout"><strong><Value data=unassigned column=total /></strong> open issues are unassigned. The chart below shows the 15 busiest assignees.</div>

<ECharts data=assignees height=420px>
    title: {text: 'Open issues by assignee (top 15, excluding unassigned)'},
    color: ['#3D6B7E', '#C87F5A', '#87A68C', '#8E7AA0'],
    legend: {top: 0},
    grid: {left: 110, top: 12},
    yAxis: {type: 'category'},
    series: [
      {name: 'Feature', type: 'bar', stack: 't', encode: {x: 'features', y: 'assignee', sort: 'total asc'}},
      {name: 'Bug', type: 'bar', stack: 't', encode: {x: 'bugs', y: 'assignee', sort: 'total asc'}},
      {name: 'Task', type: 'bar', stack: 't', encode: {x: 'tasks', y: 'assignee', sort: 'total asc'}},
      {name: 'Other', type: 'bar', stack: 't', encode: {x: 'other', y: 'assignee', sort: 'total asc'}},
    ]
</ECharts>

<Table data=top_requested title="Most-requested open issues" link=issue_url showLinkCol=false rows=15 compact=true>
  <Column id=issue title="Issue" />
  <Column id=title title="Title" />
  <Column id=issue_type title="Type" />
  <Column id=triage_label title="Triage Status" />
  <Column id=age_days title="Age" />
  <Column id=reactions title="Reactions" />
  <Column id=comments title="Comments" />
  <Column id=customer_reported title="Customer" />
</Table>
