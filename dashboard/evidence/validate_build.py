"""Validate that Evidence's static build can be served from /evidence/build."""

import json
from pathlib import Path


BUILD_DIR = Path(__file__).resolve().parent / "build"


def normalize_manifest_paths(manifest: dict) -> bool:
    changed = False
    rendered_files = manifest.get("renderedFiles", {})

    for source, paths in rendered_files.items():
        normalized_paths = []
        for rel_path in paths:
            if rel_path.startswith("static/data/"):
                rel_path = "data/" + rel_path.removeprefix("static/data/")
                changed = True
            normalized_paths.append(rel_path)
        rendered_files[source] = normalized_paths

    return changed


def validate_build(build_dir: Path = BUILD_DIR) -> None:
    manifest_path = build_dir / "data" / "manifest.json"
    if not manifest_path.exists():
        raise SystemExit(f"Evidence build manifest missing: {manifest_path}")

    manifest = json.loads(manifest_path.read_text())
    if normalize_manifest_paths(manifest):
        manifest_path.write_text(json.dumps(manifest))

    missing: list[str] = []
    invalid: list[str] = []
    rendered_files = manifest.get("renderedFiles", {})

    for paths in rendered_files.values():
        for rel_path in paths:
            if rel_path.startswith("/") or rel_path.startswith("static/"):
                invalid.append(rel_path)
            if not (build_dir / rel_path).exists():
                missing.append(rel_path)

    if invalid or missing:
        details = []
        if invalid:
            details.append("invalid data URL paths: " + ", ".join(invalid[:5]))
        if missing:
            details.append("missing data files: " + ", ".join(missing[:5]))
        raise SystemExit("Evidence static build is not portable: " + "; ".join(details))


if __name__ == "__main__":
    validate_build()
