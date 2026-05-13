# Graphene tab

This directory contains the Graphene project used for the bakeoff tab:

- `tables/fusion_issue_metrics.gsql` defines the semantic model over dashboard-ready extracts.
- `index.md` is the Graphene dashboard source.
- `build.py` materializes a local DuckDB snapshot, validates the Graphene project, and writes the GitHub Pages-compatible `index.html`.

Graphene currently serves pages through its local server rather than a static export command. The production tab therefore renders a static compatibility artifact from the same canonical dbt dashboard models while keeping the Graphene source files in the repo and validating them with the public Graphene CLI.

## MCP App (Claude Desktop)

`mcp_server.py` is a FastMCP server that builds the snapshot on startup and exposes the rendered dashboard as a `ui://` resource. Add this to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "fusion-graphene": {
      "command": "uv",
      "args": ["run", "/path/to/fusion_issue_analysis/dashboard/graphene/mcp_server.py"],
      "env": {
        "FUSION_DB": "md:fusion_issues"
      }
    }
  }
}
```

Then ask Claude to "show the Fusion issue health dashboard".
