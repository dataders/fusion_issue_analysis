# Fusion Issue Analysis — dashboard build
#
# Usage:
#   make all      # build every framework
#   make prefab   # build Prefab only
#   make serve    # build all then serve at http://localhost:8080
#
# Set MOTHERDUCK_TOKEN in your env to build against MotherDuck instead of
# the local DuckDB file at data/fusion_issues.duckdb.

.PHONY: all prefab mviz ggsql observable evidence marimo serve clean

all: prefab mviz ggsql observable evidence marimo quarto

# ── Prefab ────────────────────────────────────────────────────────────────────
prefab:
	@echo "==> Prefab"
	uv run prefab export dashboard/prefab/app.py -o dashboard/prefab/app.html
	uv run prefab export dashboard/prefab/app_myspace.py -o dashboard/prefab/app_myspace.html

# ── mviz ──────────────────────────────────────────────────────────────────────
mviz:
	@echo "==> mviz"
	cd dashboard/mviz && uv run python generate_data.py
	cd dashboard/mviz && npx mviz dashboard.md -o index.html

# ── ggsql + Vega-Lite ─────────────────────────────────────────────────────────
ggsql:
	@echo "==> ggsql"
	uv run dashboard/ggsql/build.py

# ── Observable Framework ──────────────────────────────────────────────────────
observable:
	@echo "==> Observable"
	cd dashboard/observable && npm ci --silent
	cd dashboard/observable && npm run build

# ── Evidence.dev ──────────────────────────────────────────────────────────────
evidence:
	@echo "==> Evidence"
	uv run python3 dashboard/evidence/generate_sources.py
	cd dashboard/evidence && npm ci --legacy-peer-deps --silent
	cd dashboard/evidence && ./node_modules/.bin/evidence sources
	cd dashboard/evidence && npm run build

# ── Marimo ────────────────────────────────────────────────────────────────────
marimo:
	@echo "==> Marimo"
	uv run marimo export html --no-include-code dashboard/marimo/app.py -o dashboard/marimo.html

# ── Quarto ────────────────────────────────────────────────────────────────────
quarto:
	@echo "==> Quarto"
	cd dashboard/quarto && QUARTO_PYTHON=$$(uv run which python3) quarto render index.qmd

# ── Serve ─────────────────────────────────────────────────────────────────────
serve: all
	@echo ""
	@echo "Serving at http://localhost:8080"
	@echo "Ctrl-C to stop"
	uv run python3 -m http.server 8080 --directory dashboard

# ── Clean generated artifacts ─────────────────────────────────────────────────
clean:
	rm -f dashboard/prefab/app.html dashboard/prefab/app_myspace.html
	rm -f dashboard/mviz/index.html
	rm -f dashboard/ggsql/index.html
	rm -f dashboard/marimo.html
	rm -rf dashboard/observable/dist
	rm -rf dashboard/evidence/build
	rm -f dashboard/quarto/index.html
	rm -rf dashboard/quarto/index_files dashboard/quarto/.quarto
