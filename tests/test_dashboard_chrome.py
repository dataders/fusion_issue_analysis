import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = REPO_ROOT / "dashboard" / "index.html"


class DashboardChromeTests(unittest.TestCase):
    def test_chrome_shows_source_data_refresh_metadata(self) -> None:
        content = INDEX_HTML.read_text()

        self.assertIn('id="data-refreshed"', content)
        self.assertIn("Data refreshed:", content)
        self.assertIn("data_freshness.json", content)
        self.assertNotIn("document.lastModified", content)

    def test_chrome_links_to_source_repo_with_github_favicon(self) -> None:
        content = INDEX_HTML.read_text()

        self.assertIn('href="https://github.com/dataders/fusion_issue_analysis"', content)
        self.assertIn('aria-label="Open source repository"', content)
        self.assertIn('src="https://github.githubassets.com/favicons/favicon.svg"', content)

    def test_build_writes_data_freshness_metadata(self) -> None:
        makefile = (REPO_ROOT / "Makefile").read_text()
        deploy = (REPO_ROOT / ".github" / "workflows" / "deploy-dashboard.yml").read_text()
        preview = (REPO_ROOT / ".github" / "workflows" / "pr-preview.yml").read_text()
        ci = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text()
        gitignore = (REPO_ROOT / ".gitignore").read_text()

        self.assertIn("data-freshness", makefile)
        self.assertIn("dashboard/write_data_freshness.py", makefile)
        self.assertIn("raw_github._dlt_loads", (REPO_ROOT / "dashboard" / "write_data_freshness.py").read_text())
        for content in (deploy, preview, ci):
            self.assertIn("Write data freshness metadata", content)
            self.assertIn("dashboard/write_data_freshness.py", content)
        self.assertIn("dashboard/data_freshness.json", gitignore)


if __name__ == "__main__":
    unittest.main()
