import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_JSON = REPO_ROOT / "package.json"
MAKEFILE = REPO_ROOT / "Makefile"
PLAYWRIGHT_CONFIG = REPO_ROOT / "playwright.config.js"
PLAYWRIGHT_SPEC = REPO_ROOT / "tests" / "ui" / "dashboard.spec.js"
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"


class UiE2eWiringTests(unittest.TestCase):
    def test_package_exposes_playwright_ui_test_commands(self) -> None:
        package = json.loads(PACKAGE_JSON.read_text())

        self.assertEqual(package["scripts"]["test:ui"], "playwright test")
        self.assertEqual(package["scripts"]["test:ui:headed"], "playwright test --headed")
        self.assertIn("@playwright/test", package["devDependencies"])

    def test_makefile_has_local_ui_test_target(self) -> None:
        content = MAKEFILE.read_text()

        self.assertIn(".PHONY:", content)
        self.assertIn("ui-test", content)
        self.assertIn("npm run test:ui", content)

    def test_playwright_framework_files_are_present(self) -> None:
        self.assertTrue(PLAYWRIGHT_CONFIG.exists())
        self.assertTrue(PLAYWRIGHT_SPEC.exists())

        config = PLAYWRIGHT_CONFIG.read_text()
        self.assertIn("tests/ui", config)
        self.assertIn("uv run python3 -m http.server", config)
        self.assertIn("dashboard", config)

    def test_ci_installs_browsers_and_runs_ui_tests(self) -> None:
        content = CI_WORKFLOW.read_text()

        self.assertIn("Install Playwright browsers", content)
        self.assertIn("npx playwright install --with-deps chromium", content)
        self.assertIn("Cache MDV build", content)
        self.assertIn("Smoke-test MDV", content)
        self.assertIn("bash dashboard/mdv/build.sh", content)
        self.assertIn("Run Playwright UI tests", content)
        self.assertIn("npm run test:ui", content)


if __name__ == "__main__":
    unittest.main()
