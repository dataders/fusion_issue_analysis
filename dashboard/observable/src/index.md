---
title: dbt-fusion Issue Health
---

# dbt-fusion Issue Health · Observable Framework

Actionable metrics for dbt-labs/dbt-fusion (excludes EPICs)

```js
const summary = await FileAttachment("data/summary.json").json();
const cumFlow = await FileAttachment("data/cumulative_flow.json").json();
const velocity = await FileAttachment("data/velocity.json").json();
const respPctiles = await FileAttachment("data/response_pctiles.json").json();
const ageDist = await FileAttachment("data/age_distribution.json").json();
const closeByLabel = await FileAttachment("data/close_by_label.json").json();
const triage = await FileAttachment("data/triage.json").json();
const assigneeWorkload = await FileAttachment("data/assignee_workload.json").json();
const communityPriorities = await FileAttachment("data/community_priorities.json").json();
```

## Key Metrics

<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:16px;margin:20px 0">

<div style="background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:16px;text-align:center">
  <div style="font-size:32px;font-weight:bold;color:#cba6f7">${summary.open_issues}</div>
  <div style="color:#a6adc8;font-size:13px">Open Issues</div>
</div>

<div style="background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:16px;text-align:center">
  <div style="font-size:32px;font-weight:bold;color:#a6e3a1">${summary.closed_4w - summary.opened_4w > 0 ? '+' : ''}${summary.closed_4w - summary.opened_4w}</div>
  <div style="color:#a6adc8;font-size:13px">Net Flow (4 wk)</div>
</div>

<div style="background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:16px;text-align:center">
  <div style="font-size:32px;font-weight:bold;color:#89dceb">${summary.rolling_median_close_days ?? 'N/A'}</div>
  <div style="color:#a6adc8;font-size:13px">Median Close (4 wk)</div>
</div>

<div style="background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:16px;text-align:center">
  <div style="font-size:32px;font-weight:bold;color:#fab387">${summary.pct_responded_48h != null ? summary.pct_responded_48h + '%' : 'N/A'}</div>
  <div style="color:#a6adc8;font-size:13px">48h Response SLA</div>
</div>

<div style="background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:16px;text-align:center">
  <div style="font-size:32px;font-weight:bold;color:#f38ba8">${summary.stale_count}</div>
  <div style="color:#a6adc8;font-size:13px">Stale Issues (30d+)</div>
</div>

</div>

## Cumulative Issue Flow

```js
Plot.plot({
  title: "Cumulative Issue Flow",
  height: 300,
  x: {type: "utc", label: "Week"},
  y: {label: "Issues", grid: true},
  marks: [
    Plot.areaY(cumFlow, {x: d => new Date(d.week), y: "cumulative_opened", fill: "#f38ba8", fillOpacity: 0.4, tip: true}),
    Plot.areaY(cumFlow, {x: d => new Date(d.week), y: "cumulative_closed", fill: "#a6e3a1", fillOpacity: 0.4, tip: true}),
    Plot.lineY(cumFlow, {x: d => new Date(d.week), y: "cumulative_opened", stroke: "#f38ba8", strokeWidth: 2}),
    Plot.lineY(cumFlow, {x: d => new Date(d.week), y: "cumulative_closed", stroke: "#a6e3a1", strokeWidth: 2}),
  ],
  color: {legend: true}
})
```

## Velocity & Response

```js
Plot.plot({
  title: "Median Days to Close: Bugs vs Enhancements",
  height: 280,
  x: {type: "utc", label: "Week"},
  y: {label: "Median Days", grid: true},
  marks: [
    Plot.lineY(velocity.filter(d => d.bugs != null), {
      x: d => new Date(d.week), y: "bugs", stroke: "#f38ba8", strokeWidth: 2, tip: true
    }),
    Plot.lineY(velocity.filter(d => d.enhancements != null), {
      x: d => new Date(d.week), y: "enhancements", stroke: "#89b4fa", strokeWidth: 2, tip: true
    }),
  ],
  color: {legend: true, domain: ["Bugs", "Enhancements"], range: ["#f38ba8", "#89b4fa"]}
})
```

