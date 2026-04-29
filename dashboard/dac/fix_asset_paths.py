import sys
from pathlib import Path


def fix_asset_paths(path: Path) -> None:
    content = path.read_text()
    content = content.replace('src="/assets/', 'src="assets/')
    content = content.replace('href="/assets/', 'href="assets/')
    path.write_text(content)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: fix_asset_paths.py <index.html>")
    fix_asset_paths(Path(sys.argv[1]))


if __name__ == "__main__":
    main()
