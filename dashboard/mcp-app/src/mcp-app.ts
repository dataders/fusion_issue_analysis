import { App, applyDocumentTheme } from "@modelcontextprotocol/ext-apps";
import "./style.css";

// Renders dashboard/tiles.yml generically. build_data.py bakes the manifest and
// the rows of every tile model (dashboard_meta, headline_kpis, backlog_weekly,
// weekly_flow, triage_pipeline, response_weekly, triage_queue, open_by_area,
// open_by_adapter, epic_progress, top_requested, assignee_workload), already
// sorted per the manifest's order_by. This file only lays out and encodes.

type Row = Record<string, unknown>;
type PaletteEntry = string | { light: string; dark: string; label?: string };
type Palette = Record<string, Record<string, PaletteEntry> | string>;

type Tile = {
  id: string;
  model: string;
  form: string;
  title?: string;
  subtitle?: string;
  x?: string;
  y?: string;
  color?: string;
  series?: string[];
  tooltip?: string[];
  columns?: string[];
  link?: string;
};

type Section = { id: string; question: string; tiles: Tile[] };

type Payload = {
  generated_at: string;
  manifest: { title: string; subtitle: string; palette: Palette; sections: Section[] };
  freshness_note: string;
  is_stale: boolean;
  kpis: { label: string; value: string; context: string }[];
  models: Record<string, Row[] | Row>;
};

const titleEl = document.getElementById("title")!;
const subtitleEl = document.getElementById("subtitle")!;
const freshnessEl = document.getElementById("freshness")!;
const statusEl = document.getElementById("status")!;
const sectionsEl = document.getElementById("sections")!;
const refreshBtn = document.getElementById("refresh") as HTMLButtonElement;

const app = new App({ name: "Fusion Issue Health", version: "0.1.0" });

// ---------- formatting ----------

const HEADERS: Record<string, string> = {
  issue_number: "#",
  epic_number: "#",
  issue_category: "Type",
  age_days: "Age (d)",
  days_idle: "Idle (d)",
  is_customer_reported: "Customer",
  triage_status: "Triage",
  child_closed: "Closed",
  child_total: "Sub-issues",
  pct_complete: "% closed",
  milestone_title: "Milestone",
};

function esc(value: unknown): string {
  return String(value ?? "").replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
}

function num(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  return typeof value === "number" ? new Intl.NumberFormat().format(value) : String(value);
}

function header(column: string): string {
  return HEADERS[column] ?? column.replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase());
}

function slug(value: string): string {
  return value.replace(/[^a-z0-9]+/gi, "-");
}

// ---------- palette -> CSS custom properties (light + dark) ----------

let palette: Palette = {};

function paletteGroup(key: string): Record<string, PaletteEntry> {
  const group = palette[key];
  return typeof group === "object" ? group : {};
}

function colorVar(key: string, name: string): string {
  return `var(--pal-${key}-${slug(name)}, var(--pal-single))`;
}

function seriesLabel(key: string, name: string): string {
  const entry = paletteGroup(key)[name];
  return typeof entry === "object" && entry.label ? entry.label : name;
}

function installPalette(p: Palette): void {
  palette = p;
  const light: string[] = [];
  const dark: string[] = [];
  for (const [key, group] of Object.entries(p)) {
    if (typeof group === "string") {
      light.push(`--pal-single:${group};`);
      continue;
    }
    for (const [name, entry] of Object.entries(group)) {
      const prop = `--pal-${key}-${slug(name)}`;
      light.push(`${prop}:${typeof entry === "string" ? entry : entry.light};`);
      dark.push(`${prop}:${typeof entry === "string" ? entry : entry.dark};`);
    }
  }
  let style = document.getElementById("palette-vars");
  if (!style) {
    style = document.createElement("style");
    style.id = "palette-vars";
    document.head.appendChild(style);
  }
  style.textContent =
    `:root{${light.join("")}}` +
    `@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){${dark.join("")}}}` +
    `:root[data-theme="dark"]{${dark.join("")}}`;
}

/** Series keys in palette order, limited to those present in the rows. */
function seriesOrder(key: string, rows: Row[]): string[] {
  const present = new Set(rows.map((r) => String(r[key])));
  const ordered = Object.keys(paletteGroup(key)).filter((k) => present.has(k));
  return [...ordered, ...[...present].filter((k) => !ordered.includes(k))];
}

function unique(rows: Row[], key: string): string[] {
  return [...new Set(rows.map((r) => String(r[key])))];
}

