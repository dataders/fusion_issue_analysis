import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from fix_asset_paths import fix_asset_paths


ROOT = Path(__file__).resolve().parents[2]
DAC_DIR = ROOT / "dashboard" / "dac"
SOURCE_DASHBOARDS = DAC_DIR / "dashboards"
CONFIG = DAC_DIR / "bruin.yml"
PLACEHOLDER = "set file_search_path='transform';"
DASHBOARD_NAME = "Fusion Issue Analysis"
ERROR_MARKERS = (
    "bruin query failed",
    "parsing bruin query output",
    "Installing uv ",
)


def render_dashboard_sources(destination: Path, transform_dir: str) -> None:
    shutil.copytree(SOURCE_DASHBOARDS, destination)
    dashboard = destination / "fusion-issues.yml"
    content = dashboard.read_text()
    dashboard.write_text(content.replace(PLACEHOLDER, f"set file_search_path='{transform_dir}';"))


def warm_bruin_query_runtime(config: Path, env: dict[str, str], env_name: str) -> None:
    command = [
        "bruin",
        "query",
        "--config-file",
        str(config),
        "--environment",
        env_name,
        "--connection",
        "fusion",
        "--query",
        "select 1 as value",
        "--output",
        "json",
    ]
    subprocess.run(command, check=True, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)


def validate_static_output(path: Path) -> None:
    content = path.read_text()
    matches = [marker for marker in ERROR_MARKERS if marker in content]
    if matches:
        raise SystemExit(f"DAC static build contains query errors: {', '.join(matches)}")


def main() -> None:
    output = Path(os.environ.get("DAC_OUTPUT", DAC_DIR / "build"))
    transform_dir = os.environ.get("FUSION_TRANSFORM_DIR", str(ROOT / "transform"))
    env = os.environ.copy()
    env.setdefault("FUSION_DB", "../../data/fusion_issues.duckdb")
    env_name = env.get("DAC_ENVIRONMENT")

    with tempfile.TemporaryDirectory(prefix="fusion-dac-") as tmp:
        tmp_path = Path(tmp)
        dashboards = tmp_path / "dashboards"
        render_dashboard_sources(dashboards, transform_dir)
        config = CONFIG
        if env_name:
            config = tmp_path / "bruin.yml"
            config.write_text(CONFIG.read_text().replace("default_environment: local", f"default_environment: {env_name}"))
            warm_bruin_query_runtime(config, env, env_name)

        command = ["dac", "--config", str(config)]
        command.extend([
            "build",
            "--dir",
            str(tmp_path),
            "--dashboard",
            DASHBOARD_NAME,
            "--output",
            str(output),
        ])
        subprocess.run(command, check=True, env=env)

    fix_asset_paths(output / "index.html")
    validate_static_output(output / "index.html")


if __name__ == "__main__":
    main()
