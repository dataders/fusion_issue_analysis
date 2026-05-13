<script lang="ts">
  import { onMount } from "svelte";
  import * as Plot from "@observablehq/plot";
  import { App } from "@modelcontextprotocol/ext-apps";
  import type {
    DashboardData,
    CategoryRow,
    WeeklyFlow,
    ResponsePctile,
  } from "./types";

  const palette = {
    orange: "#cb7a55",
    green: "#86a98f",
    purple: "#8973a8",
    blue: "#5b84a5",
    ink: "#111827",
    muted: "#64748b",
    line: "#d7dde5",
  };

  let data: DashboardData | null = null;
  let error: string | null = null;
  let selectedCategory = "";

  let weeklyFlowEl: HTMLDivElement;
  let selectedCategoryEl: HTMLDivElement;
  let allCategoriesEl: HTMLDivElement;
  let responseEl: HTMLDivElement;

  const fmt = (v: number | string | null | undefined): string => {
    const num = Number(v);
    return Number.isFinite(num) ? num.toLocaleString() : String(v ?? "");
  };

  const pct = (v: number | null | undefined): string => {
    const num = Number(v);
    return Number.isFinite(num) ? `${num}%` : "—";
  };

  onMount(async () => {
    try {
      const app = await App.connect();
      const result = await app.callTool("get_dashboard_data", {});
      data = result.structuredContent as DashboardData;
      const categories = uniqueCategories(data.categories);
      selectedCategory = categories.includes("bug") ? "bug" : categories[0] ?? "";
    } catch (err) {
      error = err instanceof Error ? err.message : String(err);
    }
  });

  function uniqueCategories(rows: CategoryRow[]): string[] {
    return Array.from(new Set(rows.map((r) => r.issue_category))).sort();
  }

  function parseWeek(week: string): Date {
    return new Date(`${week}T00:00:00Z`);
  }

  function renderWeeklyFlow(rows: WeeklyFlow[]) {
    if (!weeklyFlowEl) return;
    const long = rows.flatMap((r) => [
      { week: parseWeek(r.week), value: r.opened, series: "opened" },
      { week: parseWeek(r.week), value: r.closed, series: "closed" },
    ]);
    const chart = Plot.plot({
      height: 260,
      marginLeft: 44,
      marginBottom: 28,
      x: { label: null, type: "utc" },
      y: { label: null, grid: true },
      color: {
        domain: ["opened", "closed"],
        range: [palette.orange, palette.green],
        legend: true,
      },
      marks: [
        Plot.areaY(long, {
          x: "week",
          y: "value",
          fill: "series",
          fillOpacity: 0.15,
          curve: "monotone-x",
        }),
        Plot.lineY(long, {
          x: "week",
          y: "value",
          stroke: "series",
          strokeWidth: 2,
          curve: "monotone-x",
        }),
        Plot.ruleY([0]),
      ],
    });
    weeklyFlowEl.replaceChildren(chart);
  }

  function renderSelectedCategory(rows: CategoryRow[], category: string) {
    if (!selectedCategoryEl) return;
    const filtered = rows.filter((r) => r.issue_category === category);
    const chart = Plot.plot({
      height: 240,
      marginLeft: 44,
      marginBottom: 28,
      x: { label: null },
      y: { label: null, grid: true },
      color: {
        domain: ["OPEN", "CLOSED"],
        range: [palette.green, palette.orange],
        legend: true,
      },
      marks: [
        Plot.barY(filtered, {
          x: "state",
          y: "n",
          fill: "state",
          rx: 4,
        }),
        Plot.ruleY([0]),
        Plot.text(filtered, {
          x: "state",
          y: "n",
          text: (d) => fmt(d.n),
          dy: -8,
          fill: palette.ink,
          fontSize: 12,
        }),
      ],
    });
    selectedCategoryEl.replaceChildren(chart);
  }

  function renderAllCategories(rows: CategoryRow[]) {
    if (!allCategoriesEl) return;
    const chart = Plot.plot({
      height: 320,
      marginLeft: 44,
      marginBottom: 70,
      x: {
        label: null,
        tickRotate: -32,
      },
      y: { label: null, grid: true },
      color: {
        domain: ["OPEN", "CLOSED"],
        range: [palette.green, palette.orange],
        legend: true,
      },
      marks: [
        Plot.barY(rows, {
          x: "issue_category",
          y: "n",
          fill: "state",
          fx: "issue_category",
          dx: 0,
          rx: 3,
        }),
        Plot.ruleY([0]),
      ],
    });
    allCategoriesEl.replaceChildren(chart);
  }

  function renderResponse(rows: ResponsePctile[]) {
    if (!responseEl) return;
    const long = rows.flatMap((r) => [
      { week: parseWeek(r.week), value: r.p25, series: "p25" },
      { week: parseWeek(r.week), value: r.p50, series: "p50" },
      { week: parseWeek(r.week), value: r.p75, series: "p75" },
    ]);
    const chart = Plot.plot({
      height: 260,
      marginLeft: 44,
      marginBottom: 28,
      x: { label: null, type: "utc" },
      y: { label: "hours", grid: true },
      color: {
        domain: ["p25", "p50", "p75"],
        range: [palette.orange, palette.green, palette.purple],
        legend: true,
      },
      marks: [
        Plot.lineY(long, {
          x: "week",
          y: "value",
          stroke: "series",
          strokeWidth: 2,
          curve: "monotone-x",
        }),
        Plot.ruleY([0]),
      ],
    });
    responseEl.replaceChildren(chart);
  }

  $: if (data) {
    renderWeeklyFlow(data.weekly_flow);
    renderAllCategories(data.categories);
    renderResponse(data.response_pctiles);
  }

  $: if (data && selectedCategory) {
    renderSelectedCategory(data.categories, selectedCategory);
  }

  $: categories = data ? uniqueCategories(data.categories) : [];
  $: triage = data?.triage_health;
  $: kpis = data?.summary_kpis;
  $: priorities = (data?.community_priorities ?? []).slice(0, 10);
