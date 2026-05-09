import {
  RESOURCE_MIME_TYPE,
  registerAppResource,
  registerAppTool,
} from "@modelcontextprotocol/ext-apps/server";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import fs from "node:fs/promises";
import path from "node:path";

const DIST_DIR = path.join(import.meta.dirname, "dist");
const DATA_PATH = path.join(import.meta.dirname, "data", "issue-health.json");

async function loadDashboardData() {
  const raw = await fs.readFile(DATA_PATH, "utf-8");
  return JSON.parse(raw) as Record<string, unknown>;
}

function summarizeDashboard(data: Record<string, unknown>): string {
  const kpis = data.summary_kpis as Record<string, number | null>;
  const triage = data.triage_health as Record<string, number | null>;
  const openIssues = kpis.open_issues ?? "unknown";
  const opened = kpis.opened_4w ?? "unknown";
  const closed = kpis.closed_4w ?? "unknown";
  const typed = triage.pct_typed ?? "unknown";
  return `Fusion issue health: ${openIssues} open issues, ${opened} opened in the last 4 weeks, ${closed} closed in the last 4 weeks, ${typed}% typed.`;
}

export function createServer(): McpServer {
  const server = new McpServer({
    name: "Fusion Issue Health MCP App",
    version: "0.0.1",
  });

  const resourceUri = "ui://fusion-issues/issue-health.html";

  registerAppTool(
    server,
    "show_issue_health",
    {
      title: "Show Fusion Issue Health",
      description: "Open a deterministic dashboard of dbt Fusion issue health backed by dbt-modeled tables.",
      inputSchema: {},
      _meta: { ui: { resourceUri } },
    },
    async () => {
      const dashboard = await loadDashboardData();
      return {
        content: [{ type: "text", text: summarizeDashboard(dashboard) }],
        structuredContent: { dashboard },
      };
    },
  );

  registerAppResource(
    server,
    resourceUri,
    resourceUri,
    { mimeType: RESOURCE_MIME_TYPE },
    async () => {
      const html = await fs.readFile(path.join(DIST_DIR, "issue-health.html"), "utf-8");
      return {
        contents: [
          {
            uri: resourceUri,
            mimeType: RESOURCE_MIME_TYPE,
            text: html,
          },
        ],
      };
    },
  );

  return server;
}
