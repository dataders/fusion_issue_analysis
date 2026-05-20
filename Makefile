PORT ?= 8081
MCP_APP_PORT ?= 3001

.DEFAULT_GOAL := help
.PHONY: serve build ui-test data-freshness about dbt extract prefab ggsql mviz npm-dashboards mdv marimo observable evidence quarto dac shaper graphene-mcp mcp-app mcp-app-serve kill-server clean help

# ── Top-level ────────────────────────────────────────────────────────────────

## serve        Build all static exports and open the bakeoff at localhost:PORT
serve: build kill-server
	@echo "Serving bakeoff at http://localhost:$(PORT)"
	@cd dashboard && uv run python3 -m http.server $(PORT) &
	@sleep 1 && open http://localhost:$(PORT)

## build        Build every dashboard's static output (no serve)
build: data-freshness about prefab ggsql npm-dashboards mdv marimo quarto dac shaper

## ui-test      Run Playwright checks against generated dashboard exports
ui-test:
	npm run test:ui

## data-freshness Write source-data freshness metadata for the dashboard chrome
data-freshness:
	uv run python dashboard/write_data_freshness.py

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

## prefab       Export all Prefab dashboards to static HTML
prefab:
	uv run prefab export dashboard/prefab/app.py          -o dashboard/prefab/app.html
	uv run prefab export dashboard/prefab/app_reactive.py -o dashboard/prefab/app_reactive.html
	uv run prefab export dashboard/prefab/app_myspace.py  -o dashboard/prefab/app_myspace.html
	uv run prefab export dashboard/prefab/app_windows_2000.py -o dashboard/prefab/app_windows_2000.html

## ggsql        Build ggsql + Vega-Lite dashboard
ggsql:
	uv run dashboard/ggsql/build.py

## mviz         Generate data files and render mviz dashboard
mviz:
	npm run build:mviz

## npm-dashboards Build mviz, Observable, and Evidence in one npm command
npm-dashboards:
	npm run build:npm-dashboards

## mdv          Generate data files and render MDV dashboard
mdv:
	bash dashboard/mdv/build.sh

## marimo       Export Marimo notebook to static HTML
marimo:
	uv run marimo export html --no-include-code dashboard/marimo/app.py -o dashboard/marimo.html

## observable   Build Observable Framework dashboard (requires npm)
observable:
	npm --prefix dashboard/observable ci --silent
	npm run build:observable

## evidence     Build Evidence.dev dashboard (requires MOTHERDUCK_TOKEN + npm)
evidence:
	npm --prefix dashboard/evidence ci --legacy-peer-deps --silent
	npm run build:evidence

## quarto       Render Quarto dashboard to static HTML
quarto:
	cd dashboard/quarto && QUARTO_PYTHON=$$(uv run which python3) quarto render index.qmd

## dac          Build DAC dashboard to static HTML
dac:
	uv run python3 dashboard/dac/render.py
	! grep -q 'bruin query failed' dashboard/dac/build/index.html

## shaper       Build Shaper source-preview tab
shaper:
	uv run python3 dashboard/shaper/build.py

## graphene-mcp  Start the FastMCP server for the Graphene dashboard (builds snapshot on start)
graphene-mcp:
	uv run /Users/dataders/Developer/fusion_issue_analysis/.worktrees/codex-graphene-prod/dashboard/graphene/mcp_server.py

## mcp-app      Build local MCP Apps dashboard bundle
mcp-app:
	uv run python dashboard/mcp-app/build_data.py
	NPM_CONFIG_CACHE="$(CURDIR)/.cache/npm" npm --prefix dashboard/mcp-app ci --no-audit --no-fund --silent
	NPM_CONFIG_CACHE="$(CURDIR)/.cache/npm" npm --prefix dashboard/mcp-app run build
	NPM_CONFIG_CACHE="$(CURDIR)/.cache/npm" npm --prefix dashboard/mcp-app run smoke

## mcp-app-serve Build and serve local MCP Apps dashboard over streamable HTTP
mcp-app-serve: mcp-app
	NPM_CONFIG_CACHE="$(CURDIR)/.cache/npm" PORT=$(MCP_APP_PORT) npm --prefix dashboard/mcp-app start

# ── Utilities ─────────────────────────────────────────────────────────────────

## kill-server  Kill whatever is running on PORT (default: 8081)
kill-server:
	@lsof -ti:$(PORT) | xargs kill -9 2>/dev/null || true

## clean        Remove all generated dashboard files
clean:
	rm -f  dashboard/prefab/app.html dashboard/prefab/app_reactive.html dashboard/prefab/app_myspace.html dashboard/prefab/app_windows_2000.html
	rm -f  dashboard/data_freshness.json
	rm -f  dashboard/ggsql/index.html dashboard/mviz/index.html dashboard/mdv/index.html dashboard/marimo.html
	rm -rf dashboard/mviz/data dashboard/mdv/data dashboard/observable/dist dashboard/evidence/build
	rm -f  dashboard/quarto/index.html
	rm -rf dashboard/quarto/index_files dashboard/quarto/.quarto
	rm -rf dashboard/dac/build
	rm -rf dashboard/mcp-app/dist
	rm -f  dashboard/mcp-app/data/issue-health.json

## help         Show this help
help:
	@echo "Usage: make <target> [PORT=8081]"
	@echo ""
	@grep -E '^## ' Makefile | sed 's/## /  /'
	@echo ""
	@echo "Notes:"
	@echo "  Set MOTHERDUCK_TOKEN to build against MotherDuck instead of local DuckDB"
	@echo "  npm-dashboards installs nested Node dependencies before building"
	@echo "  dac requires the dac and bruin CLIs"
	@echo "  mcp-app is local-only: run make mcp-app-serve and connect an MCP Apps-capable host"