</script>

<main>
  <header>
    <div>
      <h1>Graphene</h1>
      <p>Fusion Issue Health</p>
    </div>
  </header>

  {#if error}
    <div class="error">Failed to load dashboard data: {error}</div>
  {:else if !data}
    <div class="loading">Loading dashboard…</div>
  {:else}
    <section class="kpis" aria-label="Summary metrics">
      <div class="kpi">
        <div class="kpi-label">Open issues</div>
        <div class="kpi-value">{fmt(kpis?.open_issues)}</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Opened, 4w</div>
        <div class="kpi-value">{fmt(kpis?.opened_4w)}</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Closed, 4w</div>
        <div class="kpi-value">{fmt(kpis?.closed_4w)}</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Stale</div>
        <div class="kpi-value">{fmt(kpis?.stale_count)}</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Responded ≤48h</div>
        <div class="kpi-value">{pct(kpis?.pct_responded_48h)}</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Median close (days)</div>
        <div class="kpi-value">{fmt(kpis?.rolling_median_close_days)}</div>
      </div>
    </section>

    <h2>Weekly issue flow</h2>
    <div class="chart" bind:this={weeklyFlowEl}></div>

    <div class="toolbar">
      <label>
        Issue category
        <select bind:value={selectedCategory}>
          {#each categories as category}
            <option value={category}>{category}</option>
          {/each}
        </select>
      </label>
    </div>
    <h2>Selected category open vs. closed</h2>
    <div class="chart" bind:this={selectedCategoryEl}></div>

    <h2>All categories overview</h2>
    <div class="chart" bind:this={allCategoriesEl}></div>

    <h2>Hours to first response</h2>
    <div class="chart" bind:this={responseEl}></div>

    <h2>Triage health</h2>
    <section class="kpis" aria-label="Triage metrics">
      <div class="kpi">
        <div class="kpi-label">Labeled</div>
        <div class="kpi-value">{pct(triage?.pct_labeled)}</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Typed</div>
        <div class="kpi-value">{pct(triage?.pct_typed)}</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Assigned</div>
        <div class="kpi-value">{pct(triage?.pct_assigned)}</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Milestoned</div>
        <div class="kpi-value">{pct(triage?.pct_milestoned)}</div>
      </div>
    </section>

    <h2>Community-prioritized open issues</h2>
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Title</th>
          <th>Type</th>
          <th class="num">Reactions</th>
          <th class="num">Comments</th>
          <th class="num">Age days</th>
        </tr>
      </thead>
      <tbody>
        {#each priorities as row}
          <tr>
            <td><a href={row.url} target="_blank" rel="noopener">{row.issue_number}</a></td>
            <td>{row.title}</td>
            <td>{row.issue_category}</td>
            <td class="num">{fmt(row.reactions_total_count)}</td>
            <td class="num">{fmt(row.comments_total_count)}</td>
            <td class="num">{fmt(row.age_days)}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  {/if}
</main>

<style>
  :global(:root) {
    color-scheme: light;
    --ink: #111827;
    --muted: #64748b;
    --line: #d7dde5;
    --panel: #f8fafc;
    --orange: #cb7a55;
    --green: #86a98f;
    --purple: #8973a8;
    --blue: #5b84a5;
  }
  :global(body) {
    margin: 0;
    background: #fff;
    color: var(--ink);
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }
  :global(*) {
    box-sizing: border-box;
  }
  main {
    max-width: 1180px;
    margin: 0 auto;
    padding: 32px 28px 44px;
  }
  header {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 20px;
    align-items: start;
    margin-bottom: 26px;
  }
  h1 {
    margin: 0;
    font-size: 30px;
    line-height: 1.15;
  }
  h2 {
    margin: 30px 0 12px;
    font-size: 16px;
    line-height: 1.3;
  }
  p {
    margin: 8px 0 0;
    color: var(--muted);
    line-height: 1.45;
  }
  .kpis {
    display: grid;
    grid-template-columns: repeat(6, minmax(0, 1fr));
    gap: 18px;
    margin-bottom: 24px;
  }
  .kpi {
    border-top: 1px solid var(--line);
    padding-top: 12px;
  }
  .kpi-label {
    color: #8b95a5;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
  }
  .kpi-value {
    margin-top: 4px;
    font-size: 26px;
    font-weight: 750;
    line-height: 1;
  }
  .toolbar {
    margin: 24px 0 4px;
    display: flex;
    align-items: end;
    gap: 16px;
  }
  label {
    display: grid;
    gap: 6px;
    font-size: 12px;
    font-weight: 650;
    color: #334155;
  }
  select {
    width: 220px;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 9px 36px 9px 11px;
    background: #fff;
    color: var(--ink);
    font: inherit;
  }
  .chart {
    width: 100%;
    min-height: 240px;
    border-bottom: 1px solid #e5e7eb;
  }
  .chart :global(svg) {
    width: 100%;
    height: auto;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
  }
  th,
  td {
    padding: 9px 10px;
    border-bottom: 1px solid #e5e7eb;
    text-align: left;
    vertical-align: top;
  }
  th {
    color: #475569;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }
  td.num,
  th.num {
    text-align: right;
  }
  a {
    color: #1f5f88;
    text-decoration: none;
  }
  a:hover {
    text-decoration: underline;
  }
  .loading,
  .error {
    padding: 24px;
    border: 1px solid var(--line);
    background: var(--panel);
    border-radius: 6px;
    color: #334155;
  }
  .error {
    border-color: #fca5a5;
    background: #fef2f2;
    color: #991b1b;
  }
  @media (max-width: 900px) {
    .kpis {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
  }
  @media (max-width: 600px) {
    main {
      padding: 22px 16px 34px;
    }
    .kpis {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    select {
      width: 100%;
    }
    .toolbar {
      display: block;
    }
  }
</style>
