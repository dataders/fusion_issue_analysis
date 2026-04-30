import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = REPO_ROOT / "dashboard" / "index.html"
MAKEFILE = REPO_ROOT / "Makefile"
APP_PATH = REPO_ROOT / "dashboard" / "prefab" / "app_windows_2000.py"
PR_PREVIEW_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "pr-preview.yml"
LOCAL_DB = REPO_ROOT / "data" / "fusion_issues.duckdb"


class PrefabWindows2000Tests(unittest.TestCase):
    def test_bakeoff_tab_points_to_windows_2000_export(self) -> None:
        content = INDEX_HTML.read_text()
        self.assertIn("Prefab Windows 2000", content)
        self.assertIn('data-src="prefab/app_windows_2000.html"', content)

    def test_makefile_exports_windows_2000_prefab(self) -> None:
        content = MAKEFILE.read_text()
        self.assertIn("dashboard/prefab/app_windows_2000.py", content)
        self.assertIn("dashboard/prefab/app_windows_2000.html", content)

    def test_pr_preview_workflow_includes_windows_2000_prefab(self) -> None:
        content = PR_PREVIEW_WORKFLOW.read_text()
        self.assertIn("dashboard/prefab/app_windows_2000.py", content)
        self.assertIn("preview/prefab/app_windows_2000.html", content)
        self.assertIn("| Prefab Windows 2000 | `prefab/app_windows_2000.html` |", content)

    def test_windows_2000_prefab_exports_app_shell(self) -> None:
        if not os.environ.get("MOTHERDUCK_TOKEN") and not LOCAL_DB.exists():
            self.skipTest("needs MOTHERDUCK_TOKEN or local fusion_issues.duckdb")

        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "app_windows_2000.html"
            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "prefab",
                    "export",
                    str(APP_PATH),
                    "-o",
                    str(out_path),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
            rendered = out_path.read_text() if out_path.exists() else ""

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Fusion Issue Explorer", rendered)
        self.assertIn("Issue Queue", rendered)
        self.assertIn("Ready", rendered)


if __name__ == "__main__":
    unittest.main()
