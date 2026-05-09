import { App } from "@modelcontextprotocol/ext-apps";
import "./style.css";

type Kpis = Record<string, number | null>;

type WeeklyFlow = {
  week: string;
  opened: number;
  closed: number;
};

type CategoryState = {
  issue_category: string;
  state: string;
  n: number;
};

type Priority = {
  issue_number: number;
  title: string;
  issue_category: string;
  reactions_total_count: number;
  comments_total_count: number;
  url: string;
};

type Epic = {
  epic_number: number;
  title: string;
  state: string;
  child_total: number;
  child_open: number;
  child_closed: number;
  pct_complete: number | null;
  epic_url: string;
};

type IssueHealthPayload = {
  generated_at: string;
  summary_kpis: Kpis;
  triage_health: Kpis;
  weekly_flow: WeeklyFlow[];
  open_vs_closed_by_category: CategoryState[];
  community_priorities: Priority[];
  open_epics: Epic[];
};

const statusEl = document.getElementById("status")!;
const kpisEl = document.getElementById("kpis")!;
const weeklyEl = document.getElementById("weekly-flow")!;
const categoriesEl = document.getElementById("categories")!;
const epicsEl = document.getElementById("epics")!;
const prioritiesEl = document.getElementById("priorities")!;
const refreshBtn = document.getElementById("refresh") as HTMLButtonElement;

const app = new App({ name: "Fusion Issue Health", version: "0.0.1" });

function numberFmt(value: number | null | undefined): string {
  if (value === null || value === undefined) return "n/a";
  return new Intl.NumberFormat().format(value);
}

function percentFmt(value: number | null | undefined): string {
  if (value === null || value === undefined) return "n/a";
  return `${Math.round(value)}%`;
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (char) => {
    const escapes: Record<string, string> = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    };
    return escapes[char];
  });
}

function readPayload(result: unknown): IssueHealthPayload | null {
  if (!result || typeof result !== "object") return null;
  const maybe = result as { structuredContent?: { dashboard?: IssueHealthPayload } };
  return maybe.structuredContent?.dashboard ?? null;
}

function renderKpis(payload: IssueHealthPayload): void {
  const cards = [
    ["Open issues", numberFmt(payload.summary_kpis.open_issues)],
    ["Opened, 4w", numberFmt(payload.summary_kpis.opened_4w)],
    ["Closed, 4w", numberFmt(payload.summary_kpis.closed_4w)],
    ["Responded <=48h", percentFmt(payload.summary_kpis.pct_responded_48h)],
    ["Typed", percentFmt(payload.triage_health.pct_typed)],
    ["Milestoned", percentFmt(payload.triage_health.pct_milestoned)],
  ];

  kpisEl.innerHTML = cards
    .map(([label, value]) => `<article class="kpi"><div class="label">${label}</div><div class="value">${value}</div></article>`)
    .join("");
}

function renderWeekly(payload: IssueHealthPayload): void {
  const recent = payload.weekly_flow.slice(-12);
  const max = Math.max(...recent.flatMap((row) => [row.opened, row.closed]), 1);
  weeklyEl.innerHTML = recent
    .flatMap((row) => [
      `<div class="bar-row"><span>${row.week}</span><div class="bar" style="width:${(row.opened / max) * 100}%"></div><span>${row.opened} opened</span></div>`,
      `<div class="bar-row"><span></span><div class="bar closed" style="width:${(row.closed / max) * 100}%"></div><span>${row.closed} closed</span></div>`,
    ])
    .join("");
}

function renderCategories(payload: IssueHealthPayload): void {
  categoriesEl.innerHTML = payload.open_vs_closed_by_category
    .map((row) => {
      const label = `${row.issue_category} ${row.state.toLowerCase()}`;
      return `<div class="stack-item"><span>${escapeHtml(label)}</span><strong>${numberFmt(row.n)}</strong></div>`;
    })
    .join("");
}

function renderEpics(payload: IssueHealthPayload): void {
  epicsEl.innerHTML = payload.open_epics
    .map((row) => {
      const done = row.pct_complete === null ? "n/a" : percentFmt(row.pct_complete * 100);
      return `<div class="stack-item"><span><a href="${row.epic_url}">#${row.epic_number}</a> ${escapeHtml(row.title)}<br><span class="muted">${row.child_open} open / ${row.child_total} children</span></span><strong>${done}</strong></div>`;
    })
    .join("");
}

function renderPriorities(payload: IssueHealthPayload): void {
  prioritiesEl.innerHTML = payload.community_priorities
    .map((row) => `<tr><td><a href="${row.url}">#${row.issue_number}</a></td><td>${escapeHtml(row.title)}</td><td>${escapeHtml(row.issue_category)}</td><td>${numberFmt(row.reactions_total_count)}</td><td>${numberFmt(row.comments_total_count)}</td></tr>`)
    .join("");
}

function render(payload: IssueHealthPayload): void {
  statusEl.textContent = `Snapshot generated ${new Date(payload.generated_at).toLocaleString()}.`;
  renderKpis(payload);
  renderWeekly(payload);
  renderCategories(payload);
  renderEpics(payload);
  renderPriorities(payload);
}

app.ontoolresult = (result) => {
  const payload = readPayload(result);
  if (!payload) {
    statusEl.textContent = "Tool result did not include dashboard structured content.";
    return;
  }
  render(payload);
};

refreshBtn.addEventListener("click", async () => {
  refreshBtn.disabled = true;
  statusEl.textContent = "Refreshing from MCP server...";
  try {
    const result = await app.callServerTool({ name: "show_issue_health", arguments: {} });
    const payload = readPayload(result);
    if (payload) render(payload);
  } catch (error) {
    statusEl.textContent = error instanceof Error ? error.message : "Refresh failed.";
  } finally {
    refreshBtn.disabled = false;
  }
});

app.connect();
