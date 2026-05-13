---
title: dbt-fusion Issue Health (Live)
---

# dbt-fusion Issue Health · Observable + MotherDuck live

Data fetched at page load from MotherDuck — no build-time bake.

```js
import {MDConnection} from "@motherduck/wasm-client";

const TOKEN = "__MOTHERDUCK_READ_TOKEN__";

const conn = await (async () => {
  if (!TOKEN || TOKEN.startsWith("__")) return null;
  const c = MDConnection.create({mdToken: TOKEN});
  await c.isInitialized();
  return c;
})();

const CACHE_TTL = 60 * 60 * 1000;

async function queryRows(conn, sql) {
  const key = `md:${btoa(sql).slice(0, 40)}`;
  const hit = sessionStorage.getItem(key);
  if (hit) {
    const {rows, ts} = JSON.parse(hit);
    if (Date.now() - ts < CACHE_TTL) return rows;
  }
  const result = await conn.evaluateQuery(sql);
  const rows = result.data.toRows();
  sessionStorage.setItem(key, JSON.stringify({rows, ts: Date.now()}, (_, v) => typeof v === "bigint" ? Number(v) : v));
  return rows;
}

async function queryOne(conn, sql) {
  return (await queryRows(conn, sql))[0] ?? {};
}
```

```js
const [triageHealth, summary, triage, oldestUntriaged, cumFlow, velocity,
       respPctiles, ageDist, closeByLabel, assigneeWorkload, communityPriorities] =
  conn ? await Promise.all([
    queryOne(conn, "SELECT * FROM fusion_issues.main.issue_triage_health"),
    queryOne(conn, "SELECT * FROM fusion_issues.main.summary_kpis"),
    queryOne(conn, "SELECT * FROM fusion_issues.main.triage_health"),
    queryRows(conn, "SELECT * FROM fusion_issues.main.oldest_untriaged ORDER BY age_days DESC"),
    queryRows(conn, "SELECT * FROM fusion_issues.main.cumulative_flow ORDER BY week"),
    queryRows(conn, `SELECT week, max(CASE WHEN issue_category='bug' THEN median_days END) AS bugs, max(CASE WHEN issue_category='enhancement' THEN median_days END) AS enhancements FROM fusion_issues.main.velocity GROUP BY week ORDER BY week`),
    queryRows(conn, "SELECT * FROM fusion_issues.main.response_pctiles ORDER BY week"),
    queryRows(conn, "SELECT age_bucket, issue_category, issue_count FROM fusion_issues.main.age_distribution ORDER BY CASE age_bucket WHEN '0-7d' THEN 1 WHEN '8-30d' THEN 2 WHEN '31-90d' THEN 3 WHEN '91-180d' THEN 4 ELSE 5 END"),
    queryRows(conn, "SELECT * FROM fusion_issues.main.close_by_label ORDER BY median_days_to_close DESC"),
    queryRows(conn, "SELECT * FROM fusion_issues.main.assignee_workload ORDER BY open_issues DESC"),
    queryRows(conn, "SELECT * FROM fusion_issues.main.community_priorities ORDER BY reactions_total_count DESC"),
  ]) : Array(11).fill({});
```

${conn == null ? html`<p style="color:#f38ba8;font-style:italic">Token not injected — run the deploy workflow to see live data.</p>` : ""}

## Daily triage

<div style="display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin:20px 0">
<div style="background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:16px;text-align:center">
  <div style="font-size:28px;font-weight:bold;color:#f38ba8">${triageHealth.slipped_through_count ?? "—"}</div>
  <div style="color:#a6adc8;font-size:13px">Slipped through (bugs)</div>
</div>
<div style="background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:16px;text-align:center">
  <div style="font-size:28px;font-weight:bold;color:#fab387">${triageHealth.triage_queue_count ?? "—"}</div>
  <div style="color:#a6adc8;font-size:13px">Triage queue</div>
</div>
<div style="background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:16px;text-align:center">
  <div style="font-size:28px;font-weight:bold;color:#eba0ac">${triageHealth.hard_blocker_count ?? "—"}</div>
  <div style="color:#a6adc8;font-size:13px">Hard blockers</div>
</div>
<div style="background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:16px;text-align:center">
  <div style="font-size:28px;font-weight:bold;color:#cba6f7">${triageHealth.stale_count ?? "—"}</div>
  <div style="color:#a6adc8;font-size:13px">Stale</div>
