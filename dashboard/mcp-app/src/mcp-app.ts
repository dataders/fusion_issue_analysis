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

type OldestUntriaged = {
  issue_number: number;
  title: string;
  author_login: string | null;
  issue_category: string;
  reactions_total_count: number;
  comments_total_count: number;
  issue_url: string;
  age_days: number;
  days_since_activity: number;
};

type Epic = {
  epic_number: number;
  title: string;
  state: string;
  child_total: number | null;
  child_open: number | null;
  child_closed: number | null;
  pct_complete: number | null;
  reactions_total_count: number;
  comments_total_count: number;
  epic_url: string;
};

type IssuePulse = {
  state: "cooling" | "heating" | "steady";
  label: string;
  headline: string;
  opened_4w: number;
  closed_4w: number;
  net_closed_4w: number;
  response_pct_48h: number;
};

type AttentionQueue = {
  id: string;
  label: string;
  count: number;
  severity: "critical" | "warning" | "watch" | "clear";
  why: string;
  action: string;
};

type AgentBrief = {
  headline: string;
  bullets: string[];
  suggested_prompts: string[];
};

type IssueHealthPayload = {
  generated_at: string;
  summary_kpis: Kpis;
  triage_health: Kpis;
  operational_triage: Kpis;
  issue_pulse: IssuePulse;
  attention_queues: AttentionQueue[];
  agent_brief: AgentBrief;
  weekly_flow: WeeklyFlow[];
  open_vs_closed_by_category: CategoryState[];
  community_priorities: Priority[];
  open_epics: Epic[];
  oldest_untriaged: OldestUntriaged[];
};

const statusEl = document.getElementById("status")!;
const pulseEl = document.getElementById("issue-pulse")!;
const briefEl = document.getElementById("agent-brief")!;
const queuesEl = document.getElementById("attention-queues")!;
const kpisEl = document.getElementById("kpis")!;
const weeklyEl = document.getElementById("weekly-flow")!;
const categoriesEl = document.getElementById("categories")!;
const epicsEl = document.getElementById("epics")!;
const prioritiesEl = document.getElementById("priorities")!;
const oldestEl = document.getElementById("oldest-untriaged")!;
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

function renderIssuePulse(payload: IssueHealthPayload): void {
  const pulse = payload.issue_pulse;
  const netLabel =
    pulse.net_closed_4w > 0
      ? `+${numberFmt(pulse.net_closed_4w)} net closed`
      : `${numberFmt(pulse.net_closed_4w)} net closed`;
  pulseEl.className = `pulse panel ${pulse.state}`;
  pulseEl.innerHTML = `
    <p class="eyebrow">issue pulse</p>
    <h2>${escapeHtml(pulse.label)}</h2>
    <p class="pulse-headline">${escapeHtml(pulse.headline)}</p>
    <div class="pulse-metrics">
      <span><strong>${numberFmt(pulse.opened_4w)}</strong> opened</span>
      <span><strong>${numberFmt(pulse.closed_4w)}</strong> closed</span>
      <span><strong>${escapeHtml(netLabel)}</strong></span>
      <span><strong>${percentFmt(pulse.response_pct_48h)}</strong> <=48h response</span>
    </div>
  `;
}

function renderAgentBrief(payload: IssueHealthPayload): void {
  const brief = payload.agent_brief;
  briefEl.innerHTML = `
    <p class="brief-headline">${escapeHtml(brief.headline)}</p>
    <ul class="brief-list">
      ${brief.bullets.map((bullet) => `<li>${escapeHtml(bullet)}</li>`).join("")}
    </ul>
    <div class="prompt-row">
      ${brief.suggested_prompts.map((prompt) => `<span>${escapeHtml(prompt)}</span>`).join("")}
    </div>
  `;
}

function renderAttentionQueues(payload: IssueHealthPayload): void {
  queuesEl.innerHTML = payload.attention_queues
    .map((queue) => `
      <article class="queue ${queue.severity}">
        <div class="queue-top">
          <span>${escapeHtml(queue.label)}</span>
          <strong>${numberFmt(queue.count)}</strong>
        </div>
        <p>${escapeHtml(queue.why)}</p>
        <small>${escapeHtml(queue.action)}</small>
      </article>
    `)
    .join("");
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
      const done = row.pct_complete === null ? null : percentFmt(row.pct_complete * 100);
      const detail =
        row.child_total === null
          ? `${numberFmt(row.reactions_total_count)} reactions / ${numberFmt(row.comments_total_count)} comments`
          : `${numberFmt(row.child_open)} open / ${numberFmt(row.child_total)} children`;
      return `<div class="stack-item"><span><a href="${row.epic_url}">#${row.epic_number}</a> ${escapeHtml(row.title)}<br><span class="muted">${escapeHtml(detail)}</span></span><strong>${done ?? "open"}</strong></div>`;
    })
    .join("");
}

function renderPriorities(payload: IssueHealthPayload): void {
  prioritiesEl.innerHTML = payload.community_priorities
    .map((row) => `<tr><td><a href="${row.url}">#${row.issue_number}</a></td><td>${escapeHtml(row.title)}</td><td>${escapeHtml(row.issue_category)}</td><td>${numberFmt(row.reactions_total_count)}</td><td>${numberFmt(row.comments_total_count)}</td></tr>`)
    .join("");
}

function renderOldestUntriaged(payload: IssueHealthPayload): void {
  oldestEl.innerHTML = payload.oldest_untriaged
    .map((row) => {
      const signals = `${numberFmt(row.reactions_total_count)} reactions / ${numberFmt(row.comments_total_count)} comments`;
      return `<tr><td><a href="${row.issue_url}">#${row.issue_number}</a></td><td>${escapeHtml(row.title)}</td><td>${numberFmt(row.age_days)}d</td><td>${numberFmt(row.days_since_activity)}d</td><td>${escapeHtml(signals)}</td></tr>`;
    })
    .join("");
}

function render(payload: IssueHealthPayload): void {
  statusEl.textContent = `Snapshot generated ${new Date(payload.generated_at).toLocaleString()}.`;
  renderIssuePulse(payload);
  renderAgentBrief(payload);
  renderAttentionQueues(payload);
  renderKpis(payload);
  renderWeekly(payload);
  renderCategories(payload);
  renderEpics(payload);
  renderOldestUntriaged(payload);
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
