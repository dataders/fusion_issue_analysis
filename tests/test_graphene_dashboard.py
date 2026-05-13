import importlib.util
import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = REPO_ROOT / "dashboard" / "index.html"
MAKEFILE = REPO_ROOT / "Makefile"
PACKAGE_JSON = REPO_ROOT / "dashboard" / "graphene" / "package.json"
GRAPHENE_PAGE = REPO_ROOT / "dashboard" / "graphene" / "index.md"
GRAPHENE_MODEL = REPO_ROOT / "dashboard" / "graphene" / "tables" / "fusion_issue_metrics.gsql"
GRAPHENE_BUILD = REPO_ROOT / "dashboard" / "graphene" / "build.py"
PR_PREVIEW_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "pr-preview.yml"
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"
DEPLOY_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "deploy-dashboard.yml"


class GrapheneDashboardTests(unittest.TestCase):
    def test_bakeoff_tab_points_to_static_graphene_page(self) -> None:
        content = INDEX_HTML.read_text()
        self.assertIn("Graphene", content)
        self.assertIn('data-src="graphene/index.html"', content)
        self.assertIn('data-tab="graphene"', content)

    def test_makefile_and_workflows_build_graphene_tab(self) -> None:
        makefile = MAKEFILE.read_text()
        preview = PR_PREVIEW_WORKFLOW.read_text()
        ci = CI_WORKFLOW.read_text()
        deploy = DEPLOY_WORKFLOW.read_text()

        self.assertIn("graphene", makefile)
        self.assertIn("uv run python3 dashboard/graphene/build.py", makefile)
        self.assertIn("npm --prefix dashboard/graphene ci", makefile)
        self.assertIn("npm exec graphene -- check", makefile)
        self.assertIn("dashboard/graphene/index.html", makefile)

        for content in (preview, ci, deploy):
            self.assertIn("Build Graphene tab", content)
            self.assertIn("make graphene", content)

        self.assertIn("preview/graphene", preview)
        self.assertIn("| Graphene | \\`graphene/index.html\\` |", preview)

    def test_graphene_project_pins_public_cli_and_local_duckdb(self) -> None:
        package = json.loads(PACKAGE_JSON.read_text())
        self.assertEqual(package["graphene"]["duckdb"]["path"], "fusion_graphene.duckdb")
        self.assertEqual(package["dependencies"]["@graphenedata/cli"], "0.0.18")
        self.assertIn("@duckdb/node-api", package["dependencies"])

    def test_graphene_page_uses_canonical_metric_tables(self) -> None:
        page = GRAPHENE_PAGE.read_text()
        model = GRAPHENE_MODEL.read_text()
        self.assertIn("from summary_kpis", page)
        self.assertIn("from weekly_flow", page)
        self.assertIn("from community_priorities", page)
        self.assertIn("where issue_category = $category", page)
        self.assertIn("table summary_kpis", model)
        self.assertIn("table response_pctiles", model)

    def test_static_renderer_explains_export_boundary(self) -> None:
        spec = importlib.util.spec_from_file_location("graphene_build", GRAPHENE_BUILD)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        sys.path.insert(0, str(GRAPHENE_BUILD.parent))
        spec.loader.exec_module(module)

        html = module.render_static_page(
            {
                "summary_kpis": [
                    {
                        "open_issues": 10,
                        "opened_4w": 3,
                        "closed_4w": 4,
                        "pct_responded_48h": 50,
                    }
                ],
                "weekly_flow": [{"week": "2026-01-05", "opened": 3, "closed": 4}],
                "open_vs_closed_by_category": [
                    {"issue_category": "bug", "state": "OPEN", "n": 2},
                    {"issue_category": "bug", "state": "CLOSED", "n": 8},
                ],
                "triage_health": [
                    {
                        "pct_labeled": 90,
                        "pct_typed": 80,
                        "pct_assigned": 20,
                        "pct_milestoned": 5,
                    }
                ],
                "response_pctiles": [{"week": "2026-01-05", "p25": 1, "p50": 2, "p75": 3}],
                "community_priorities": [
                    {
                        "issue_number": 1,
                        "title": "Example",
                        "issue_category": "bug",
                        "reactions_total_count": 5,
                        "comments_total_count": 2,
                        "age_days": 7,
                        "url": "https://github.com/dbt-labs/dbt-fusion/issues/1",
                    }
                ],
            }
        )
        self.assertIn("Graphene", html)
        self.assertIn("static Pages export", html)
        self.assertIn("graphene/index.md", html)
        self.assertIn("window.__GRAPHENE_DATA__", html)


if __name__ == "__main__":
    unittest.main()
