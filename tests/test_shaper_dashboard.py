import importlib.util
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = REPO_ROOT / "dashboard" / "index.html"
MAKEFILE = REPO_ROOT / "Makefile"
PR_PREVIEW_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "pr-preview.yml"
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"
DEPLOY_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "deploy-dashboard.yml"
SHAPER_DIR = REPO_ROOT / "dashboard" / "shaper"
SHAPER_SQL = SHAPER_DIR / "fusion-issue-health.dashboard.sql"
SHAPER_BUILD = SHAPER_DIR / "build.py"


class ShaperDashboardTests(unittest.TestCase):
    def test_bakeoff_tab_points_to_shaper_static_page(self) -> None:
        content = INDEX_HTML.read_text()
        self.assertIn("Shaper", content)
        self.assertIn('data-src="shaper/index.html"', content)
        self.assertIn('data-tab="shaper"', content)

    def test_makefile_and_workflows_build_shaper_tab(self) -> None:
        makefile = MAKEFILE.read_text()
        preview = PR_PREVIEW_WORKFLOW.read_text()
        ci = CI_WORKFLOW.read_text()
        deploy = DEPLOY_WORKFLOW.read_text()

        self.assertIn("shaper", makefile)
        self.assertIn("uv run python3 dashboard/shaper/build.py", makefile)
        for content in (preview, ci, deploy):
            self.assertIn("uv run python3 dashboard/shaper/build.py", content)

        self.assertIn("preview/shaper", preview)
        self.assertIn("| Shaper | `shaper/index.html` |", preview)

    def test_shaper_dashboard_source_uses_shaper_sql_types(self) -> None:
        sql = SHAPER_SQL.read_text()
        self.assertTrue(sql.startswith("-- shaperid:"))
        for token in (
            "::SECTION",
            "::DROPDOWN_MULTI",
            "::HINT",
            "::GAUGE_PERCENT",
            "::LINECHART",
            "::BARCHART_STACKED",
            "::DOWNLOAD_CSV",
            "::FOOTER_LINK",
            "getvariable('issue_category')",
        ):
            self.assertIn(token, sql)

    def test_shaper_static_page_builder_renders_source(self) -> None:
        spec = importlib.util.spec_from_file_location("shaper_build", SHAPER_BUILD)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        sql = SHAPER_SQL.read_text()
        html = module.render_page(sql)
        self.assertIn("Open source Shaper joins the bakeoff", html)
        self.assertIn("fusion-issue-health.dashboard.sql", html)
        self.assertIn("&quot;Open Issues&quot;", html)


if __name__ == "__main__":
    unittest.main()