function legend(key: string, names: string[]): string {
  if (names.length < 2) return "";
  return `<div class="legend">${names
    .map((n) => `<span><i style="background:${colorVar(key, n)}"></i>${esc(seriesLabel(key, n))}</span>`)
    .join("")}</div>`;
}

// ---------- SVG chart frame ----------

const W = 640;
const H = 220;
const PAD = { l: 44, r: 12, t: 10, b: 26 };
const plotW = W - PAD.l - PAD.r;
const plotH = H - PAD.t - PAD.b;

function niceMax(value: number): number {
  if (value <= 0) return 1;
  const mag = 10 ** Math.floor(Math.log10(value));
  const step = [1, 2, 2.5, 5, 10].find((s) => s * mag >= value / 4)! * mag;
  return Math.ceil(value / step) * step;
}

function yScale(max: number) {
  return (v: number) => PAD.t + plotH - (v / max) * plotH;
}

function axes(max: number, xLabels: string[], suffix = ""): string {
  const y = yScale(max);
  const ticks = [0, max / 4, max / 2, (3 * max) / 4, max];
  const grid = ticks
    .map((t) => `<line class="grid" x1="${PAD.l}" x2="${W - PAD.r}" y1="${y(t)}" y2="${y(t)}"/>` +
      `<text class="tick" x="${PAD.l - 6}" y="${y(t) + 4}" text-anchor="end">${num(Math.round(t))}${suffix}</text>`)
    .join("");
  const n = xLabels.length;
  const picks = n <= 1 ? [0] : [0, Math.floor((n - 1) / 2), n - 1];
  const xs = picks
    .map((i) => {
      const x = PAD.l + (n <= 1 ? plotW / 2 : (i / (n - 1)) * plotW);
      const anchor = i === 0 ? "start" : i === n - 1 ? "end" : "middle";
      return `<text class="tick" x="${x}" y="${H - 8}" text-anchor="${anchor}">${esc(xLabels[i])}</text>`;
    })
    .join("");
  return grid + xs;
}

function svg(body: string, label: string): string {
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(label)}">${body}</svg>`;
}

// ---------- tile forms ----------

function stackedArea(tile: Tile, rows: Row[]): string {
  const [xKey, yKey, cKey] = [tile.x!, tile.y!, tile.color!];
  const xs = unique(rows, xKey);
  const series = seriesOrder(cKey, rows);
  const value = new Map(rows.map((r) => [`${r[xKey]}|${r[cKey]}`, Number(r[yKey] ?? 0)]));
  const cum = xs.map(() => 0);
  const layers = series.map((s) => {
    const lower = [...cum];
    xs.forEach((x, i) => (cum[i] += value.get(`${x}|${s}`) ?? 0));
    return { s, lower, upper: [...cum] };
  });
  const max = niceMax(Math.max(...cum, 1));
  const y = yScale(max);
  const xAt = (i: number) => PAD.l + (xs.length <= 1 ? 0 : (i / (xs.length - 1)) * plotW);
  const paths = layers
    .map(({ s, lower, upper }) => {
      const top = upper.map((v, i) => `${xAt(i)},${y(v)}`);
      const bottom = lower.map((v, i) => `${xAt(i)},${y(v)}`).reverse();
      return `<path d="M${top.join("L")}L${bottom.join("L")}Z" fill="${colorVar(cKey, s)}"><title>${esc(seriesLabel(cKey, s))}</title></path>`;
    })
    .join("");
  const bandW = plotW / Math.max(xs.length, 1);
  const hovers = xs
    .map((x, i) => {
      const tip = [x, ...series.map((s) => `${seriesLabel(cKey, s)}: ${num(value.get(`${x}|${s}`) ?? 0)}`)].join("\n");
      return `<rect class="hover" x="${xAt(i) - bandW / 2}" y="${PAD.t}" width="${bandW}" height="${plotH}"><title>${esc(tip)}</title></rect>`;
    })
    .join("");
  return legend(cKey, series) + svg(axes(max, xs) + paths + hovers, tile.title ?? tile.id);
}