</div>
<div style="background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:16px;text-align:center">
  <div style="font-size:28px;font-weight:bold;color:#89dceb">${triageHealth.needs_repro_count ?? "—"}</div>
  <div style="color:#a6adc8;font-size:13px">Needs repro</div>
</div>
<div style="background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:16px;text-align:center">
  <div style="font-size:28px;font-weight:bold;color:#a6e3a1">${triageHealth.repro_verified_count ?? "—"}</div>
  <div style="color:#a6adc8;font-size:13px">Repro verified</div>
</div>
</div>

### Oldest untriaged bugs

<table style="width:100%;border-collapse:collapse;margin:12px 0">
  <thead>
    <tr style="border-bottom:1px solid #313244;color:#a6adc8;text-align:left">
      <th style="padding:8px">Issue</th><th style="padding:8px">Title</th><th style="padding:8px;text-align:right">Age (days)</th>
    </tr>
  </thead>
  <tbody>
    ${(Array.isArray(oldestUntriaged) ? oldestUntriaged : []).map(d => html`<tr style="border-bottom:1px solid #313244">
      <td style="padding:8px"><a href="${d.issue_url}" style="color:#89b4fa">#${d.issue_number}</a></td>
      <td style="padding:8px">${d.title}</td>
      <td style="padding:8px;text-align:right;color:#f38ba8;font-weight:bold">${d.age_days}</td>
    </tr>`)}
  </tbody>
</table>

## Key metrics

<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:16px;margin:20px 0">
<div style="background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:16px;text-align:center">
  <div style="font-size:32px;font-weight:bold;color:#cba6f7">${summary.open_issues ?? "—"}</div>
  <div style="color:#a6adc8;font-size:13px">Open issues</div>
</div>
<div style="background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:16px;text-align:center">
  <div style="font-size:32px;font-weight:bold;color:#a6e3a1">${summary.closed_4w != null && summary.opened_4w != null ? (summary.closed_4w - summary.opened_4w > 0 ? "+" : "") + (summary.closed_4w - summary.opened_4w) : "—"}</div>
  <div style="color:#a6adc8;font-size:13px">Net flow (4 wk)</div>
</div>
<div style="background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:16px;text-align:center">
  <div style="font-size:32px;font-weight:bold;color:#89dceb">${summary.rolling_median_close_days ?? "N/A"}</div>
  <div style="color:#a6adc8;font-size:13px">Median close (4 wk)</div>
</div>
<div style="background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:16px;text-align:center">
  <div style="font-size:32px;font-weight:bold;color:#fab387">${summary.pct_responded_48h != null ? summary.pct_responded_48h + "%" : "N/A"}</div>
  <div style="color:#a6adc8;font-size:13px">48h response SLA</div>
</div>
<div style="background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:16px;text-align:center">
  <div style="font-size:32px;font-weight:bold;color:#f38ba8">${summary.stale_count ?? "—"}</div>
  <div style="color:#a6adc8;font-size:13px">Stale (30d+)</div>
</div>
</div>

## Cumulative issue flow

```js
Plot.plot({
  height: 300,
  x: {type: "utc", label: "Week"},
  y: {label: "Issues", grid: true},
  color: {legend: true},
  marks: [
    Plot.areaY(cumFlow.map(d => ({...d, week: new Date(d.week)})), {x: "week", y: "cumulative_opened", fill: "#f38ba8", fillOpacity: 0.4, tip: true}),
    Plot.areaY(cumFlow.map(d => ({...d, week: new Date(d.week)})), {x: "week", y: "cumulative_closed", fill: "#a6e3a1", fillOpacity: 0.4, tip: true}),
    Plot.lineY(cumFlow.map(d => ({...d, week: new Date(d.week)})), {x: "week", y: "cumulative_opened", stroke: "#f38ba8", strokeWidth: 2}),
    Plot.lineY(cumFlow.map(d => ({...d, week: new Date(d.week)})), {x: "week", y: "cumulative_closed", stroke: "#a6e3a1", strokeWidth: 2}),
  ],
})
```

## Velocity & response

