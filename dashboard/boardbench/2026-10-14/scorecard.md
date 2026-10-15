# BoardBench scorecard: dbt v2 issue dashboard bakeoff

Captured 14 October 2026 from the [published bakeoff](https://dashboard-bakeoff.anders.omg.lol/). This covers all 19 framework tabs in the published picker, plus its three alternate Prefab themes and the separate DuckDB WASM MetricFlow view. The About page is not a dashboard. All 23 direct routes returned a page and were captured at a 1440px browser width after a five-second load wait.

## Read this scorecard

**[Read the results table](results.md)** for each dashboard's starting points, scaled excellence bonus, deductions, and final score. The [interactive version](results.html) adds sorting, filters, and readable criterion evidence. The YAML cards remain the raw BoardBench output.

**[Browse all 47 rules](rules.md)** by category, weight, and question; the [searchable rule browser](rules.html) also shows the dashboards each rule affected.

Scores use [BoardBench rubric 2.8.0](rubric.yml), sourced from the `dataface` repository at commit `dceb49f18e649711feb8bc67bcf02e09f8a56dc3`. BoardBench's program checks and its default OpenAI visual judge (`gpt-5.6-terra`) produced the [individual cards](cards/), with per-criterion verdicts and evidence. Each card used one judge sample on the saved screenshot and page text. The notes in the tables and cross-cutting findings are a local visual review of the same captures.

The same [issue-health brief](brief.md) was used for every view except MetricFlow, which is a different dashboard. **Score = 60 starting points + scaled excellence bonus − defect deductions**, capped at 0–100. A failed gate sets the score to zero. A negative `points_earned` in a YAML card means the judge found a defect and subtracted that many score points. The `DEL-01` row's raw `+10` is a delivery gate result, not a bonus added to the final score. For example, dbt charts is **60 + 14.5 − 12 = 62.5**. Scores within a few points are not a meaningful ranking. Cards report agreement as 1.0 because each criterion received one judge vote; that is not independent reviewer agreement. Numerical correctness was not checked against an external reference, so `COR-01` is not applicable.

## Published framework tabs

| Snapshot dashboard | Score / 100 | Most consequential observed issue | Evidence |
|---|---:|---|---|
| [dbt charts](https://dashboard-bakeoff.anders.omg.lol/dbt-charts/fusion-issue-health.html) | **62.5** | Full brief coverage and direct chart labels; one console resource error. | [Card](cards/dbt-charts.yml) |
| [Graphene](https://dashboard-bakeoff.anders.omg.lol/graphene/index.html) | **47.1** | No as-of date or customer-reported-open KPI; shows 485 open issues while current tabs show 511. | [Card](cards/graphene.yml) |
| [Prefab](https://dashboard-bakeoff.anders.omg.lol/prefab/app.html) | **54.7** | Complete content; several chart labels and table columns are clipped. | [Card](cards/prefab.yml) |
| [Evidence.dev](https://dashboard-bakeoff.anders.omg.lol/evidence/build/) | **42.7** | Narrow tables clip columns; detail competes with headline charts. | [Card](cards/evidence.yml) |
| [DAC](https://dashboard-bakeoff.anders.omg.lol/dac/build/) | **56.7** | Epic values such as `0.96` appear under a `% complete` heading; tables truncate detail. | [Card](cards/dac.yml) |
| [ggsql + Vega-Lite](https://dashboard-bakeoff.anders.omg.lol/ggsql/index.html) | **38.7** | Query/path scaffolding and long tables dominate the page. | [Card](cards/ggsql.yml) |
| [Glyf](https://dashboard-bakeoff.anders.omg.lol/glyf/build/site/dashboards/fusion_issue_health.html) | **36.7** | Date ticks overlap in several charts; raw field names remain visible. | [Card](cards/glyf.yml) |
| [Chart.js](https://dashboard-bakeoff.anders.omg.lol/chartjs/index.html) | **53.7** | Weekly response line is faint at normal size; final row leaves a large gap. | [Card](cards/chartjs.yml) |
| [mviz](https://dashboard-bakeoff.anders.omg.lol/mviz/index.html) | **41.7** | Long tables dominate the page and the weekly spike compresses routine comparisons. | [Card](cards/mviz.yml) |
| [MDV](https://dashboard-bakeoff.anders.omg.lol/mdv/index.html) | **35.7** | Very long tables, overlapping date ticks, and an unlabeled response axis. | [Card](cards/mdv.yml) |
| [TanStack Charts](https://dashboard-bakeoff.anders.omg.lol/tanstack/dist/) | **52.7** | Complete brief coverage; weekly outlier compresses routine bars and the last row is half empty. | [Card](cards/tanstack.yml) |
| [Observable](https://dashboard-bakeoff.anders.omg.lol/observable/dist/) | **53.7** | Complete coverage; weekly outlier compresses routine comparisons. | [Card](cards/observable.yml) |
| [Marimo](https://dashboard-bakeoff.anders.omg.lol/marimo.html) | **38.7** | Some table text is cut off and the final layout leaves unused space. | [Card](cards/marimo.yml) |
| [Quarto](https://dashboard-bakeoff.anders.omg.lol/quarto/index.html) | **54.8** | Useful prose finding, but narrow layout causes table text collision and cutoff. | [Card](cards/quarto.yml) |
| [Shaper](https://dashboard-bakeoff.anders.omg.lol/shaper/index.html) | **12.9 (preview)** | Published tab is a source/run preview rather than a rendered issue-health dashboard. | [Card](cards/shaper.yml) |

| Live dashboard | Score / 100 | Most consequential observed issue | Evidence |
|---|---:|---|---|
| [DuckDB WASM](https://dashboard-bakeoff.anders.omg.lol/duckdb-wasm/index.html) | **29.7** | All panels load, but the as-of date renders as `[object Ob…]`. | [Card](cards/duckdb-wasm.yml) |
| [Mosaic](https://dashboard-bakeoff.anders.omg.lol/mosaic/index.html) | **5.7** | Seven chart panels stay blank; console reports missing `fusion_issues.main` chart tables. | [Card](cards/mosaic.yml) |
| [Semiotic](https://dashboard-bakeoff.anders.omg.lol/semiotic/index.html) | **48.7** | All panels load, but the as-of date renders as `[object Ob…]`. | [Card](cards/semiotic.yml) |
| [Observable live](https://dashboard-bakeoff.anders.omg.lol/observable/dist/live.html) | **34.7** | All panels load with cache context, but the as-of date renders as `[object Ob…]`. | [Card](cards/observable-live.yml) |

Shaper's number describes the published preview page under the shared brief. It should not be used to rank Shaper's unrendered SQL dashboard against rendered frameworks.

## Other selectable views

| View | Score / 100 | Main observation | Evidence |
|---|---:|---|---|
| [Prefab Reactive](https://dashboard-bakeoff.anders.omg.lol/prefab/app_reactive.html) | 50.7 | Clear filter scope; clipped labels and issue titles. | [Card](cards/prefab-reactive.yml) |
| [Prefab MySpace](https://dashboard-bakeoff.anders.omg.lol/prefab/app_myspace.html) | 29.7 | All content present; heavy retro styling and long tables slow scanning. | [Card](cards/prefab-myspace.yml) |
| [Prefab Windows 2000](https://dashboard-bakeoff.anders.omg.lol/prefab/app_windows_2000.html) | 50.7 | All content present; heavy chrome and cropped chart labels. | [Card](cards/prefab-windows-2000.yml) |
| [DuckDB WASM MetricFlow](https://dashboard-bakeoff.anders.omg.lol/duckdb-wasm/metricflow/index.html) | 33.1 (other brief) | Metric definitions are explicit; raw metric names and clipped labels make this developer-facing view less readable. | [Card](cards/duckdb-wasm-metricflow.yml) |

MetricFlow was scored without the issue-health brief. Its score is not directly comparable with the other views.

## Cross-cutting findings and limits

- **Fix Mosaic's live chart queries first.** The captured page renders KPIs and tables, but seven chart panels are blank and the console reports missing catalog tables. The judge penalized those panels under `WRK-02`; it did not trip the whole-page `WRK-01` gate because other parts of the page contain data. The score describes the public capture; a fix is proposed in open [PR #124](https://github.com/dataders/fusion_issue_analysis/pull/124).
- **Fix live freshness headers together.** DuckDB WASM, Mosaic, Semiotic, and Observable live all display a JavaScript object fragment in place of the as-of date. Their freshness signal is unusable even where the charts render.
- **Reconcile Graphene's snapshot.** It shows 485 open issues against 511 on current published views and omits an as-of date, so readers cannot tell whether the difference is age, scope, or both.
- **Check DAC's percentage formatting.** Values under `% complete` are shown as fractions, which can change the reader's interpretation by a factor of 100.
- **Treat outlier-scale penalties as judgment-sensitive.** One large opened-issue week compresses typical weeks in several implementations; reviewers applied `FRM-08` only where routine comparisons became difficult to read. A change on this one criterion moves a card by eight points.

This evaluates the visible page after a single load, not filter interactions, accessibility behavior, framework authoring experience, or the underlying SQL's numerical truth. Most pages logged at least one console error; the BoardBench `DEL-02` penalty is included even when the screenshot otherwise looks complete. BoardBench's standard tiler can omit lower full-resolution sections of especially long pages; the local notes also inspected the full MDV, Prefab MySpace, and ggsql captures. The unpublished MCP app was outside the published picker and is outside this scorecard.