function groupedBar(tile: Tile, rows: Row[]): string {
  const xKey = tile.x!;
  const series = tile.series ?? [];
  const xs = rows.map((r) => String(r[xKey]));
  const max = niceMax(Math.max(...rows.flatMap((r) => series.map((s) => Number(r[s] ?? 0))), 1));
  const y = yScale(max);
  const band = plotW / Math.max(rows.length, 1);
  const barW = (band * 0.8) / Math.max(series.length, 1);
  const bars = rows
    .map((r, i) => {
      const tip = [r[xKey], ...series.map((s) => `${seriesLabel("flow", s)}: ${num(r[s])}`),
        ...(tile.tooltip ?? []).map((t) => `${header(t)}: ${num(r[t])}`)].join("\n");
      const x0 = PAD.l + i * band + band * 0.1;
      return `<g><title>${esc(tip)}</title>${series
        .map((s, j) => {
          const v = Number(r[s] ?? 0);
          return `<rect x="${x0 + j * barW}" y="${y(v)}" width="${Math.max(barW - 1, 1)}" height="${PAD.t + plotH - y(v)}" fill="${colorVar("flow", s)}"/>`;
        })
        .join("")}<rect class="hover" x="${PAD.l + i * band}" y="${PAD.t}" width="${band}" height="${plotH}"/></g>`;
    })
    .join("");
  return legend("flow", series) + svg(axes(max, xs) + bars, tile.title ?? tile.id);
}

function line(tile: Tile, rows: Row[]): string {
  const [xKey, yKey] = [tile.x!, tile.y!];
  const xs = rows.map((r) => String(r[xKey]));
  const max = 100; // pct 0-100
  const y = yScale(max);
  const xAt = (i: number) => PAD.l + (rows.length <= 1 ? plotW / 2 : (i / (rows.length - 1)) * plotW);
  const pts = rows
    .map((r, i) => (r[yKey] === null || r[yKey] === undefined ? null : [xAt(i), y(Number(r[yKey])), r] as const))
    .filter((p): p is readonly [number, number, Row] => p !== null);
  const path = `<polyline class="line" fill="none" stroke="var(--pal-single)" points="${pts.map(([x, yy]) => `${x},${yy}`).join(" ")}"/>`;
  const dots = pts
    .map(([x, yy, r]) => {
      const tip = [r[xKey], `${header(yKey)}: ${num(r[yKey])}%`, ...(tile.tooltip ?? []).map((t) => `${header(t)}: ${num(r[t])}`)].join("\n");
      return `<circle cx="${x}" cy="${yy}" r="3.5" fill="var(--pal-single)"><title>${esc(tip)}</title></circle>`;
    })
    .join("");
  return svg(axes(max, xs, "%") + path + dots, tile.title ?? tile.id);
}

function horizontalStackedBar(tile: Tile, rows: Row[]): string {
  const [yKey, xKey, cKey] = [tile.y!, tile.x!, tile.color!];
  const cats = unique(rows, yKey); // rows arrive sorted per tiles.yml order_by
  const series = seriesOrder(cKey, rows);
  const value = new Map(rows.map((r) => [`${r[yKey]}|${r[cKey]}`, Number(r[xKey] ?? 0)]));
  const totals = cats.map((c) => series.reduce((sum, s) => sum + (value.get(`${c}|${s}`) ?? 0), 0));
  const max = Math.max(...totals, 1); // layout only: longest bar = full width
  // Show the model's own total column (e.g. area_total) when it has one.
  const totalKey = `${yKey}_total`;
  const modelTotal = new Map(rows.map((r) => [String(r[yKey]), r[totalKey]]));
  const bars = cats
    .map((c) => {
      const segs = series
        .map((s) => {
          const v = value.get(`${c}|${s}`) ?? 0;
          if (!v) return "";
          return `<span class="seg" style="width:${(v / max) * 100}%;background:${colorVar(cKey, s)}" title="${esc(`${c} · ${seriesLabel(cKey, s)}: ${num(v)}`)}"></span>`;
        })
        .join("");
      return `<div class="hbar"><span class="hbar-label" title="${esc(c)}">${esc(c)}</span><span class="hbar-track">${segs}</span><span class="hbar-total">${totalKey in rows[0] ? num(modelTotal.get(c)) : ""}</span></div>`;
    })
    .join("");
  return legend(cKey, series) + `<div class="hbars">${bars}</div>`;
}

function cell(tile: Tile, row: Row, column: string): string {
  const v = row[column];
  const url = tile.link ? String(row[tile.link] ?? "") : "";
  if ((column === "issue_number" || column === "epic_number") && url) {
    return `<a href="${esc(url)}" target="_blank" rel="noopener">#${esc(v)}</a>`;
  }
  if (column === "title" && url) return `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(v)}</a>`;
  if (column === "issue_category") {
    return `<span class="tag"><i style="background:${colorVar("issue_category", String(v))}"></i>${esc(seriesLabel("issue_category", String(v)))}</span>`;
  }
  if (column === "pct_complete" && tile.form === "table_with_bar") {
    const pct = Number(v ?? 0);
    return `<span class="pct"><span class="pct-track"><span style="width:${pct}%"></span></span>${num(v)}%</span>`;
  }
  if (typeof v === "boolean") return v ? "Yes" : "—";
  if (v === "" || v === null || v === undefined) return "—";
  return typeof v === "number" ? num(v) : esc(v);
}

