import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MCP_APP_DIR = REPO_ROOT / "dashboard" / "mcp-app"
PACKAGE_JSON = MCP_APP_DIR / "package.json"
SERVER_TS = MCP_APP_DIR / "server.ts"
APP_TS = MCP_APP_DIR / "src" / "mcp-app.ts"
BUILD_DATA = MCP_APP_DIR / "build_data.py"
README = MCP_APP_DIR / "README.md"
MAKEFILE = REPO_ROOT / "Makefile"


class McpAppDashboardTests(unittest.TestCase):
    def test_package_declares_mcp_apps_runtime(self) -> None:
        package = json.loads(PACKAGE_JSON.read_text())
        self.assertEqual(package["name"], "fusion-issue-analysis-mcp-app")
        self.assertIn("@modelcontextprotocol/ext-apps", package["dependencies"])
        self.assertIn("@modelcontextprotocol/sdk", package["dependencies"])
        self.assertEqual(package["scripts"]["build"], "tsc --noEmit && tsc -p tsconfig.server.json && cross-env INPUT=issue-health.html vite build")

    def test_server_registers_dashboard_tool_and_ui_resource(self) -> None:
        server = SERVER_TS.read_text()
        self.assertIn('const resourceUri = "ui://fusion-issues/issue-health.html"', server)
        self.assertIn('registerAppTool(', server)
        self.assertIn('"show_issue_health"', server)
        self.assertIn("_meta: { ui: { resourceUri } }", server)
        self.assertIn("structuredContent", server)
        self.assertIn("registerAppResource(", server)
        self.assertIn("RESOURCE_MIME_TYPE", server)

    def test_view_connects_to_host_and_supports_app_refresh(self) -> None:
        app = APP_TS.read_text()
        self.assertIn('new App({ name: "Fusion Issue Health"', app)
        self.assertIn("app.ontoolresult", app)
        self.assertIn("app.callServerTool", app)
        self.assertIn('"show_issue_health"', app)
        self.assertIn("app.connect()", app)

    def test_data_builder_reads_canonical_dashboard_models(self) -> None:
        builder = BUILD_DATA.read_text()
        for model in [
            "summary_kpis",
            "triage_health",
            "weekly_flow",
            "open_vs_closed_by_category",
            "community_priorities",
            "fct_epics",
        ]:
            self.assertIn(f"main.{model}", builder)

    def test_makefile_has_local_mcp_app_targets(self) -> None:
        makefile = MAKEFILE.read_text()
        self.assertIn("mcp-app", makefile)
        self.assertIn("uv run python dashboard/mcp-app/build_data.py", makefile)
        self.assertIn("npm --prefix dashboard/mcp-app ci", makefile)
        self.assertIn("PORT=$(MCP_APP_PORT) npm --prefix dashboard/mcp-app start", makefile)

    def test_readme_documents_claude_desktop_config(self) -> None:
        readme = README.read_text()
        self.assertIn("Claude Desktop", readme)
        self.assertIn('"fusion-issue-health"', readme)
        self.assertIn("--stdio", readme)
        self.assertIn("MCP Apps", readme)


if __name__ == "__main__":
    unittest.main()
