# ggsql dashboard

Tracking issue: [#49](https://github.com/dataders/fusion_issue_analysis/issues/49)

Evaluates [ggsql](https://ggsql.org/) — an experimental SQL extension from
Posit that adds `VISUALISE … DRAW …` clauses and emits Vega-Lite — as a third
authoring path alongside Prefab and mviz.

## Run

```bash
uv run dashboard/ggsql/build.py
open dashboard/ggsql/index.html
```

Uses the local DuckDB file built by `dbtf build`. Set `FUSION_DB` to point at
another path. The script has a PEP 723 header, so `uv run` bootstraps its own
deps; no project install is needed.

## What's in here

- `build.py` — renders the tile contract in `dashboard/tiles.yml`: section
  questions, tile titles/subtitles, the freshness banner and KPI formatting
  come from the manifest via `dashboard/tiles.py`; each tile's data comes from
  one `queries/NN_<tile_id>.sql` file (numbered in tiles.yml order).
- `queries/*.sql` — ggsql chart specs (`SELECT … VISUALISE … DRAW …`) over the
  `transform/models/dashboard/` models, plus plain SELECTs for the KPI row
  (`-- type: kpi`) and tables (`-- type: table`), which `build.py` renders
  as HTML with rows linked to `issue_url`.
- `index.html` — generated artifact. Pure HTML + vega-embed.

## Approach: build-time vs. in-browser

ggsql ships two execution paths:

| Path | Status | Notes |
|---|---|---|
| **Python (`pip install ggsql`)** | Used here | Rust/PyO3 bindings, DuckDB backend, renders to Altair/Vega-Lite. `vl-convert-python` handles the static save. |
| **WASM (`ggsql-wasm` crate)** | Not feasible without upstream work | The crate exists ([posit-dev/ggsql/ggsql-wasm](https://github.com/posit-dev/ggsql/tree/main/ggsql-wasm)) and the playground at <https://ggsql.org/wasm/> runs entirely in the browser via `wasm-bindgen`. But there is **no published `ggsql-wasm` npm package** — the demo depends on a local `file:../pkg`. Reproducing it requires `wasm-pack` + an LLVM with `wasm32-unknown-unknown` support to compile `sqlite-wasm-rs`, which Apple's stock clang lacks. |

So today's deployable path is build-time in Python, matching how Prefab and
mviz already produce static HTML. A fully client-side ggsql demo would mean
either (a) upstream publishing `@posit-dev/ggsql-wasm` to npm, or (b) us
vendoring a self-built `pkg/ggsql_wasm.js` + `ggsql_wasm_bg.wasm` (~10 MB).

The browser path is interesting because the WASM build registers data as
parquet bytes (`ctx.register_parquet(name, bytes)`) and runs on SQLite — so
our parquet sources under `data/raw/fusion_issues/` would load directly. If
the spike is greenlit, the follow-up is to vendor the pre-built pkg and swap
`build.py` for a tiny HTML page.

## Author ergonomics, very rough

- **Prefab** — Python DSL, reactive updates, filters for free. Wins for
  interactive dashboards.
- **mviz** — JSON spec files, deterministic, good for AI-agent generation.
  Wins when the chart list is stable and you want diff-able specs.
- **ggsql** — SQL + a handful of extension clauses. Wins when the shape of
  the chart is dictated by the query itself; authoring feels like writing
  `dbt` models. Least ceremony per chart, but you get one chart per query
  rather than a composed dashboard.

## Known quirks

- `ggsql.DuckDBReader` mangles absolute paths (`duckdb:///abs/path` loses a
  leading slash). Worked around by wrapping a `duckdb.Connection` with a
  custom reader that implements `execute_sql(sql) -> polars.DataFrame` +
  `register(name, df, …)`.
- ggsql 0.3 rejects polars' Utf8View strings in discrete scales, so the reader
  casts string columns to Categorical.
- Discrete axes are always sorted alphabetically. `-- order: y` makes
  `build.py` set the Vega-Lite domain to the query's row order (bars sorted
  by `*_total`).
- Stacks are also ordered alphabetically by fill value, so stacked series are
  prefixed with their palette order (`'1 feature'`, `'1 0-7d'`) and
  `RENAMING` restores the labels.
- Dodged bars on a temporal axis render as hairlines; `weekly_flow` keeps the
  week as a string so each week gets a band.
- No tooltips: ggsql's Vega-Lite output uses internal field names.
