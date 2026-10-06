import { areaY, barX, barY, defineChart, group, lineY, mountChart, stack } from '@tanstack/charts';
import { scaleBand } from '@tanstack/charts/scales/band';
import { scaleLinear } from '@tanstack/charts/scales/linear';
import { scaleOrdinal } from '@tanstack/charts/scales/ordinal';
import { scalePoint } from '@tanstack/charts/scales/point';
import { tooltip } from '@tanstack/charts/tooltip';
import snapshot from '../data/tiles.json';
import './style.css';

type Row = Record<string, string | number | boolean | null>;
type Tile = {
  id: string; title?: string; subtitle?: string; form: string;
  x?: string; y?: string; color?: string; series?: string[];
  columns?: string[]; link?: string; tooltip?: string[];
};
type Palette = Record<string, string | { light: string; dark: string; label: string }>;
type Payload = {
  manifest: {
    title: string; subtitle: string;
    palette: Record<string, Palette | string>;
    sections: { id: string; question: string; tiles: Tile[] }[];
  };
  rows: Record<string, Row[]>;
  kpis: { label: string; value: string; context: string }[];
  freshness: string; is_stale: boolean;
};
type ChartRow = { category: string; value: number | null; series: string; source: Row };
const data = snapshot as Payload;
const app = document.querySelector<HTMLElement>('#app')!;
const dark = window.matchMedia('(prefers-color-scheme: dark)');
const number = new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 });
const hosts: { destroy(): void }[] = [];

