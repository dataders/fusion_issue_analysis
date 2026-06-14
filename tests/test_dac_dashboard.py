import importlib.util
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = REPO_ROOT / "dashboard" / "index.html"
MAKEFILE = REPO_ROOT / "Makefile"
PR_PREVIEW_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "pr-preview.yml"
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"
DEPLOY_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "deploy-dashboard.yml"
DAC_CONFIG = REPO_ROOT / "dashboard" / "dac" / "bruin.yml"
DAC_DASHBOARD = REPO_ROOT / "dashboard" / "dac" / "dashboards" / "fusion-issues.yml"
DAC_ASSET_FIX = REPO_ROOT / "dashboard" / "dac" / "fix_asset_paths.py"
DAC_RENDER = REPO_ROOT / "dashboard" / "dac" / "render.py"


class DacDashboardTests(unittest.TestCase):
    def test_bakeoff_tab_points_to_dac_static_build(self) -> None:
        content = INDEX_HTML.read_text()
        self.assertIn("DAC", content)
        self.assertIn('data-src="dac/build/"', content)

    def test_makefile_builds_and_cleans_dac(self) -> None:
        content = MAKEFILE.read_text()
        self.assertIn("build: data-freshness about prefab ggsql npm-dashboards mdv marimo quarto dac shaper", content)
        self.assertIn("uv run python dashboard/dac/render.py", content)
        self.assertIn("dashboard/dac/build", content)

    def test_ci_and_preview_workflows_build_dac(self) -> None:
        preview = PR_PREVIEW_WORKFLOW.read_text()
        ci = CI_WORKFLOW.read_text()
        deploy = DEPLOY_WORKFLOW.read_text()

        for content in (preview, ci, deploy):
            self.assertIn("Install DAC", content)
            self.assertIn("DAC_ENVIRONMENT: prod", content)
            self.assertIn("uv run python dashboard/dac/render.py", content)

        self.assertIn("preview/dac", preview)
        self.assertIn("DAC | \\`dac/index.html\\`", preview)
        self.assertIn("dashboard/dac/build", deploy)

    def test_dac_project_uses_fusion_issue_marts(self) -> None:
        config = DAC_CONFIG.read_text()
        dashboard = DAC_DASHBOARD.read_text()
        render = DAC_RENDER.read_text()

        self.assertIn("path: ${FUSION_DB}", config)
        self.assertIn("motherduck:", config)
        self.assertIn("token: ${MOTHERDUCK_TOKEN}", config)
        self.assertIn("database: fusion_issues", config)
        self.assertIn('env.setdefault("FUSION_DB", str(ROOT / "data" / "fusion_issues.duckdb"))', render)
        self.assertIn("name: Fusion Issue Analysis", dashboard)
        self.assertIn("connection: fusion", dashboard)
        self.assertIn("from summary_kpis", dashboard)
        self.assertIn("cumulative_flow", dashboard)
        self.assertIn("open_issues", dashboard)
        self.assertNotIn("set file_search_path", dashboard)
        self.assertIn("default_environment: {env_name}", render)
        self.assertIn("warm_bruin_query_runtime(config, env, env_name)", render)

    def test_dac_asset_rewrite_makes_nested_static_build_portable(self) -> None:
        spec = importlib.util.spec_from_file_location("fix_asset_paths", DAC_ASSET_FIX)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        sys.path.insert(0, str(DAC_RENDER.parent))
        spec.loader.exec_module(module)

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "index.html"
            path.write_text('<script src="/assets/app.js"></script><link href="/assets/app.css">')
            module.fix_asset_paths(path)

            rewritten = path.read_text()
            self.assertIn('src="assets/app.js"', rewritten)
            self.assertIn('href="assets/app.css"', rewritten)
            self.assertNotIn('"/assets/', rewritten)

    def test_dac_static_output_validation_rejects_baked_query_errors(self) -> None:
        spec = importlib.util.spec_from_file_location("render", DAC_RENDER)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "index.html"
            path.write_text("parsing bruin query output: Installing uv v0.10.8")

            with self.assertRaises(SystemExit):
                module.validate_static_output(path)

    def test_dac_static_output_validation_rejects_empty_widget_results(self) -> None:
        spec = importlib.util.spec_from_file_location("render", DAC_RENDER)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "index.html"
            path.write_text('<script>window.__DAC_STATIC__={"widgetData":{"Open Issues":{"columns":null,"rows":[]}}};</script>')

            with self.assertRaises(SystemExit):
                module.validate_static_output(path)

    def test_dac_static_output_validation_rejects_widget_errors(self) -> None:
        spec = importlib.util.spec_from_file_location("render", DAC_RENDER)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "index.html"
            payload = {
                "widgetData": {
                    "r0-w0": {
                        "columns": None,
                        "rows": None,
                        "query": "select 1",
                        "error": "bruin query failed",
                    }
                }
            }
            path.write_text(f"<script>window.__DAC_STATIC__={json.dumps(payload)};</script>")

            with self.assertRaises(SystemExit):
                module.validate_static_output(path)

    def test_dac_render_resolves_relative_outputs_from_repo_root(self) -> None:
        spec = importlib.util.spec_from_file_location("render", DAC_RENDER)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        self.assertEqual(module.resolve_output_path("dashboard/dac/build"), REPO_ROOT / "dashboard" / "dac" / "build")


if __name__ == "__main__":
    unittest.main()
