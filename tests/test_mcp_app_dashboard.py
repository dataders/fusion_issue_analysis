import json
import unittest
import importlib.util
import os
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
MCP_APP_DIR = REPO_ROOT / "dashboard" / "mcp-app"
PACKAGE_JSON = MCP_APP_DIR / "package.json"
SERVER_TS = MCP_APP_DIR / "server.ts"
APP_TS = MCP_APP_DIR / "src" / "mcp-app.ts"
BUILD_DATA = MCP_APP_DIR / "build_data.py"
README = MCP_APP_DIR / "README.md"
MAKEFILE = REPO_ROOT / "Makefile"
ISSUE_HEALTH_HTML = MCP_APP_DIR / "issue-health.html"


def load_build_data_module():
    spec = importlib.util.spec_from_file_location("mcp_app_build_data", BUILD_DATA)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


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

    def test_data_builder_reads_tiles_through_shared_helper(self) -> None:
        # Tile coverage itself is enforced by tests/test_tiles_contract.py.
        builder = BUILD_DATA.read_text()
        self.assertIn("tiles.tile_rows", builder)
        self.assertIn("tiles.kpis()", builder)
        self.assertNotIn("duckdb.connect", builder)

    def test_http_server_defaults_to_loopback_and_local_cors(self) -> None:
        main = (MCP_APP_DIR / "main.ts").read_text()
        self.assertIn('process.env.MCP_APP_HOST ?? "127.0.0.1"', main)
        self.assertIn("createMcpExpressApp({ host })", main)
        self.assertIn("app.listen(port, host", main)
        self.assertIn("isAllowedOrigin", main)
        self.assertIn('"localhost"', main)
        self.assertIn('"127.0.0.1"', main)
        self.assertIn('"::1"', main)
        self.assertNotIn("app.use(cors());", main)

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
        self.assertIn("/absolute/path/to/fusion_issue_analysis/dashboard/mcp-app", readme)
        self.assertNotIn("fusion_issue_analysis.codex-mcp-ui-app-spike", readme)


if __name__ == "__main__":
    unittest.main()
