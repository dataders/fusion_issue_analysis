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

    def test_data_builder_reads_canonical_dashboard_models(self) -> None:
        builder = BUILD_DATA.read_text()
        for model in [
            "summary_kpis",
            "triage_health",
            "issue_triage_health",
            "oldest_untriaged",
            "weekly_flow",
            "open_vs_closed_by_category",
            "community_priorities",
            "epic_list",
        ]:
            self.assertIn(f"main.{model}", builder)

    def test_data_builder_source_database_follows_dashboard_precedence(self) -> None:
        with patch.dict(os.environ, {"FUSION_DB": "custom.duckdb", "MOTHERDUCK_TOKEN": "token"}, clear=True):
            self.assertEqual(load_build_data_module().SOURCE_DB, "custom.duckdb")

        with patch.dict(os.environ, {"MOTHERDUCK_TOKEN": "token"}, clear=True):
            self.assertEqual(load_build_data_module().SOURCE_DB, "md:fusion_issues")

        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(load_build_data_module().SOURCE_DB, str(REPO_ROOT / "data" / "fusion_issues.duckdb"))

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

    def test_data_builder_enriches_agent_command_center_payload(self) -> None:
        build_data = load_build_data_module()

        payload = build_data.enrich_payload({
            "summary_kpis": {
                "opened_4w": 20,
                "closed_4w": 30,
                "open_issues": 100,
                "pct_responded_48h": 45,
                "stale_count": 12,
            },
            "triage_health": {
                "pct_labeled": 90,
                "pct_typed": 92,
                "pct_assigned": 19,
                "pct_milestoned": 4,
                "unlabeled_count": 5,
                "unassigned_count": 40,
            },
            "operational_triage": {
                "slipped_through_count": 7,
                "triage_queue_count": 9,
                "hard_blocker_count": 2,
                "hard_blocker_unreleased": 1,
                "needs_repro_count": 8,
                "repro_verified_count": 4,
                "awaiting_release_count": 3,
                "stale_count": 11,
            },
            "oldest_untriaged": [
                {"issue_number": 123, "title": "First zero-signal bug", "age_days": 45, "issue_url": "https://example.test/123"},
            ],
        })

        self.assertEqual(payload["issue_pulse"]["state"], "cooling")
        self.assertEqual(payload["issue_pulse"]["net_closed_4w"], 10)
        self.assertIn("10 more closed than opened", payload["agent_brief"]["headline"])
        self.assertEqual(payload["attention_queues"][0]["id"], "slipped-through")
        self.assertEqual(payload["attention_queues"][0]["severity"], "critical")
        self.assertEqual(payload["attention_queues"][0]["count"], 7)
        self.assertIn("#123", payload["agent_brief"]["bullets"][-1])

    def test_app_renders_agent_command_center_surfaces(self) -> None:
        html = ISSUE_HEALTH_HTML.read_text()
        app = APP_TS.read_text()

        self.assertIn('id="agent-brief"', html)
        self.assertIn('id="issue-pulse"', html)
        self.assertIn('id="attention-queues"', html)
        self.assertIn('id="oldest-untriaged"', html)
        self.assertIn("renderAgentBrief", app)
        self.assertIn("renderIssuePulse", app)
        self.assertIn("renderAttentionQueues", app)
        self.assertIn("renderOldestUntriaged", app)

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
