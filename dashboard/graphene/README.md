# Graphene

`index.html` is a **static export** of a [Graphene](https://github.com/graphene-data/graphene) page. It is committed, not built in CI, and retains Graphene's standalone report renderer. The file embeds query results and remains a snapshot until explicitly refreshed.

After rebuilding the local dbt models, refresh those embedded results with:

```bash
uv run python dashboard/graphene/refresh.py
```

This re-executes the export's compiled SQL against `data/fusion_issues.duckdb`, checks result column names, and updates its data date. It preserves the renderer and removes the obsolete unassigned callout. Use `--source` for another local database; it needs the full models, not only the dashboard serving snapshot. Existing files under `data/` are not used or modified. Layout changes still require a new Graphene export; the CLI's export command supports synced Cloud reports only.

`source/` is the Graphene project the page was built from:

- `tables/issues.gsql` is a small semantic model over `fct_issues`, `fct_issue_labels`, `epic_progress` and `assignee_workload` in the MotherDuck `fusion_issues` database.
- `pages/index.md` is the dashboard.

Unlike the other tabs, this page does not follow `tiles.yml` tile-for-tile and is not covered by `tests/test_tiles_contract.py`; it reads `fct_*` models directly to show off Graphene's semantic layer.

To iterate on it locally (needs a MotherDuck read token in `source/.env` as `MOTHERDUCK_TOKEN`):

```bash
cd dashboard/graphene/source
npm install
npx graphene serve
```
