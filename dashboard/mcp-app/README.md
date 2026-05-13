# Fusion Issue Health MCP App

Local-only MCP Apps spike for the dashboard bakeoff. The point is to test the
Layer 7 question from the About page: an agent can open an issue-health command
center while the data path stays deterministic.

The app registers one MCP tool, `show_issue_health`, and links it to one UI
resource, `ui://fusion-issues/issue-health.html`. The tool returns an agent
briefing for the model plus `structuredContent.dashboard` for the iframe UI:
issue pulse, attention queues, oldest zero-signal bugs, epics, flow, and
community-priority tables.

```bash
make mcp-app
make mcp-app-serve
```

`make mcp-app` snapshots canonical dbt dashboard models into
`dashboard/mcp-app/data/issue-health.json` and bundles the iframe UI into
`dashboard/mcp-app/dist/issue-health.html`.

Fresh worktrees usually do not have `data/fusion_issues.duckdb`. Either run
`make dbt` first, or point the app at a checkout with data:

```bash
FUSION_PROJECT_ROOT=/Users/dataders/Developer/fusion_issue_analysis make mcp-app
```

To try it in Claude Desktop, add this to `claude_desktop_config.json` after
running `make mcp-app`:

```json
{
  "mcpServers": {
    "fusion-issue-health": {
      "command": "npm",
      "args": ["--prefix", "/Users/dataders/Developer/fusion_issue_analysis.codex-mcp-ui-app-spike/dashboard/mcp-app", "run", "start:stdio"]
    }
  }
}
```

The `start:stdio` script runs `tsx main.ts --stdio`, which is the local
transport Claude Desktop expects. Then ask Claude to show the Fusion issue
health dashboard. For HTTP transport, `make mcp-app-serve` starts the server at
`http://localhost:3001/mcp`.
