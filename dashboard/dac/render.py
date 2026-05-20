import json
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
DASHBOARD_NAME = "Fusion Issue Analysis"
ERROR_MARKERS = (
    "bruin query failed",
    "parsing bruin query output",
    "Installing uv ",
)


def render_dashboard_sources(destination: Path) -> None:
    shutil.copytree(SOURCE_DASHBOARDS, destination)


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
    subprocess.run(
        command,
        check=True,
        env=env,
        cwd=ROOT / "transform",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )


def extract_static_payload(content: str) -> dict:
    marker = "window.__DAC_STATIC__="
    start = content.find(marker)
    if start == -1:
        raise SystemExit("DAC static build is missing window.__DAC_STATIC__")

    start += len(marker)
    end = content.find(";</script>", start)
    if end == -1:
        raise SystemExit("DAC static build payload is not terminated")

    return json.loads(content[start:end])


def validate_static_output(path: Path) -> None:
    content = path.read_text()
    matches = [marker for marker in ERROR_MARKERS if marker in content]
    if matches:
        raise SystemExit(f"DAC static build contains query errors: {', '.join(matches)}")

    payload = extract_static_payload(content)
    widget_data = payload.get("widgetData") or {}
    if not widget_data:
        raise SystemExit("DAC static build does not contain widget data")

    invalid = []
    for widget_id, result in widget_data.items():
        if result.get("error"):
            invalid.append(f"{widget_id}: {result['error']}")
        elif not result.get("columns"):
            invalid.append(f"{widget_id}: missing columns")
        elif result.get("rows") is None:
            invalid.append(f"{widget_id}: missing rows")

    if invalid:
        raise SystemExit("DAC static build contains invalid widget data: " + "; ".join(invalid[:5]))


def resolve_output_path(raw_output: str | Path) -> Path:
    output = Path(raw_output)
    if output.is_absolute():
        return output
    return ROOT / output


def main() -> None:
    output = resolve_output_path(os.environ.get("DAC_OUTPUT", DAC_DIR / "build"))
    env = os.environ.copy()
    env.setdefault("FUSION_DB", str(ROOT / "data" / "fusion_issues.duckdb"))
    env_name = env.get("DAC_ENVIRONMENT")

    with tempfile.TemporaryDirectory(prefix="fusion-dac-") as tmp:
        tmp_path = Path(tmp)
        dashboards = tmp_path / "dashboards"
        render_dashboard_sources(dashboards)
        config = tmp_path / "bruin.yml"
        config_text = CONFIG.read_text()
        if env_name:
            config_text = config_text.replace("default_environment: local", f"default_environment: {env_name}")
        config.write_text(config_text)

        if env_name:
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
        subprocess.run(command, check=True, env=env, cwd=ROOT / "transform")

    fix_asset_paths(output / "index.html")
    validate_static_output(output / "index.html")


if __name__ == "__main__":
    main()
