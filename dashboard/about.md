<p class="links">
  <a href="./?tab=prefab" target="_top">Dashboard</a> ·
  <a href="https://github.com/dataders/fusion_issue_analysis" target="_blank" rel="noreferrer">GitHub repo</a> ·
  <a href="https://github.com/dbt-labs/dbt-fusion" target="_blank" rel="noreferrer">Upstream issues</a>
</p>

# About this dashboard bakeoff

This repo compares multiple static or static-friendly dashboard frameworks on one real analytics problem: GitHub issue health for [dbt-labs/dbt-fusion](https://github.com/dbt-labs/dbt-fusion). Main question is simple: what belongs in dbt, and what belongs in dashboard layer?

## Background

I got interested in agentic analytics partly because static-site dashboard frameworks are fun, and partly because I used to spend a lot of time in Power BI. I am not a web developer. This project is me trying to build intuition for what these frameworks can and cannot do when the goal is a real dashboard, not just a demo chart.

I expected a couple of options. I was surprised by how many there are. Along the way I started to learn what the static dashboard stack actually looks like, where it is strong, where it gets awkward, and how to make it work cleanly with dbt.

## What this repo is testing

- Same analytics problem, implemented across multiple static or static-friendly dashboard frameworks.
- Eight dashboard tabs sit on top of the same dbt `models/dashboard/` layer, so comparison is closer to apples-to-apples.
- Shared data layer runs on DuckDB locally and MotherDuck in deployed builds.
- Each framework makes different choices about authoring, transport, layout, interactivity, and build shape.

## How data flows

1. **Extract:** dlt pulls issues, comments, labels, assignees, and reactions from GitHub GraphQL.
2. **Transform:** dbt Fusion builds shared issue-health models into DuckDB locally and MotherDuck in CI.
3. **Visualize:** each dashboard framework renders against the same transformed layer.
4. **Publish:** the static wrapper ships to GitHub Pages on a custom domain.

## Tools in the bakeoff

**Core bakeoff frameworks:** Prefab, Evidence.dev, Observable Framework, ggsql + Vega-Lite, mviz, Marimo.

**Side experiments:** Prefab MySpace and Quarto.

**Data stack:** dlt, dbt Fusion, DuckDB, MotherDuck, GitHub Actions, GitHub Pages.

**Direct links:** [Prefab](./?tab=prefab), [Prefab MySpace](./?tab=prefab-myspace), [ggsql](./?tab=ggsql), [mviz](./?tab=mviz), [Observable](./?tab=observable), [Evidence.dev](./?tab=evidence), [Marimo](./?tab=marimo), [Quarto](./?tab=quarto).

## Main challenge

Hard part is not charting. Hard part is keeping business logic out of the dashboard. Agents do this. Humans do this too. The dashboard layer always tempts you to tuck a little metric logic, filtering logic, or status logic into the page because it feels faster in the moment. But once that starts, the dashboard becomes the semantic layer by accident.

The discipline here is to keep metric definitions, joins, and business rules in dbt whenever possible, then let the dashboard focus on layout, interaction, and presentation. When that boundary holds, the bakeoff is easier to compare, easier to diff, and easier to swap between tools.

## What I started to learn about the static dashboard stack

Every framework here is really a set of picks across a few layers:

- query engine
- query authoring
- data transport
- chart grammar
- chart runtime
- layout and composition
- authoring DSL and build system

The interesting choices are usually in the first three. Once query engine and transport are fixed, a lot of the rest follows from that.

## Build-time bake vs render-time query

| Mode | What happens | Frameworks |
|---|---|---|
| Build-time bake | SQL runs in CI against MotherDuck and rows are baked into static artifacts. | Prefab, Prefab MySpace, mviz, ggsql, Observable, Marimo, Quarto |
| Render-time query | Browser reruns page SQL against shipped Parquet through DuckDB-WASM. | Evidence.dev |

## Decision guide

| If you need... | Pick |
|---|---|
| Agent-authored, spec-diffable, static | [mviz](./?tab=mviz) |
| Python-first, design-system feel, KPI + charts | [Prefab](./?tab=prefab) |
| SQL is the chart | [ggsql](./?tab=ggsql) |
| Investigation more than presentation | [Marimo](./?tab=marimo) |
| Analyst-authored BI site with filters and polish | [Evidence.dev](./?tab=evidence) |
| Rich interactivity + bespoke viz if you accept Node | [Observable Framework](./?tab=observable) |
| Narrative report or document feel | [Quarto](./?tab=quarto) |

## Open questions

- Where is the right boundary between dbt models and dashboard-specific shaping queries?
- When is build-time baking enough, and when is browser-side or runtime querying worth the extra complexity?
- Should Evidence push all the way to true browser-to-MotherDuck querying, or is baked static data the better constraint?
- What is the best authoring format for agents: JSON specs, SQL-first tools, Markdown + SQL, or Python?
- How interactive can a static dashboard get before it becomes an accidental app?
- What is the right preview target for this kind of project: GitHub Pages, Netlify-style previews, or something more data-tool-native?
