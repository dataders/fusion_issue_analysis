import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const transport = new StdioClientTransport({
  command: "npm",
  args: ["run", "start:stdio"],
});

const client = new Client({
  name: "fusion-issue-health-smoke",
  version: "0.0.1",
});

try {
  await client.connect(transport);
  const tools = await client.listTools();
  const issueHealth = tools.tools.find((tool) => tool.name === "show_issue_health");
  if (!issueHealth?._meta?.ui) {
    throw new Error("show_issue_health is missing MCP Apps UI metadata");
  }

  const result = await client.callTool({
    name: "show_issue_health",
    arguments: {},
  });

  const dashboard = result.structuredContent?.dashboard;
  if (!dashboard?.models?.headline_kpis || !dashboard?.manifest?.sections?.length) {
    throw new Error("show_issue_health did not return dashboard structured content");
  }
  const missing = dashboard.manifest.sections
    .flatMap((section) => section.tiles.map((tile) => tile.model))
    .filter((model) => !(model in dashboard.models));
  if (missing.length) throw new Error(`payload is missing tile models: ${missing.join(", ")}`);

  console.log(result.content?.[0]?.text ?? "MCP app smoke passed");
} finally {
  await client.close();
}
