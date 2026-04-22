# Contributing to `fusion_issue_analysis`

`fusion_issue_analysis` is an end-to-end analytics pipeline for dbt-labs/dbt-fusion GitHub issues: Extract (dlt) → Transform (dbt Fusion + DuckDB) → Visualize (Prefab).

1. [About this document](#about-this-document)
2. [Getting the code](#getting-the-code)
3. [Setting up an environment](#setting-up-an-environment)
4. [Running in development](#running-in-development)
5. [Adding or modifying a changelog entry](#adding-or-modifying-a-changelog-entry)
6. [Submitting a Pull Request](#submitting-a-pull-request)

## About this document

We encourage you to first read our higher-level document: ["Expectations for Open Source Contributors"](https://docs.getdbt.com/docs/contributing/oss-expectations).

### Notes

- **CLA:** Anyone contributing code must sign the [Contributor License Agreement](https://docs.getdbt.com/docs/contributor-license-agreements).
- **Branches:** All pull requests from community contributors should target the `main` branch (default).

## Getting the code

### External contributors

Fork the repository, clone locally, check out a new branch for your changes, and open a pull request against `dataders/fusion_issue_analysis`.

### Maintainers

Clone the repository directly, check out a new branch, and push to that branch.

## Setting up an environment

### Prerequisites

- [uv](https://docs.astral.sh/uv/) for Python dependency management
- [dbtf](https://docs.getdbt.com/docs/cloud/cloud-cli-installation) (dbt Cloud CLI with Fusion engine)
- A GitHub personal access token with `public_repo` and `read:org` scopes

### Install dependencies

```bash
uv sync
```

### Environment variables

```bash
export GITHUB_TOKEN=ghp_your_token_here       # required for extract
export MOTHERDUCK_TOKEN=your_md_token_here    # optional, for prod target
```

## Running in development

### Extract

```bash
cd extract && uv run python run.py
```

### Transform

```bash
cd transform && dbtf build --profiles-dir . --target dev
```

### Dashboard

```bash
uv run prefab serve dashboard/app.py --reload
```

Opens at [http://127.0.0.1:5175](http://127.0.0.1:5175).

## Adding or modifying a CHANGELOG Entry

We use [changie](https://changie.dev) to generate `CHANGELOG` entries. **Do not edit `CHANGELOG.md` directly.**

```shell
changie new
```

Commit the generated file with your PR.

## Submitting a Pull Request

Open a PR against `main`. A maintainer will review. Automated checks run via GitHub Actions — first-time contributors require maintainer approval before CI runs.

PRs that change a dashboard should include an export verification:

```bash
uv run prefab export dashboard/app.py -o /tmp/test.html
```
