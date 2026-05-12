---
title: dbt-fusion Issue Health (Live)
---

# dbt-fusion Issue Health · Observable + MotherDuck live

Data fetched at page load from MotherDuck via DuckDB WASM — no build-time bake.

```js
import {MDConnection} from "@motherduck/wasm-client";

const TOKEN = "__MOTHERDUCK_READ_TOKEN__";

const conn = await (async () => {
  if (!TOKEN || TOKEN.startsWith("__")) return null;
  const c = MDConnection.create({mdToken: TOKEN});
  await c.isInitialized();
  return c;
})();

async function queryRows(conn, sql) {
  const result = await conn.evaluateStreamingQuery(sql);
  const table = await result.arrowStream.readAll();
  return [...table].map(row => Object.fromEntries(row));
}
```

```js
const triageHealth = conn
  ? (await queryRows(conn, "SELECT * FROM fusion_issues.main.issue_triage_health"))[0]
  : null;
```

${triageHealth == null
  ? html`<p style="color:#f38ba8">Token not injected — run the deploy workflow to see live data.</p>`
  : html`<div style="display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin:20px 0">
      ${[
        ["slipped_through_count", "#f38ba8", "Slipped through"],
        ["triage_queue_count",    "#fab387", "Triage queue"],
        ["hard_blocker_count",   "#eba0ac", "Hard blockers"],
        ["needs_repro_count",    "#89dceb", "Needs repro"],
        ["repro_verified_count", "#a6e3a1", "Repro verified"],
        ["stale_count",          "#cba6f7", "Stale"],
      ].map(([k, color, label]) =>
        html`<div style="background:#313244;border-radius:8px;padding:16px;text-align:center">
          <div style="font-size:2rem;font-weight:bold;color:${color}">${triageHealth[k] ?? "—"}</div>
          <div style="color:#a6adc8;font-size:.75rem;margin-top:4px">${label}</div>
        </div>`
      )}
    </div>`}

```js
const velocity = conn
  ? await queryRows(conn, `
      SELECT week,
        max(CASE WHEN issue_category = 'bug' THEN median_days END) AS bugs,
        max(CASE WHEN issue_category = 'enhancement' THEN median_days END) AS enhancements
      FROM fusion_issues.main.velocity GROUP BY week ORDER BY week
    `)
  : [];
```

```js
Plot.plot({
  color: {legend: true},
  marks: [
    Plot.lineY(velocity, {x: "week", y: "bugs", stroke: "#f38ba8", tip: true}),
    Plot.lineY(velocity, {x: "week", y: "enhancements", stroke: "#89b4fa", tip: true}),
  ]
})
```
