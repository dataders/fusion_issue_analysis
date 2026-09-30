# Graphene

`index.html` is a **static export** of a [Graphene](https://github.com/graphene-data/graphene) page. It is committed, not built in CI: Graphene pages can't be self-hosted or embedded live yet, and it was generated with Graphene's standalone report export. The file embeds the query results captured at export time, so it is a snapshot and doesn't refresh.

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