function table(tile: Tile, rows: Row[]): string {
  const cols = tile.columns ?? [];
  const numeric = (c: string) => rows.some((r) => typeof r[c] === "number") && c !== "issue_number" && c !== "epic_number";
  const head = cols.map((c) => `<th class="${numeric(c) ? "num" : ""}">${esc(header(c))}</th>`).join("");
  const body = rows
    .map((r) => `<tr>${cols.map((c) => `<td class="${numeric(c) ? "num" : ""} col-${c}">${cell(tile, r, c)}</td>`).join("")}</tr>`)
    .join("");
  return `<div class="table-wrap"><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
}

function kpiRow(payload: Payload): string {
  return `<div class="kpi-grid">${payload.kpis
    .map((k) => `<article class="kpi"><div class="label">${esc(k.label)}</div><div class="value">${esc(k.value)}</div>${k.context ? `<div class="context">${esc(k.context)}</div>` : ""}</article>`)
    .join("")}</div>`;
}

const FORMS: Record<string, (tile: Tile, rows: Row[]) => string> = {
  stacked_area: stackedArea,
  grouped_bar: groupedBar,
  line,
  horizontal_stacked_bar: horizontalStackedBar,
  table,
  table_with_bar: table,
};

function renderTile(tile: Tile, payload: Payload): string {
  if (tile.form === "kpi_row") return kpiRow(payload);
  const rows = (payload.models[tile.model] as Row[] | undefined) ?? [];
  const render = FORMS[tile.form];
  const body = !rows.length
    ? `<p class="muted">No rows in ${esc(tile.model)}.</p>`
    : render
      ? render(tile, rows)
      : `<p class="muted">Unsupported form ${esc(tile.form)}.</p>`;
  const wide = tile.form.startsWith("table") ? " wide" : "";
  return `<article class="panel tile${wide}" id="tile-${esc(tile.id)}">
    ${tile.title ? `<h3>${esc(tile.title)}</h3>` : ""}
    ${tile.subtitle ? `<p class="subtitle">${esc(tile.subtitle)}</p>` : ""}
    ${body}
  </article>`;
}

function render(payload: Payload): void {
  const { manifest } = payload;
  installPalette(manifest.palette);
  titleEl.textContent = manifest.title;
  subtitleEl.textContent = manifest.subtitle;
  freshnessEl.textContent = payload.freshness_note;
  freshnessEl.className = payload.is_stale ? "freshness stale" : "freshness";
  statusEl.textContent = `Snapshot baked ${new Date(payload.generated_at).toLocaleString()}.`;
  sectionsEl.innerHTML = manifest.sections
    .map((s) => {
      const onlyKpis = s.tiles.every((t) => t.form === "kpi_row");
      return `<section class="dash-section" id="section-${esc(s.id)}">
        <h2>${esc(s.question)}</h2>
        <div class="${onlyKpis ? "" : "tile-grid"}">${s.tiles.map((t) => renderTile(t, payload)).join("")}</div>
      </section>`;
    })
    .join("");
}

function readPayload(result: unknown): Payload | null {
  if (!result || typeof result !== "object") return null;
  const maybe = result as { structuredContent?: { dashboard?: Payload } };
  return maybe.structuredContent?.dashboard ?? null;
}

// Links inside the sandboxed iframe go through the host.
document.addEventListener("click", (event) => {
  const anchor = (event.target as HTMLElement).closest?.("a[href^='http']") as HTMLAnchorElement | null;
  if (!anchor) return;
  event.preventDefault();
  app.openLink({ url: anchor.href }).catch(() => window.open(anchor.href, "_blank", "noopener"));
});

app.ontoolresult = (result) => {
  const payload = readPayload(result);
  if (!payload) {
    statusEl.textContent = "Tool result did not include dashboard structured content.";
    return;
  }
  render(payload);
};

app.onhostcontextchanged = (ctx) => {
  if (ctx.theme) applyDocumentTheme(ctx.theme);
};

refreshBtn.addEventListener("click", async () => {
  refreshBtn.disabled = true;
  statusEl.textContent = "Refreshing from MCP server...";
  try {
    const payload = readPayload(await app.callServerTool({ name: "show_issue_health", arguments: {} }));
    if (payload) render(payload);
  } catch (error) {
    statusEl.textContent = error instanceof Error ? error.message : "Refresh failed.";
  } finally {
    refreshBtn.disabled = false;
  }
});

app.connect().then(() => {
  const theme = app.getHostContext()?.theme;
  if (theme) applyDocumentTheme(theme);
});