```js
Plot.plot({
  height: 280,
  x: {type: "utc", label: "Week"},
  y: {label: "Median days", grid: true},
  color: {legend: true, domain: ["Bugs", "Enhancements"], range: ["#f38ba8", "#89b4fa"]},
  marks: [
    Plot.lineY(velocity.filter(d => d.bugs != null).map(d => ({...d, week: new Date(d.week)})), {x: "week", y: "bugs", stroke: "#f38ba8", strokeWidth: 2, tip: true}),
    Plot.lineY(velocity.filter(d => d.enhancements != null).map(d => ({...d, week: new Date(d.week)})), {x: "week", y: "enhancements", stroke: "#89b4fa", strokeWidth: 2, tip: true}),
  ],
})
```

```js
Plot.plot({
  height: 280,
  x: {type: "utc", label: "Week"},
  y: {label: "Hours", grid: true},
  color: {legend: true, domain: ["p75", "p50 (median)", "p25"], range: ["#f38ba8", "#89b4fa", "#a6e3a1"]},
  marks: [
    Plot.lineY(respPctiles.map(d => ({...d, week: new Date(d.week)})), {x: "week", y: "p75", stroke: "#f38ba8", strokeWidth: 1.5, tip: true}),
    Plot.lineY(respPctiles.map(d => ({...d, week: new Date(d.week)})), {x: "week", y: "p50", stroke: "#89b4fa", strokeWidth: 2, tip: true}),
    Plot.lineY(respPctiles.map(d => ({...d, week: new Date(d.week)})), {x: "week", y: "p25", stroke: "#a6e3a1", strokeWidth: 1.5, tip: true}),
  ],
})
```

## Issue distribution

```js
Plot.plot({
  height: 300,
  x: {label: "Age bucket"},
  y: {label: "Issues", grid: true},
  color: {legend: true, domain: ["bug", "enhancement", "other"], range: ["#f38ba8", "#89b4fa", "#a6adc8"]},
  marks: [
    Plot.barY(ageDist, Plot.stackY({x: "age_bucket", y: "issue_count", fill: "issue_category", tip: true})),
  ],
})
```

```js
Plot.plot({
  height: 360,
  marginLeft: 180,
  x: {label: "Median days", grid: true},
  y: {label: null},
  marks: [
    Plot.barX(closeByLabel, {x: "median_days_to_close", y: "label_name", fill: "#89b4fa", tip: true, sort: {y: "-x"}}),
  ],
})
```

## Triage health

<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:20px 0">
<div style="background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:16px;text-align:center">
  <div style="font-size:28px;font-weight:bold;color:#a6e3a1">${triage.pct_labeled ?? "—"}%</div>
  <div style="color:#a6adc8;font-size:13px">% Labeled</div>
</div>
<div style="background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:16px;text-align:center">
  <div style="font-size:28px;font-weight:bold;color:#fab387">${triage.pct_typed ?? "—"}%</div>
  <div style="color:#a6adc8;font-size:13px">% Typed</div>
</div>
<div style="background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:16px;text-align:center">
  <div style="font-size:28px;font-weight:bold;color:#89dceb">${triage.pct_assigned ?? "—"}%</div>
  <div style="color:#a6adc8;font-size:13px">% Assigned</div>
</div>
<div style="background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:16px;text-align:center">
  <div style="font-size:28px;font-weight:bold;color:#cba6f7">${triage.pct_milestoned ?? "—"}%</div>
  <div style="color:#a6adc8;font-size:13px">% Milestoned</div>
</div>
</div>

## Workload & priorities

```js
Plot.plot({
  height: 400,
  marginLeft: 140,
  x: {label: "Open issues", grid: true},
  y: {label: null},
  marks: [
    Plot.barX(assigneeWorkload, {x: "open_issues", y: "assignee_login", fill: "#89b4fa", tip: true, sort: {y: "-x"}}),
  ],
})
```

```js
Plot.plot({
  height: 400,
  marginLeft: 300,
  x: {label: "Reactions", grid: true},
  y: {label: null},
  color: {legend: true, domain: ["bug", "enhancement", "other"], range: ["#f38ba8", "#89b4fa", "#a6adc8"]},
  marks: [
    Plot.barX(communityPriorities, {
      x: "reactions_total_count",
      y: d => `#${d.issue_number} ${String(d.title).slice(0, 40)}`,
      fill: "issue_category",
      tip: true,
      sort: {y: "-x"},
    }),
  ],
})
```
