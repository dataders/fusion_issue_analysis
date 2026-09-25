# Fusion Issue Health MCP App

Local-only MCP Apps spike for the dashboard bakeoff. The point is to test the
Layer 7 question from the About page: an agent can open an issue-health command
center while the data path stays deterministic.

The app registers one MCP tool, `show_issue_health`, and links it to one UI
resource, `ui://fusion-issues/issue-health.html`. The tool returns the
formatted KPI row and freshness note as text for the model, plus
`structuredContent.dashboard` for the iframe UI: the `dashboard/tiles.yml`
manifest and the rows of every tile model. The widget renders every section
and tile from that manifest generically (KPI row, stacked area, grouped bar,
line, horizontal stacked bars, tables), follows the host light/dark theme, and
uses the manifest palette.

```bash
make mcp-app
make mcp-app-serve
```

`make mcp-app` snapshots canonical dbt dashboard models into
`dashboard/mcp-app/data/issue-health.json` and bundles the iframe UI into
`dashboard/mcp-app/dist/issue-health.html`.

Fresh worktrees usually do not have `data/fusion_issues.duckdb`. Either run
`make dbt` first, or point the app at a DuckDB file with the dashboard models
(`build_data.py` resolves the database via `dashboard/tiles.py`: `FUSION_DB`,
then MotherDuck when `MOTHERDUCK_TOKEN` is set, then the local dev DB):

```bash
FUSION_DB=/Users/dataders/Developer/fusion_issue_analysis/data/fusion_issues.duckdb make mcp-app
```

To try it in Claude Desktop, add this to `claude_desktop_config.json` after
running `make mcp-app`. Replace `/absolute/path/to/fusion_issue_analysis` with
the absolute path to your checkout:

```json
{
  "mcpServers": {
    "fusion-issue-health": {
      "command": "npm",
      "args": ["--prefix", "/absolute/path/to/fusion_issue_analysis/dashboard/mcp-app", "run", "start:stdio"]
    }
  }
}
```

The `start:stdio` script runs `tsx main.ts --stdio`, which is the local
transport Claude Desktop expects. Then ask Claude to show the Fusion issue
health dashboard. For HTTP transport, `make mcp-app-serve` starts the server at
`http://127.0.0.1:3001/mcp` by default. Set `MCP_APP_HOST` only when you
intentionally want to bind another interface.
