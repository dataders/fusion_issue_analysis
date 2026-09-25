// Renders the tiles in dashboard/tiles.yml (passed in as `contract`) with
// Observable Plot. Used by index.md (build-time data) and live.md (MotherDuck).
// Rows arrive already sorted by each tile's order_by; this module only
// selects, renames, formats and lightly pivots model columns.
import * as Plot from "npm:@observablehq/plot";
import {html} from "npm:htl";

const COLUMN_LABELS = {
  issue_number: "#", epic_number: "#", title: "Title", issue_category: "Type",
  areas: "Areas", triage_status: "Triage", reactions: "Reactions", comments: "Comments",
  age_days: "Age (d)", days_idle: "Idle (d)", is_customer_reported: "Customer",
  child_closed: "Closed", child_total: "Sub-issues", pct_complete: "% complete",
  milestone_title: "Milestone",
};
const NUMERIC = new Set(["reactions", "comments", "age_days", "days_idle", "child_closed", "child_total", "pct_complete"]);

const fmtNumber = (v) => v == null ? "—" : Number(v).toLocaleString("en-US", {maximumFractionDigits: 1});
// Dates may arrive as ISO strings (JSON files) or Date / epoch ms (MotherDuck).
const isoDay = (v) => v instanceof Date || typeof v === "number" ? new Date(v).toISOString().slice(0, 10) : String(v).slice(0, 10);
const toDate = (v) => new Date(`${isoDay(v)}T00:00:00Z`);