function element<K extends keyof HTMLElementTagNameMap>(tag: K, text?: string, className?: string) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}
function display(value: Row[string] | undefined): string {
  return value == null ? '—' : typeof value === 'number' ? number.format(value) : String(value);
}
function numeric(value: Row[string] | undefined): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}
function fieldLabel(value: string) {
  return value.replaceAll('_', ' ').replace(/^./, (first) => first.toUpperCase());
}
function palette(tile: Tile): Palette {
  return (data.manifest.palette[tile.form === 'grouped_bar' ? 'flow' : tile.color ?? ''] ?? {}) as Palette;
}
function color(entry: Palette[string]) {
  return typeof entry === 'string' ? entry : entry[dark.matches ? 'dark' : 'light'];
}
function seriesLabel(key: string, colors: Palette) {
  const entry = colors[key];
  return typeof entry === 'object' ? entry.label : key;
}
function legend(card: HTMLElement, colors: Palette) {
  if (!Object.keys(colors).length) return;
  const list = element('ul', undefined, 'legend');
  for (const [key, entry] of Object.entries(colors)) {
    const item = element('li');
    const swatch = element('span', undefined, 'swatch');
    swatch.style.backgroundColor = color(entry);
    swatch.setAttribute('aria-hidden', 'true');
    item.append(swatch, document.createTextNode(seriesLabel(key, colors)));
    list.append(item);
  }
  card.append(list);
}
function table(card: HTMLElement, tile: Tile, rows: Row[]) {
  const scroll = element('div', undefined, 'table-scroll');
  scroll.tabIndex = 0;
  scroll.setAttribute('role', 'region');
  scroll.setAttribute('aria-label', tile.title!);
  const grid = element('table');
  const head = element('thead');
  const headings = element('tr');
  for (const column of tile.columns ?? []) {
    const th = element('th', fieldLabel(column));
    th.scope = 'col';
    headings.append(th);
  }
  head.append(headings);
  grid.append(head);
  const body = element('tbody');
  for (const row of rows) {
    const tr = element('tr');
    for (const column of tile.columns ?? []) {
      const cell = element('td');
      if (column === 'title' && tile.link && typeof row[tile.link] === 'string') {
        const href = String(row[tile.link]);
        const link = element('a', display(row[column]));
        // Only public web links are navigable; all data is inserted as text.
        if (/^https?:\/\//i.test(href)) link.href = href;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        cell.append(link);
      } else if (tile.form === 'table_with_bar' && column === 'pct_complete') {
        const value = numeric(row[column]);
        if (value !== null) {
          const progress = element('progress');
          progress.max = 100;
          progress.value = value;
          progress.setAttribute('aria-label', `${display(row.title)} completion`);
          cell.append(progress, document.createTextNode(` ${display(value)}%`));
        } else cell.textContent = '—';
      } else cell.textContent = display(row[column]);
      tr.append(cell);
    }
    body.append(tr);
  }
  grid.append(body);
  scroll.append(grid);
  card.append(scroll);
}
function chart(card: HTMLElement, tile: Tile, rows: Row[]) {
  const horizontal = tile.form === 'horizontal_stacked_bar';
  const colors = palette(tile);
  const order = Object.keys(colors);
  const category = horizontal ? tile.y! : tile.x!;
  // Folding series columns is presentation shaping; values come directly from dbt.
  const points: ChartRow[] = tile.form === 'grouped_bar'
    ? rows.flatMap((source) => tile.series!.map((series) => ({
        category: String(source[category]), value: numeric(source[series]), series, source,
      })))
    : rows.map((source) => ({
        category: String(source[category]), value: numeric(source[horizontal ? tile.x! : tile.y!]),
        series: tile.color ? String(source[tile.color]) : '', source,
      }));
  if (!points.some((point) => point.value !== null)) {
    card.append(element('p', 'No data available.', 'empty'));
    return;
  }
  legend(card, colors);
  const container = element('div', undefined, 'chart');
  card.append(container);
  const categories = [...new Set(points.map((point) => point.category))];
  const options = {
    height: horizontal ? Math.max(250, categories.length * 30 + 55) : 290,
    initialWidth: 640,
    ariaLabel: tile.title!,
  };
  const paint = { scale: scaleOrdinal<string, string>().domain(order).range(order.map((key) => color(colors[key]))) };
  const details = {
    use: tooltip,
    format: (point: { datum: ChartRow }) => {
      const row = point.datum;
      const label = seriesLabel(row.series, colors);
      const extra = (tile.tooltip ?? []).map((key) => `${fieldLabel(key)}: ${display(row.source[key])}`);
      return [`${row.category}${label ? ` · ${label}` : ''}: ${display(row.value)}`, ...extra].join('\n');
    },
  };
  if (horizontal) {
    const definition = defineChart({
      marks: [barX(points, {
        x: 'value', y: 'category', color: 'series',
        key: (row) => `${row.category}:${row.series}`, layout: stack({ order }),
      })],
      scales: {
        x: { scale: scaleLinear, nice: true, grid: true, axis: { label: 'Issues' } },
        y: { scale: () => scaleBand<string>().domain(categories).padding(0.25) },
      },
      color: paint, tooltip: details,
    });
    hosts.push(mountChart(container, { ...options, definition }));
    return;
  }
  const mark = tile.form === 'stacked_area'
    ? areaY(points, { x: 'category', y: 'value', color: 'series', layout: stack({ order }) })
    : tile.form === 'grouped_bar'
      ? barY(points, { x: 'category', y: 'value', color: 'series', layout: group({ scale: scaleBand<string>().domain(order).padding(0.15) }) })
      : lineY(points, { x: 'category', y: 'value', stroke: String(data.manifest.palette.single_series), points: true });
  const definition = defineChart({
    marks: [mark],
    scales: {
      x: {
        scale: tile.form === 'grouped_bar'
          ? () => scaleBand<string>().domain(categories).padding(0.2)
          : () => scalePoint<string>().domain(categories).padding(0.15),
        axis: { label: 'Week', ticks: { values: categories.filter((_, i) => i % Math.max(1, Math.ceil(categories.length / 5)) === 0), format: (value) => String(value).slice(5, 10) } },
      },
      y: {
        scale: tile.form === 'line' ? () => scaleLinear().domain([0, 100]) : scaleLinear,
        nice: tile.form !== 'line', grid: true,
        axis: { label: tile.form === 'line' ? 'Answered within 48h (%)' : 'Issues' },
      },
    },
    ...(order.length ? { color: paint } : {}),
    tooltip: details,
  });
  hosts.push(mountChart(container, { ...options, definition }));
}
function render() {
  for (const host of hosts.splice(0)) host.destroy();
  app.replaceChildren();
  const header = element('header');
  header.append(element('p', 'TanStack Charts', 'framework'), element('h1', data.manifest.title), element('p', data.manifest.subtitle));
  header.append(element('p', data.freshness, data.is_stale ? 'freshness stale' : 'freshness'));
  app.append(header);
  for (const section of data.manifest.sections) {
    const sectionNode = element('section');
    sectionNode.id = section.id;
    sectionNode.append(element('h2', section.question));
    const grid = element('div', undefined, 'tiles');
    sectionNode.append(grid);
    app.append(sectionNode);
    for (const tile of section.tiles) {
      const card = element('article', undefined, 'tile');
      card.dataset.tile = tile.id;
      grid.append(card);
      if (tile.form === 'kpi_row') {
        card.classList.add('kpis');
        for (const kpi of data.kpis) {
          const item = element('div');
          item.append(element('h3', kpi.label), element('strong', kpi.value), element('p', kpi.context));
          card.append(item);
        }
      } else {
        card.append(element('h3', tile.title), element('p', tile.subtitle, 'subtitle'));
        const rows = data.rows[tile.id];
        if (!rows) throw new Error(`Missing tile data: ${tile.id}`);
        if (!rows.length) card.append(element('p', 'No data available.', 'empty'));
        else if (tile.form === 'table' || tile.form === 'table_with_bar') {
          card.classList.add('wide');
          table(card, tile, rows);
        } else chart(card, tile, rows);
      }
    }
  }
}
render();
dark.addEventListener('change', render);
window.addEventListener('pagehide', (event) => {
  if (!event.persisted) hosts.forEach((host) => host.destroy());
});
