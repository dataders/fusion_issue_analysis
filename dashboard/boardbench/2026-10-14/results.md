# BoardBench results table

Captured 14 October 2026. [Interactive report with criterion evidence](results.html) · [Browse the rules](rules.md) · [Scorecard and capture notes](scorecard.md)

**Score = 60 starting points + scaled excellence bonus − defect deductions**, capped at 0–100. A failed delivery or whole-page gate sets the score to zero. Negative values mean a defect was found; they are changes to the score, not negative final scores. The raw `DEL-01` `+10` in YAML is a gate marker and is excluded from the formula.

For example, dbt charts is **60 + 14.5 − 12 = 62.5**; the captured Mosaic page is **60 + 9.7 − 64 = 5.7**. Values are rounded to one decimal for display.

| Rank | Dashboard | Type | Start | Excellence bonus | Defect deductions | Score / 100 | Largest deductions |
|---:|---|---|---:|---:|---:|---:|---|
| 1 | [dbt charts](https://dashboard-bakeoff.anders.omg.lol/dbt-charts/fusion-issue-health.html) ([details](results.html#dbt-charts)) | Snapshot | 60 | +14.5 | −12.0 | **62.5** | FRM-08 (−8), DEL-02 (−4) |
| 2 | [DAC](https://dashboard-bakeoff.anders.omg.lol/dac/build/) ([details](results.html#dac)) | Snapshot | 60 | +9.7 | −13.0 | **56.7** | LAY-04 (−5), DEL-02 (−4) |
| 3 | [Quarto](https://dashboard-bakeoff.anders.omg.lol/quarto/index.html) ([details](results.html#quarto)) | Snapshot | 60 | +21.8 | −27.0 | **54.8** | BRF-01 (−15), FRM-08 (−8) |
| 4 | [Prefab](https://dashboard-bakeoff.anders.omg.lol/prefab/app.html) ([details](results.html#prefab)) | Snapshot | 60 | +9.7 | −15.0 | **54.7** | FRM-08 (−8), DEL-02 (−4) |
| 5 | [Chart.js](https://dashboard-bakeoff.anders.omg.lol/chartjs/index.html) ([details](results.html#chartjs)) | Snapshot | 60 | +9.7 | −16.0 | **53.7** | FRM-08 (−8), DEL-02 (−4) |
| 6 | [Observable](https://dashboard-bakeoff.anders.omg.lol/observable/dist/) ([details](results.html#observable)) | Snapshot | 60 | +9.7 | −16.0 | **53.7** | FRM-08 (−8), DEL-02 (−4) |
| 7 | [TanStack Charts](https://dashboard-bakeoff.anders.omg.lol/tanstack/dist/) ([details](results.html#tanstack)) | Snapshot | 60 | +9.7 | −17.0 | **52.7** | FRM-08 (−8), LAY-01 (−5) |
| 8 | [Prefab Reactive](https://dashboard-bakeoff.anders.omg.lol/prefab/app_reactive.html) ([details](results.html#prefab-reactive)) | Alternate | 60 | +9.7 | −19.0 | **50.7** | FRM-08 (−8), DEL-02 (−4) |
| 9 | [Prefab Windows 2000](https://dashboard-bakeoff.anders.omg.lol/prefab/app_windows_2000.html) ([details](results.html#prefab-windows-2000)) | Alternate | 60 | +9.7 | −19.0 | **50.7** | FRM-08 (−8), DEL-02 (−4) |
| 10 | [Semiotic](https://dashboard-bakeoff.anders.omg.lol/semiotic/index.html) ([details](results.html#semiotic)) | Live | 60 | +9.7 | −21.0 | **48.7** | FRM-08 (−8), LAY-01 (−5) |
| 11 | [Graphene](https://dashboard-bakeoff.anders.omg.lol/graphene/index.html) ([details](results.html#graphene)) | Snapshot | 60 | +6.1 | −19.0 | **47.1** | FRM-08 (−8), DEL-02 (−4) |
| 12 | [Evidence.dev](https://dashboard-bakeoff.anders.omg.lol/evidence/build/) ([details](results.html#evidence)) | Snapshot | 60 | +9.7 | −27.0 | **42.7** | BRF-01 (−15), FRM-08 (−8) |
| 13 | [mviz](https://dashboard-bakeoff.anders.omg.lol/mviz/index.html) ([details](results.html#mviz)) | Snapshot | 60 | +9.7 | −28.0 | **41.7** | FRM-08 (−8), LAY-04 (−5) |
| 14 | [ggsql + Vega-Lite](https://dashboard-bakeoff.anders.omg.lol/ggsql/index.html) ([details](results.html#ggsql)) | Snapshot | 60 | +9.7 | −31.0 | **38.7** | BRF-01 (−15), FRM-08 (−8) |
| 15 | [Marimo](https://dashboard-bakeoff.anders.omg.lol/marimo.html) ([details](results.html#marimo)) | Snapshot | 60 | +9.7 | −31.0 | **38.7** | LBL-09 (−10), FRM-08 (−8) |
| 16 | [Glyf](https://dashboard-bakeoff.anders.omg.lol/glyf/build/site/dashboards/fusion_issue_health.html) ([details](results.html#glyf)) | Snapshot | 60 | +9.7 | −33.0 | **36.7** | FRM-08 (−8), LEG-02 (−8) |
| 17 | [MDV](https://dashboard-bakeoff.anders.omg.lol/mdv/index.html) ([details](results.html#mdv)) | Snapshot | 60 | +9.7 | −34.0 | **35.7** | FRM-08 (−8), LEG-02 (−8) |
| 18 | [Observable live](https://dashboard-bakeoff.anders.omg.lol/observable/dist/live.html) ([details](results.html#observable-live)) | Live | 60 | +9.7 | −35.0 | **34.7** | BRF-01 (−15), FRM-08 (−8) |
| 19 | [DuckDB WASM MetricFlow](https://dashboard-bakeoff.anders.omg.lol/duckdb-wasm/metricflow/index.html) ([details](results.html#duckdb-wasm-metricflow)) | Other brief | 60 | +6.1 | −33.0 | **33.1** | HON-03 (−12), FRM-08 (−8) |
| 20 | [DuckDB WASM](https://dashboard-bakeoff.anders.omg.lol/duckdb-wasm/index.html) ([details](results.html#duckdb-wasm)) | Live | 60 | +9.7 | −40.0 | **29.7** | BRF-01 (−15), FRM-08 (−8) |
| 21 | [Prefab MySpace](https://dashboard-bakeoff.anders.omg.lol/prefab/app_myspace.html) ([details](results.html#prefab-myspace)) | Alternate | 60 | +9.7 | −40.0 | **29.7** | BRF-01 (−15), FRM-08 (−8) |
| 22 | [Shaper](https://dashboard-bakeoff.anders.omg.lol/shaper/index.html) ([details](results.html#shaper)) | Preview | 60 | +6.9 | −54.0 | **12.9** | BRF-01 (−15), LBL-03 (−6) |
| 23 | [Mosaic](https://dashboard-bakeoff.anders.omg.lol/mosaic/index.html) ([details](results.html#mosaic)) | Live | 60 | +9.7 | −64.0 | **5.7** | BRF-01 (−15), WRK-02 (−15) |

Each score comes from one OpenAI judge sample plus program checks. Scores a few points apart should be treated as close. Shaper is a source/run preview, and MetricFlow uses a different brief; neither is directly comparable with the rendered issue-health views. Numerical correctness was not checked against reference values. The [raw cards](cards/) retain every BoardBench verdict and vote.