export function Tiles(contract, {dark = false, resize} = {}) {
  const mode = dark ? "dark" : "light";
  const tiles = new Map(contract.sections.flatMap((s) => s.tiles.map((t) => [t.id, t])));
  const sections = new Map(contract.sections.map((s) => [s.id, s]));

  const keys = (key) => Object.keys(contract.palette[key]);
  const color = (key, name) => {
    const e = contract.palette[key][name];
    return typeof e === "string" ? e : e[mode];
  };
  const label = (key, name) => contract.palette[key]?.[name]?.label ?? name;
  const scale = (key) => ({
    domain: keys(key), range: keys(key).map((k) => color(key, k)),
    legend: true, tickFormat: (k) => label(key, k),
  });

  // KPI values: a bare column name or a "{col}" / "{col:+}" template; nulls -> "—".
  function fill(template, row) {
    const t = String(template);
    const tpl = t.includes("{") ? t : `{${t}}`;
    if ([...tpl.matchAll(/\{(\w+)(?::\+)?\}/g)].some(([, c]) => row[c] == null)) return "—";
    return tpl.replace(/\{(\w+)(:\+)?\}/g, (_, c, sign) =>
      (sign && row[c] > 0 ? "+" : "") + fmtNumber(row[c]));
  }

  function header(meta) {
    const asOf = isoDay(meta.as_of_date);
    const stale = meta.days_stale > contract.meta.stale_after_days;
    return html`<div class="tiles-header">
      <h1>${contract.title}</h1>
      <p class="tiles-subtitle">${contract.subtitle}</p>
      <p class="tiles-asof">Data as of <strong>${asOf}</strong> · ${meta.source_repo} · label ${meta.source_label}</p>
      ${stale ? html`<p class="tiles-stale" role="alert">⚠ Data is ${meta.days_stale} days old — the extract has probably stopped.</p>` : ""}
    </div>`;
  }

  const question = (sectionId) => sections.get(sectionId).question;

  function kpis(row) {
    const tile = tiles.get("headline_kpis");
    return html`<div class="grid grid-cols-3 tiles-kpis">${tile.kpis.map((k) => html`<div class="card">
      <h2>${k.label}</h2>
      <span class="big">${fill(k.value, row)}</span>
      ${k.context ? html`<div class="muted">${fill(k.context, row)}</div>` : ""}
    </div>`)}</div>`;
  }

  // ── Chart forms ──────────────────────────────────────────────────────────
  function stackedArea(tile, rows, width) {
    const order = keys(tile.color);
    return Plot.plot({
      width, height: 280,
      x: {type: "utc", label: null},
      y: {label: "Open issues", grid: true},
      color: scale(tile.color),
      marks: [
        Plot.areaY(rows, {x: (d) => toDate(d[tile.x]), y: tile.y, fill: tile.color, order, tip: true}),
        Plot.ruleY([0]),
      ],
    });
  }

  function groupedBar(tile, rows, width) {
    // Light pivot: wide series columns -> long rows for Plot's fx grouping.
    const long = rows.flatMap((d) => tile.series.map((s) => ({
      week: toDate(d[tile.x]), series: s, issues: d[s],
      ...Object.fromEntries((tile.tooltip ?? []).map((c) => [c, d[c]])),
    })));
    return Plot.plot({
      width, height: 280,
      fx: {label: null, interval: "week", tickFormat: "%b %d", ticks: 6},
      x: {axis: null, domain: tile.series},
      y: {label: "Issues", grid: true},
      color: scale("flow"),
      marks: [
        Plot.barY(long, {fx: "week", x: "series", y: "issues", fill: "series", tip: {
          channels: Object.fromEntries((tile.tooltip ?? []).map((c) => [c, c])),
        }}),
        Plot.ruleY([0]),
      ],
    });
  }

  function horizontalStackedBar(tile, rows, width) {
    const yDomain = [...new Set(rows.map((d) => d[tile.y]))]; // already ordered by order_by
    const paletteKey = tile.color;
    return Plot.plot({
      width, height: Math.max(160, 28 * yDomain.length + 60),
      marginLeft: 150,
      x: {label: "Open issues", grid: true},
      y: {label: null, domain: yDomain},
      color: scale(paletteKey),
      marks: [
        Plot.barX(rows, {y: tile.y, x: tile.x, fill: paletteKey, order: keys(paletteKey), tip: true}),
        Plot.ruleX([0]),
      ],
    });
  }

  function line(tile, rows, width) {
    return Plot.plot({
      width, height: 280,
      x: {type: "utc", label: null},
      y: {label: "% answered within 48h", domain: [0, 100], grid: true},
      marks: [
        Plot.lineY(rows, {x: (d) => toDate(d[tile.x]), y: tile.y, stroke: contract.palette.single_series, strokeWidth: 2}),
        Plot.dot(rows, {x: (d) => toDate(d[tile.x]), y: tile.y, fill: contract.palette.single_series, r: 2.5}),
        Plot.tip(rows, Plot.pointerX({
          x: (d) => toDate(d[tile.x]), y: tile.y,
          channels: Object.fromEntries((tile.tooltip ?? []).map((c) => [c, c])),
        })),
      ],
    });
  }

  function table(tile, rows) {
    const cell = (col, d) => {
      const v = d[col];
      if (col === "issue_number" || col === "epic_number" || col === "title") {
        return html`<a href=${d[tile.link]} target="_blank" rel="noopener">${col === "title" ? v : `#${v}`}</a>`;
      }
      if (col === "issue_category") return label("issue_category", v);
      if (typeof v === "boolean") return v ? "Yes" : "";
      if (col === "pct_complete" && tile.form === "table_with_bar") {
        return html`<div class="tiles-bar"><div class="track"><div style="width:${v ?? 0}%;background:${contract.palette.single_series}"></div></div><span>${fmtNumber(v)}%</span></div>`;
      }
      return NUMERIC.has(col) ? fmtNumber(v) : (v ?? "");
    };
    return html`<div class="tiles-table"><table>
      <thead><tr>${tile.columns.map((c) => html`<th class=${NUMERIC.has(c) ? "num" : ""}>${COLUMN_LABELS[c] ?? c}</th>`)}</tr></thead>
      <tbody>${rows.map((d) => html`<tr>${tile.columns.map((c) => html`<td class=${NUMERIC.has(c) ? "num" : ""}>${cell(c, d)}</td>`)}</tr>`)}</tbody>
    </table></div>`;
  }

  const FORMS = {
    stacked_area: stackedArea,
    grouped_bar: groupedBar,
    horizontal_stacked_bar: horizontalStackedBar,
    line,
    table,
    table_with_bar: table,
  };

  // One titled card per tile; charts re-render on width changes.
  function card(tileId, rows) {
    const tile = tiles.get(tileId);
    const render = FORMS[tile.form];
    if (!render) throw new Error(`No renderer for form ${tile.form} (${tileId})`);
    const body = tile.form.startsWith("table") ? render(tile, rows) : resize((width) => render(tile, rows, width));
    return html`<div class="card"><h2>${tile.title}</h2><h3>${tile.subtitle}</h3>${body}</div>`;
  }

  return {header, question, kpis, card};
}

export const css = `
.tiles-header h1 { margin-bottom: 0.2rem; }
.tiles-subtitle, .tiles-asof { margin: 0.2rem 0; color: var(--theme-foreground-muted); }
.tiles-stale { margin: 0.5rem 0; padding: 0.5rem 0.75rem; border-radius: 6px; font-weight: 600;
  border: 1px solid var(--theme-red); color: var(--theme-red); max-width: none; }
.tiles-kpis .big { font-size: 2rem; font-weight: 700; }
.tiles-table { max-height: 480px; overflow: auto; }
.tiles-table table { width: 100%; max-width: none; font-size: 0.85rem; }
.tiles-table td.num, .tiles-table th.num { text-align: right; font-variant-numeric: tabular-nums; }
.tiles-bar { display: flex; align-items: center; gap: 0.4rem; min-width: 150px; }
.tiles-bar .track { flex: 1; height: 0.7rem; background: var(--theme-foreground-faintest); border-radius: 3px; overflow: hidden; }
.tiles-bar .track > div { height: 100%; }
.tiles-bar > span { font-size: 0.8rem; min-width: 2.6em; text-align: right; font-variant-numeric: tabular-nums; }
`;
