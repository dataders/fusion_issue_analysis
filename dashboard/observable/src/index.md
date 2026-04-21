---
title: dbt-fusion Issue Health
---

# dbt-fusion Issue Health · Observable Framework


```js
const data = await FileAttachment("data/summary.json").json();
const {summary, flow, velocity, triage, top_issues} = data;
```

## Summary

<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:20px 0">

<div style="background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:16px;text-align:center">
  <div style="font-size:32px;font-weight:bold;color:#cba6f7">${summary.open_issues}</div>
  <div style="color:#a6adc8;font-size:13px">Open Issues</div>
</div>

<div style="background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:16px;text-align:center">
  <div style="font-size:32px;font-weight:bold;color:#a6e3a1">${summary.closed_4w - summary.opened_4w > 0 ? '+' : ''}${summary.closed_4w - summary.opened_4w}</div>
  <div style="color:#a6adc8;font-size:13px">Net Flow (4 wk)</div>
</div>

<div style="background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:16px;text-align:center">
  <div style="font-size:32px;font-weight:bold;color:#89dceb">${summary.median_close_days ?? 'N/A'}</div>
  <div style="color:#a6adc8;font-size:13px">Median Close Days (4 wk)</div>
</div>

<div style="background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:16px;text-align:center">
  <div style="font-size:32px;font-weight:bold;color:#f38ba8">${summary.stale_count}</div>
  <div style="color:#a6adc8;font-size:13px">Stale Issues (30+ days)</div>
</div>

</div>

## Issue Flow

```js
Plot.plot({
  title: "Weekly Opened vs Closed",
  height: 300,
  x: {type: "utc", label: "Week"},
  y: {label: "Issues", grid: true},
  marks: [
    Plot.areaY(flow, {x: d => new Date(d.week), y: "opened", fill: "#f38ba8", fillOpacity: 0.4, tip: true}),
    Plot.areaY(flow, {x: d => new Date(d.week), y: "closed", fill: "#a6e3a1", fillOpacity: 0.4, tip: true}),
    Plot.lineY(flow, {x: d => new Date(d.week), y: "opened", stroke: "#f38ba8", strokeWidth: 2}),
    Plot.lineY(flow, {x: d => new Date(d.week), y: "closed", stroke: "#a6e3a1", strokeWidth: 2}),
  ],
  color: {legend: true}
})
```

## Resolution Velocity (Median Days to Close)

```js
Plot.plot({
  title: "Bug vs Enhancement Velocity",
  height: 280,
  x: {type: "utc", label: "Week"},
  y: {label: "Median Days", grid: true},
  color: {legend: true, domain: ["bug", "enhancement"], range: ["#f38ba8", "#89b4fa"]},
  marks: [
    Plot.lineY(velocity.filter(d => d.issue_category === "bug"), {
      x: d => new Date(d.week), y: "median_days", stroke: "#f38ba8", strokeWidth: 2, tip: true
    }),
    Plot.lineY(velocity.filter(d => d.issue_category === "enhancement"), {
      x: d => new Date(d.week), y: "median_days", stroke: "#89b4fa", strokeWidth: 2, tip: true
    }),
  ]
})
```

## Triage Health

<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:20px 0">
<div style="background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:16px;text-align:center">
  <div style="font-size:28px;font-weight:bold;color:#a6e3a1">${triage.pct_labeled}%</div>
  <div style="color:#a6adc8;font-size:13px">Labeled</div>
</div>
<div style="background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:16px;text-align:center">
  <div style="font-size:28px;font-weight:bold;color:#89dceb">${triage.pct_assigned}%</div>
  <div style="color:#a6adc8;font-size:13px">Assigned</div>
</div>
<div style="background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:16px;text-align:center">
  <div style="font-size:28px;font-weight:bold;color:#cba6f7">${triage.pct_milestoned}%</div>
  <div style="color:#a6adc8;font-size:13px">In Milestone</div>
</div>
</div>

## Top Community Priorities

```js
Plot.plot({
  title: "Most-Reacted Open Issues",
  height: 400,
  marginLeft: 300,
  x: {label: "Reactions", grid: true},
  y: {label: null},
  marks: [
    Plot.barX(top_issues, {
      x: "reactions_total_count",
      y: d => `#${d.issue_number} ${d.title.slice(0,40)}`,
      fill: d => d.issue_category === "bug" ? "#f38ba8" : "#89b4fa",
      tip: true,
      sort: {y: "-x"}
    })
  ]
})
```
