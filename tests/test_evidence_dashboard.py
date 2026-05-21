import importlib.util
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_JSON = REPO_ROOT / "package.json"
EVIDENCE_VALIDATE = REPO_ROOT / "dashboard" / "evidence" / "validate_build.py"


class EvidenceDashboardTests(unittest.TestCase):
    def test_evidence_build_validates_manifest_after_static_export(self) -> None:
        script = PACKAGE_JSON.read_text()

        self.assertIn("npm --prefix dashboard/evidence run sources", script)
        self.assertIn("npm --prefix dashboard/evidence run build", script)
        self.assertNotIn("EVIDENCE_DATA_URL_PREFIX=data", script)
        self.assertIn("uv run python dashboard/evidence/validate_build.py", script)

    def test_evidence_validation_rejects_manifest_paths_that_do_not_exist(self) -> None:
        spec = importlib.util.spec_from_file_location("validate_build", EVIDENCE_VALIDATE)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        with TemporaryDirectory() as tmpdir:
            build = Path(tmpdir)
            manifest = build / "data" / "manifest.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text('{"renderedFiles": {"fusion.summary": ["static/data/fusion/summary.parquet"]}}')

            with self.assertRaises(SystemExit):
                module.validate_build(build)

    def test_evidence_validation_rewrites_static_manifest_paths_to_deployed_data_paths(self) -> None:
        spec = importlib.util.spec_from_file_location("validate_build", EVIDENCE_VALIDATE)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        with TemporaryDirectory() as tmpdir:
            build = Path(tmpdir)
            data_file = build / "data" / "fusion" / "summary.parquet"
            data_file.parent.mkdir(parents=True)
            data_file.write_bytes(b"PAR1")
            manifest = build / "data" / "manifest.json"
            manifest.write_text('{"renderedFiles": {"fusion.summary": ["static/data/fusion/summary.parquet"]}}')

            module.validate_build(build)

            self.assertIn("data/fusion/summary.parquet", manifest.read_text())
            self.assertNotIn("static/data/fusion/summary.parquet", manifest.read_text())

    def test_evidence_validation_accepts_manifest_paths_inside_build_dir(self) -> None:
        spec = importlib.util.spec_from_file_location("validate_build", EVIDENCE_VALIDATE)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        with TemporaryDirectory() as tmpdir:
            build = Path(tmpdir)
            data_file = build / "data" / "fusion" / "summary.parquet"
            data_file.parent.mkdir(parents=True)
            data_file.write_bytes(b"PAR1")
            manifest = build / "data" / "manifest.json"
            manifest.write_text('{"renderedFiles": {"fusion.summary": ["data/fusion/summary.parquet"]}}')

            module.validate_build(build)


if __name__ == "__main__":
    unittest.main()
