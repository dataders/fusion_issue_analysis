"""Record deployed dashboard framework versions and compare them with upstream releases."""

from __future__ import annotations

import json
import re
import subprocess
import tomllib
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dashboard" / "framework_versions.json"


def package_lock(path: str, name: str) -> str:
    lock = json.loads((ROOT / path).read_text())
    return lock["packages"][f"node_modules/{name}"]["version"]


def source_version(path: str, pattern: str) -> str:
    match = re.search(pattern, (ROOT / path).read_text())
    if not match:
        raise ValueError(f"Version not found in {path}: {pattern}")
    return match.group(1)


def command_version(command: list[str]) -> str | None:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=5, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    match = re.search(r"\d+\.\d+(?:\.\d+)?", result.stdout + result.stderr)
    return match.group() if match else None


def upstream(kind: str, name: str) -> tuple[str | None, str]:
    if kind == "pypi":
        url = f"https://pypi.org/pypi/{name}/json"
    elif kind == "npm":
        url = f"https://registry.npmjs.org/{quote(name, safe='')}/latest"
    elif kind == "github-commit":
        url = f"https://api.github.com/repos/{name}/commits/HEAD"
    else:
        url = f"https://api.github.com/repos/{name}/releases/latest"
    try:
        request = Request(url, headers={"User-Agent": "fusion-issue-analysis/version-check"})
        with urlopen(request, timeout=8) as response:
            data = json.load(response)
        version = {
            "pypi": lambda: data["info"]["version"],
            "npm": lambda: data["version"],
            "github-commit": lambda: data["sha"],
            "github-release": lambda: data["tag_name"].lstrip("v"),
        }[kind]()
        return version, url
    except (OSError, ValueError, KeyError):
        return None, url


def main() -> None:
    python = {
        package["name"]: package["version"] for package in tomllib.loads((ROOT / "uv.lock").read_text())["package"]
    }

    def npm(lock: str, name: str) -> str:
        return package_lock(lock, name)

    entries = {
        "dbt-charts": (python["dbt-charts"], "pypi", "dbt-charts"),
        "graphene": (
            source_version("dashboard/graphene/source/package.json", r'"@graphenedata/cli": "\^?([^\"]+)"'),
            "npm",
            "@graphenedata/cli",
        ),
        "prefab": (python["prefab-ui"], "pypi", "prefab-ui"),
        "evidence": (
            npm("dashboard/evidence/package-lock.json", "@evidence-dev/evidence"),
            "npm",
            "@evidence-dev/evidence",
        ),
        "dac": (command_version(["dac", "--version"]), "github-release", "bruin-data/dac"),
        "ggsql": (source_version("dashboard/ggsql/build.py", r'"ggsql==([0-9.]+)"'), "pypi", "ggsql"),
        "glyf": (source_version("dashboard/glyf/build.py", r'"glyf-core==([0-9.]+)"'), "pypi", "glyf-core"),
        "chartjs": (source_version("dashboard/chartjs/template.html", r"chart\.js@([0-9.]+)"), "npm", "chart.js"),
        "mviz": (source_version("package.json", r"mviz@([0-9.]+)"), "npm", "mviz"),
        "mdv": (
            source_version("dashboard/mdv/build.sh", r"MDV_SHA:-([0-9a-f]{40})"),
            "github-commit",
            "drasimwagan/mdv",
        ),
        "tanstack": (npm("dashboard/tanstack/package-lock.json", "@tanstack/charts"), "npm", "@tanstack/charts"),
        "observable": (
            npm("dashboard/observable/package-lock.json", "@observablehq/framework"),
            "npm",
            "@observablehq/framework",
        ),
        "marimo": (python["marimo"], "pypi", "marimo"),
        "quarto": (command_version(["quarto", "--version"]), "github-release", "quarto-dev/quarto-cli"),
        "shaper": (command_version(["shaper", "--version"]), "github-release", "taleshape-com/shaper"),
        "duckdb-wasm": (
            source_version("dashboard/duckdb-wasm/index.html", r"wasm-client@([0-9A-Za-z.\-]+)"),
            "npm",
            "@motherduck/wasm-client",
        ),
        "mosaic": (source_version("dashboard/mosaic/index.html", r"vgplot@([0-9.]+)"), "npm", "@uwdata/vgplot"),
        "semiotic": (source_version("dashboard/semiotic/index.html", r"semiotic@([0-9.]+)"), "npm", "semiotic"),
    }
    entries["observable-live"] = entries["observable"]
    releases = sorted({(kind, name) for _, kind, name in entries.values()})
    with ThreadPoolExecutor(max_workers=8) as pool:
        latest = dict(zip(releases, pool.map(lambda release: upstream(*release), releases), strict=True))

    checked_at = datetime.now(UTC).isoformat()
    frameworks = {}
    for tab, (installed, kind, name) in entries.items():
        release, source = latest.get((kind, name), (None, None))
        status = (
            "untracked"
            if not installed
            else "unverified"
            if not release
            else "current"
            if installed == release
            else "outdated"
        )
        if tab == "graphene":
            # Graphene's HTML is a committed snapshot, not rebuilt during deploy.
            status = "snapshot"
        frameworks[tab] = {"installed": installed, "latest": release, "status": status, "source": source}
    OUT.write_text(json.dumps({"checked_at": checked_at, "frameworks": frameworks}, indent=2) + "\n")
    print(f"Wrote {OUT.relative_to(ROOT)}: {len(frameworks)} frameworks")


if __name__ == "__main__":
    main()
