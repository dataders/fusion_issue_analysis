# ggsql spike

Tracking issue: [#49](https://github.com/dbt-labs/fusion_issue_analysis/issues/49)

Evaluates [ggsql](https://ggsql.org/) — an experimental SQL extension from
Posit that adds `VISUALISE … DRAW …` clauses and emits Vega-Lite — as a third
authoring path alongside Prefab and mviz.

## Run

```bash
uv run dashboard/ggsql_spike/build.py
open dashboard/ggsql_spike/index.html
```

Uses the local DuckDB file built by `dbtf build`. Set `FUSION_DB` to point at
another path. The script has a PEP 723 header, so `uv run` bootstraps its own
deps; no project install is needed.

## What's in here

- `build.py` — connects to DuckDB, runs five ggsql queries against
  `fct_issues` / `issue_summary` / `milestone_burndown` / etc., and stitches
  per-chart Vega-Lite embeds into a single static HTML page.
- `index.html` — generated artifact. Pure HTML + vega-embed, safe to drop into
  the PR preview deploy alongside the Prefab `app.html`.

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
- Our dbt models reference parquet sources with relative paths, so
  `build.py` chdirs to `transform/` before opening the connection.
