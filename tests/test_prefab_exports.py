import importlib.util
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Loaded by path: extract/tests is also a `tests` package, so `from tests import ...` is ambiguous.
_spec = importlib.util.spec_from_file_location("dashboard_fixture", Path(__file__).with_name("dashboard_fixture.py"))
dashboard_fixture = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dashboard_fixture)
APPS = ["app", "app_reactive", "app_myspace", "app_windows_2000"]


class PrefabExportTests(unittest.TestCase):
    """Every Prefab variant must export against a fixture DB (no MotherDuck needed)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db = dashboard_fixture.build(Path(cls.tmp.name) / "fixture.duckdb")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def export(self, app: str) -> str:
        out = Path(self.tmp.name) / f"{app}.html"
        env = {**os.environ, "FUSION_DB": str(self.db)}
        env.pop("MOTHERDUCK_TOKEN", None)
        result = subprocess.run(
            ["uv", "run", "--frozen", "prefab", "export", f"dashboard/prefab/{app}.py", "-o", str(out)],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return out.read_text()

    def test_every_variant_exports_the_contract_sections(self) -> None:
        for app in APPS:
            with self.subTest(app=app):
                rendered = self.export(app)
                self.assertIn("Triage queue", rendered)


if __name__ == "__main__":
    unittest.main()
