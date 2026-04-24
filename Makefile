PORT ?= 8081

.DEFAULT_GOAL := help
.PHONY: serve build about dbt extract prefab ggsql mviz mdv marimo observable evidence quarto kill-server clean help

# ── Top-level ────────────────────────────────────────────────────────────────

## serve        Build all static exports and open the bakeoff at localhost:PORT
serve: build kill-server
	@echo "Serving bakeoff at http://localhost:$(PORT)"
	@cd dashboard && uv run python3 -m http.server $(PORT) &
	@sleep 1 && open http://localhost:$(PORT)

## build        Build every dashboard's static output (no serve)
build: about prefab ggsql mviz mdv marimo observable evidence quarto

## about        Render dashboard/about.html from dashboard/about.md
about:
	uv run python3 dashboard/render_about.py

## dbt          Run dbt build against local DuckDB (dev target)
dbt:
	cd transform && dbtf build --profiles-dir . --target dev --static-analysis off

## extract      Pull latest GitHub issues into local DuckDB
extract:
	cd extract && uv run python3 run.py

# ── Per-framework ─────────────────────────────────────────────────────────────

## prefab       Export both Prefab dashboards to static HTML
prefab:
	uv run prefab export dashboard/prefab/app.py          -o dashboard/prefab/app.html
	uv run prefab export dashboard/prefab/app_myspace.py  -o dashboard/prefab/app_myspace.html

## ggsql        Build ggsql + Vega-Lite dashboard
ggsql:
	uv run python3 dashboard/ggsql/build.py

## mviz         Generate data files and render mviz dashboard
mviz:
	uv run python3 dashboard/mviz/generate_data.py
	npx --yes mviz dashboard/mviz/dashboard.md -o dashboard/mviz/index.html

## mdv          Generate data files and render MDV dashboard
mdv:
	bash dashboard/mdv/build.sh

## marimo       Export Marimo notebook to static HTML
marimo:
	uv run marimo export html dashboard/marimo/app.py -o dashboard/marimo.html

## observable   Build Observable Framework dashboard (requires npm)
observable:
	cd dashboard/observable && npm run build

## evidence     Build Evidence.dev dashboard (requires MOTHERDUCK_TOKEN + npm)
evidence:
	uv run python3 dashboard/evidence/generate_sources.py
	cd dashboard/evidence && npm run build

## quarto       Render Quarto dashboard to static HTML
quarto:
	cd dashboard/quarto && QUARTO_PYTHON=$$(uv run which python3) quarto render index.qmd

# ── Utilities ─────────────────────────────────────────────────────────────────

## kill-server  Kill whatever is running on PORT (default: 8081)
kill-server:
	@lsof -ti:$(PORT) | xargs kill -9 2>/dev/null || true

## clean        Remove all generated dashboard files
clean:
	rm -f  dashboard/prefab/app.html dashboard/prefab/app_myspace.html
	rm -f  dashboard/ggsql/index.html dashboard/mviz/index.html dashboard/mdv/index.html dashboard/marimo.html
	rm -rf dashboard/mviz/data dashboard/mdv/data dashboard/observable/dist dashboard/evidence/build
	rm -f  dashboard/quarto/index.html
	rm -rf dashboard/quarto/index_files dashboard/quarto/.quarto

## help         Show this help
help:
	@echo "Usage: make <target> [PORT=8081]"
	@echo ""
	@grep -E '^## ' Makefile | sed 's/## /  /'
	@echo ""
	@echo "Notes:"
	@echo "  Set MOTHERDUCK_TOKEN to build against MotherDuck instead of local DuckDB"
	@echo "  observable and evidence require node_modules (run npm ci in each dir first)"
