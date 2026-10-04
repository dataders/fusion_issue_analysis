import unittest
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = REPO_ROOT / ".github" / "workflows"


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def run_steps(workflow: dict) -> list[str]:
    return [s["run"] for job in workflow["jobs"].values() for s in job["steps"] if "run" in s]


class WorkflowStructureTests(unittest.TestCase):
    def test_all_workflows_and_actions_parse(self) -> None:
        paths = [*WORKFLOWS.glob("*.yml"), *(REPO_ROOT / ".github" / "actions").glob("*/action.yml")]
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(path=path.name):
                self.assertIsInstance(load(path), dict)

    def test_every_prefab_variant_is_exported_by_preview_and_makefile(self) -> None:
        preview = "\n".join(run_steps(load(WORKFLOWS / "pr-preview.yml")))
        makefile = (REPO_ROOT / "Makefile").read_text()
        for app in sorted((REPO_ROOT / "dashboard" / "prefab").glob("app*.py")):
            with self.subTest(app=app.name):
                self.assertIn(f"dashboard/prefab/{app.name}", preview)
                self.assertIn(f"dashboard/prefab/{app.name}", makefile)

    def test_preview_and_deploy_use_the_shared_setup_action(self) -> None:
        for name in ("pr-preview.yml", "deploy-dashboard.yml"):
            with self.subTest(workflow=name):
                steps = [s for job in load(WORKFLOWS / name)["jobs"].values() for s in job["steps"]]
                self.assertIn("./.github/actions/dashboard-setup", [s.get("uses") for s in steps])

    def test_ci_lints_with_ruff(self) -> None:
        commands = "\n".join(run_steps(load(WORKFLOWS / "ci.yml")))
        self.assertIn("ruff check", commands)
        self.assertIn("ruff format --check", commands)


if __name__ == "__main__":
    unittest.main()
