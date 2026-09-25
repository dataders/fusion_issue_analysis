---
title: dbt Fusion issue health
toc: false
---

```js
// Tile contract (dashboard/tiles.yml) + one build-time JSON file per dbt dashboard model.
import {Tiles, css} from "./components/tiles.js";

const contract = await FileAttachment("data/tiles.json").json();
const dashboard_meta = await FileAttachment("data/dashboard_meta.json").json();
const headline_kpis = await FileAttachment("data/headline_kpis.json").json();
const backlog_weekly = await FileAttachment("data/backlog_weekly.json").json();
const weekly_flow = await FileAttachment("data/weekly_flow.json").json();
const triage_pipeline = await FileAttachment("data/triage_pipeline.json").json();
const response_weekly = await FileAttachment("data/response_weekly.json").json();
const triage_queue = await FileAttachment("data/triage_queue.json").json();
const open_by_area = await FileAttachment("data/open_by_area.json").json();
const open_by_adapter = await FileAttachment("data/open_by_adapter.json").json();
const epic_progress = await FileAttachment("data/epic_progress.json").json();
const top_requested = await FileAttachment("data/top_requested.json").json();
const assignee_workload = await FileAttachment("data/assignee_workload.json").json();
```

```js
const T = Tiles(contract, {dark, resize});
display(html`<style>${css}</style>`);
```

<div class="grid grid-cols-1">${T.header(dashboard_meta)}</div>

## ${T.question("status")}

<div class="grid grid-cols-1">${T.kpis(headline_kpis)}</div>

## ${T.question("backlog")}

<div class="grid grid-cols-2">
  ${T.card("backlog_weekly", backlog_weekly)}
  ${T.card("weekly_flow", weekly_flow)}
</div>

## ${T.question("triage")}

<div class="grid grid-cols-2">
  ${T.card("triage_pipeline", triage_pipeline)}
  ${T.card("response_weekly", response_weekly)}
</div>

<div class="grid grid-cols-1">${T.card("triage_queue", triage_queue)}</div>

## ${T.question("where")}

<div class="grid grid-cols-2">
  ${T.card("open_by_area", open_by_area)}
  ${T.card("open_by_adapter", open_by_adapter)}
</div>

## ${T.question("epics")}

<div class="grid grid-cols-1">${T.card("epic_progress", epic_progress)}</div>

## ${T.question("next")}

<div class="grid grid-cols-1">${T.card("top_requested", top_requested)}</div>

<div class="grid grid-cols-1">${T.card("assignee_workload", assignee_workload)}</div>
