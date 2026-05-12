// Mosaic + MotherDuck live connector
//
// Connector pattern from motherduckdb/wasm-client examples/mosaic-integration:
//   - MDConnection.create({mdToken}) from @motherduck/wasm-client
//   - evaluateStreamingQuery() + @uwdata/flechette for result handling
//   - coordinator().databaseConnector(connector) to wire into Mosaic
//   - vg.plot(), vg.barY(), vg.barX(), vg.from(), vg.Selection from @uwdata/vgplot v0.25.x

import {Table, tableToIPC} from 'apache-arrow';
import {tableFromIPC} from '@uwdata/flechette';
import {MDConnection} from '@motherduck/wasm-client';
import * as vg from '@uwdata/vgplot';

const TOKEN = (window.__MD_TOKEN__ && !window.__MD_TOKEN__.startsWith('__')) ? window.__MD_TOKEN__ : '';
const status = document.getElementById('status');

if (!TOKEN) {
  status.textContent = 'Token not injected — run deploy workflow.';
  status.className = 'error';
} else {
  setup().catch(err => {
    status.textContent = `Error: ${err.message}`;
    status.className = 'error';
    console.error(err);
  });
}

function makeMDConnector(connection) {
  return {
    query: async (query) => {
      const {sql, type} = query;
      if (type === 'exec') {
        await connection.evaluateQuery(sql);
        return undefined;
      }
      const result = await connection.evaluateStreamingQuery(sql);
      if (result.type !== 'streaming') {
        throw new Error('expected streaming result from MotherDuck');
      }
      const batches = await result.arrowStream.readAll();
      const ipcBytes = tableToIPC(new Table(batches));
      const table = tableFromIPC(ipcBytes, {useDate: true});
      switch (type) {
        case 'arrow':
          return table;
        case 'json':
          return table.toArray();
        default:
          return undefined;
      }
    },
  };
}

async function setup() {
  const connection = MDConnection.create({mdToken: TOKEN});
  await connection.isInitialized();

  // Wire the Mosaic coordinator to MotherDuck
  vg.coordinator().databaseConnector(makeMDConnector(connection));

  // Ensure the fusion_issues database is attached
  await vg.coordinator().exec("ATTACH IF NOT EXISTS 'md:fusion_issues' AS fusion_issues;");

  status.textContent = 'Connected. Rendering charts…';

  // Crossfilter selection: clicking an age bucket filters the workload chart
  const sel = vg.Selection.crossfilter();

  const app = document.getElementById('app');

  // --- Chart 1: Issue age distribution by category ---
  const ageTitle = document.createElement('div');
  ageTitle.className = 'chart-title';
  ageTitle.textContent = 'Open issues by age bucket';

  const ageHint = document.createElement('div');
  ageHint.className = 'hint';
  ageHint.textContent = 'Click a bar to filter the workload chart below.';

  const ageChart = vg.plot(
    vg.barY(
      vg.from('fusion_issues.main.age_distribution', {filterBy: sel}),
      {
        x: 'age_bucket',
        y: vg.sum('issue_count'),
        fill: 'issue_category',
        tip: true,
      }
    ),
    vg.toggleX({as: sel}),
    vg.colorLegend(),
    vg.xLabel('Age bucket'),
    vg.yLabel('Open issues'),
    vg.style({background: 'transparent', color: '#cdd6f4'}),
    vg.width(700),
    vg.height(280)
  );

  // --- Chart 2: Assignee workload (filtered by age selection) ---
  const workloadTitle = document.createElement('div');
  workloadTitle.className = 'chart-title';
  workloadTitle.textContent = 'Assignee workload (filtered by age selection)';

  const workloadChart = vg.plot(
    vg.barX(
      vg.from('fusion_issues.main.assignee_workload', {filterBy: sel}),
      {
        y: 'assignee',
        x: 'open_issues',
        fill: '#89b4fa',
        tip: true,
        sort: {y: '-x'},
      }
    ),
    vg.xLabel('Open issues'),
    vg.yLabel(null),
    vg.style({background: 'transparent', color: '#cdd6f4'}),
    vg.width(700),
    vg.height(320)
  );

  app.append(ageTitle, ageHint, ageChart, workloadTitle, workloadChart);
  status.textContent = 'Data loaded live from MotherDuck (Mosaic).';
}
