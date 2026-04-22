[![Deploy Dashboard](https://github.com/dataders/fusion_issue_analysis/actions/workflows/deploy-dashboard.yml/badge.svg)](https://github.com/dataders/fusion_issue_analysis/actions/workflows/deploy-dashboard.yml)

# Fusion Issue Analytics

Static dashboard bakeoff for [dbt-labs/dbt-fusion](https://github.com/dbt-labs/dbt-fusion) issue analytics.

Start here:

- Live dashboard: [dashboard-bakeoff.anders.omg.lol](https://dashboard-bakeoff.anders.omg.lol/)
- About, context, findings, and decision guide: [dashboard-bakeoff.anders.omg.lol/#about](https://dashboard-bakeoff.anders.omg.lol/#about)
- Contributing: [CONTRIBUTING.md](./CONTRIBUTING.md)

## Local Development

Prerequisites:

- [uv](https://docs.astral.sh/uv/)
- [dbtf](https://docs.getdbt.com/docs/cloud/cloud-cli-installation)
- `GITHUB_TOKEN` for extract
- `MOTHERDUCK_TOKEN` for MotherDuck-backed builds

Install dependencies:

```bash
uv sync
```

Common commands:

```bash
make extract
make dbt
make build
make serve
```

What they do:

- `make extract`: pull GitHub issue data with dlt
- `make dbt`: build shared models in DuckDB
- `make build`: export all dashboard variants
- `make serve`: build and open local static wrapper

## Repo Shape

- `extract/`: GitHub extraction with dlt
- `transform/`: shared dbt models
- `dashboard/`: framework-specific dashboard implementations and static wrapper

See the live about page for the longer write-up.