```js
Plot.plot({
  title: "Time to First Response (hours)",
  height: 280,
  x: {type: "utc", label: "Week"},
  y: {label: "Hours", grid: true},
  marks: [
    Plot.lineY(respPctiles, {x: d => new Date(d.week), y: "p75", stroke: "#f38ba8", strokeWidth: 1.5, tip: true}),
    Plot.lineY(respPctiles, {x: d => new Date(d.week), y: "p50", stroke: "#89b4fa", strokeWidth: 2, tip: true}),
    Plot.lineY(respPctiles, {x: d => new Date(d.week), y: "p25", stroke: "#a6e3a1", strokeWidth: 1.5, tip: true}),
  ],
  color: {legend: true, domain: ["p75", "p50 (median)", "p25"], range: ["#f38ba8", "#89b4fa", "#a6e3a1"]}
})
```

## Issue Distribution

```js
Plot.plot({
  title: "Open Issue Age by Type",
  height: 300,
  x: {label: "Age Bucket"},
  y: {label: "Issues", grid: true},
  color: {legend: true, domain: ["bug", "enhancement", "other"], range: ["#f38ba8", "#89b4fa", "#a6adc8"]},
  marks: [
    Plot.barY(ageDist.flatMap(d => [
      {age_bucket: d.age_bucket, count: d.bug, type: "bug"},
      {age_bucket: d.age_bucket, count: d.enhancement, type: "enhancement"},
      {age_bucket: d.age_bucket, count: d.other, type: "other"},
    ]), Plot.stackY({x: "age_bucket", y: "count", fill: "type", tip: true}))
  ]
})
```

```js
Plot.plot({
  title: "Median Days to Close by Label",
  height: 360,
  marginLeft: 180,
  x: {label: "Median Days", grid: true},
  y: {label: null},
  marks: [
    Plot.barX(closeByLabel, {
      x: "median_days_to_close",
      y: "label_name",
      fill: "#89b4fa",
      tip: true,
      sort: {y: "-x"}
    })
  ]
})
```

## Triage Health

<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:20px 0">
<div style="background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:16px;text-align:center">
  <div style="font-size:28px;font-weight:bold;color:#a6e3a1">${triage.pct_labeled}%</div>
  <div style="color:#a6adc8;font-size:13px">% Labeled</div>
</div>
<div style="background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:16px;text-align:center">
  <div style="font-size:28px;font-weight:bold;color:#fab387">${triage.pct_typed}%</div>
  <div style="color:#a6adc8;font-size:13px">% Typed</div>
</div>
<div style="background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:16px;text-align:center">
  <div style="font-size:28px;font-weight:bold;color:#89dceb">${triage.pct_assigned}%</div>
  <div style="color:#a6adc8;font-size:13px">% Assigned</div>
</div>
<div style="background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:16px;text-align:center">
  <div style="font-size:28px;font-weight:bold;color:#cba6f7">${triage.pct_milestoned}%</div>
  <div style="color:#a6adc8;font-size:13px">% Milestoned</div>
</div>
</div>

## Workload & Priorities

```js
Plot.plot({
  title: "Open Issues by Assignee",
  height: 400,
  marginLeft: 140,
  x: {label: "Open Issues", grid: true},
  y: {label: null},
  color: {legend: true, domain: ["bugs", "enhancements"], range: ["#f38ba8", "#89b4fa"]},
  marks: [
    Plot.barX(assigneeWorkload.flatMap(d => [
      {assignee_login: d.assignee_login, count: d.bugs, type: "bugs"},
      {assignee_login: d.assignee_login, count: d.enhancements, type: "enhancements"},
    ]), Plot.stackX({y: "assignee_login", x: "count", fill: "type", tip: true,
      sort: {y: "-x"}}))
  ]
})
```

```js
Plot.plot({
  title: "Community Priorities",
  height: 400,
  marginLeft: 300,
  x: {label: "Reactions", grid: true},
  y: {label: null},
  color: {legend: true, domain: ["bug", "enhancement", "other"], range: ["#f38ba8", "#89b4fa", "#a6adc8"]},
  marks: [
    Plot.barX(communityPriorities, {
      x: "reactions_total_count",
      y: d => `#${d.issue_number} ${d.title.slice(0, 40)}`,
      fill: "issue_category",
      tip: true,
      sort: {y: "-x"}
    })
  ]
})
```
