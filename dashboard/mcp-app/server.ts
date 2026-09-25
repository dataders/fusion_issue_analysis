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

type Kpi = { label: string; value: string; context: string };

/** Agent-facing text: the pre-formatted KPI row plus the freshness note. */
function summarizeDashboard(data: Record<string, unknown>): string {
  const kpis = (data.kpis as Kpi[] | undefined) ?? [];
  const lines = kpis.map((k) => `- ${k.label}: ${k.value}${k.context ? ` (${k.context})` : ""}`);
  return [String(data.freshness_note ?? ""), ...lines].filter(Boolean).join("\n");
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
      description: "Open the dbt Fusion (engine:v2) issue health dashboard: every tile in dashboard/tiles.yml, backed by dbt dashboard models.",
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
