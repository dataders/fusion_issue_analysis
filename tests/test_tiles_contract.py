"""Keep dashboard/tiles.yml, the dbt dashboard models, and every framework in sync.

Run: uv run pytest tests/test_tiles_contract.py
"""

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = yaml.safe_load((ROOT / "dashboard" / "tiles.yml").read_text())
MODELS_DIR = ROOT / "transform" / "models" / "dashboard"

# Hand-written source for each bakeoff framework (generated output excluded).
# Directories are scanned for SOURCE_SUFFIXES; list .html files explicitly.
FRAMEWORKS = {
    "prefab": ["dashboard/prefab/app.py"],
    "prefab-reactive": ["dashboard/prefab/app_reactive.py"],
    "prefab-myspace": ["dashboard/prefab/app_myspace.py"],
    "prefab-windows-2000": ["dashboard/prefab/app_windows_2000.py"],
    "ggsql": ["dashboard/ggsql"],
    "mviz": ["dashboard/mviz"],
    "mdv": ["dashboard/mdv"],
    "observable": ["dashboard/observable/src/index.md", "dashboard/observable/src/data"],
    "observable-live": ["dashboard/observable/src/live.md"],
    "evidence": ["dashboard/evidence/pages", "dashboard/evidence/sources"],
    "marimo": ["dashboard/marimo/app.py"],
    "quarto": ["dashboard/quarto/index.qmd"],
    "dac": ["dashboard/dac/dashboards"],
    "shaper": ["dashboard/shaper"],
    "dbt-charts": ["transform/charts"],
    "duckdb-wasm": ["dashboard/duckdb-wasm/index.html"],
    "mosaic": ["dashboard/mosaic/index.html"],
    "mcp-app": ["dashboard/mcp-app/build_data.py", "dashboard/mcp-app/src"],
}
SOURCE_SUFFIXES = {".py", ".sql", ".md", ".qmd", ".yml", ".yaml", ".js", ".ts", ".mdv", ".sh"}
NON_TILE_MODELS = {"metric_avg_time_to_close", "metric_open_issue_count"}
# Renderers that loop over tiles.yml instead of naming each model. They get
# every tile by construction, so they're checked for the loop instead.
MANIFEST_DRIVEN = {"prefab": "tiles.sections()"}


def tile_models() -> list[str]:
    models = [MANIFEST["meta"]["model"]]
    for section in MANIFEST["sections"]:
        models += [tile["model"] for tile in section["tiles"]]
    return models


def framework_source(paths: list[str]) -> str:
    text = []
    for rel in paths:
        path = ROOT / rel
        files = [path] if path.is_file() else sorted(
            p for p in path.rglob("*")
            if p.is_file() and p.suffix in SOURCE_SUFFIXES and "node_modules" not in p.parts
        )
        assert files, f"{rel} has no source files"
        text += [f.read_text() for f in files]
    return "\n".join(text)


def test_manifest_models_match_dbt_models():
    dbt_models = {p.stem for p in MODELS_DIR.glob("*.sql")} - NON_TILE_MODELS
    assert sorted(tile_models()) == sorted(dbt_models)


def test_manifest_has_no_duplicate_tiles():
    ids = [t["id"] for s in MANIFEST["sections"] for t in s["tiles"]]
    assert len(ids) == len(set(ids))


def test_exposure_covers_every_tile_model():
    exposures = yaml.safe_load((MODELS_DIR / "_exposures.yml").read_text())["exposures"]
    bakeoff = next(e for e in exposures if e["name"] == "issue_health_bakeoff")
    refs = [re.search(r"ref\('(\w+)'\)", r).group(1) for r in bakeoff["depends_on"]]
    assert sorted(refs) == sorted(tile_models())


def test_db_path_precedence(monkeypatch):
    import sys
    sys.path.insert(0, str(ROOT / "dashboard"))
    import tiles

    monkeypatch.setenv("FUSION_DB", "custom.duckdb")
    monkeypatch.setenv("MOTHERDUCK_TOKEN", "token")
    assert tiles.db_path() == "custom.duckdb"
    monkeypatch.delenv("FUSION_DB")
    assert tiles.db_path() == "md:fusion_issues"
    monkeypatch.delenv("MOTHERDUCK_TOKEN")
    assert tiles.db_path() == str(ROOT / "data" / "fusion_issues.duckdb")


def test_every_tile_model_is_documented():
    schema = yaml.safe_load((MODELS_DIR / "_schema.yml").read_text())
    documented = {m["name"] for m in schema["models"]}
    assert set(tile_models()) <= documented


@pytest.mark.parametrize("framework", sorted(FRAMEWORKS))
def test_framework_renders_every_tile(framework):
    source = framework_source(FRAMEWORKS[framework])
    if framework in MANIFEST_DRIVEN:
        assert MANIFEST_DRIVEN[framework] in source
        return
    missing = [m for m in tile_models() if not re.search(rf"\b{m}\b", source)]
    assert not missing, f"{framework} does not reference tile models: {missing}"


@pytest.mark.parametrize("framework", sorted(FRAMEWORKS))
def test_framework_reads_only_dashboard_models(framework):
    """Metric logic belongs in dbt; frameworks must not query marts or staging."""
    source = framework_source(FRAMEWORKS[framework])
    leaks = sorted(set(re.findall(r"\b(?:fct|stg|dim)_\w+", source)))
    assert not leaks, f"{framework} reads non-dashboard models: {leaks}"
