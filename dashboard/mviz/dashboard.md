---
title: dbt-fusion Issue Health
theme: dark
continuous: true
---

# dbt-fusion Issue Health

## Key Metrics

```big_value size=[3,2] file=data/kpi_net_flow.json
```
```big_value size=[3,2] file=data/kpi_open_issues.json
```
```big_value size=[3,2] file=data/kpi_median_close.json
```
```big_value size=[3,2] file=data/kpi_sla.json
```
```big_value size=[4,2] file=data/kpi_stale.json
```

## Cumulative Issue Flow

```area size=[16,6] file=data/cumulative_flow.json
{
  "title": "Cumulative Opened vs Closed (excludes EPICs)",
  "x": "week",
  "y": ["cumulative_opened", "cumulative_closed"]
}
```

## Velocity & Response Time

```line size=[8,6] file=data/velocity.json
{
  "title": "Median Days to Close: Bugs vs Enhancements",
  "x": "week",
  "y": ["bugs", "enhancements"]
}
```
```line size=[8,6] file=data/response_pctiles.json
{
  "title": "Time to First Response (hours)",
  "x": "week",
  "y": ["p25", "p50", "p75"]
}
```

## Issue Distribution

```bar size=[8,6] file=data/age_distribution.json
{
  "title": "Open Issue Age by Type",
  "x": "age_bucket",
  "y": ["bug", "enhancement", "other"]
}
```
```bar size=[8,6] file=data/close_by_label.json
{
  "title": "Median Days to Close by Label",
  "x": "label_name",
  "y": "median_days_to_close"
}
```

## Assignee Workload

```bar size=[16,6] file=data/assignee_workload.json
{
  "title": "Open Issues by Assignee",
  "x": "assignee_login",
  "y": ["bugs", "enhancements"]
}
```

## Community Priorities

```table size=[16,6] file=data/community_priorities.json
{
  "title": "Top Reacted Open Issues",
  "columns": [
    {"id": "issue_number", "title": "#", "bold": true},
    {"id": "title", "title": "Title"},
    {"id": "issue_category", "title": "Type"},
    {"id": "reactions", "title": "Reactions", "bold": true},
    {"id": "comments", "title": "Comments"},
    {"id": "age_days", "title": "Age (days)"}
  ]
}
```
