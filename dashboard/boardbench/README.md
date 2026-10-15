# BoardBench reports

`uv run python dashboard/boardbench/build.py` regenerates the browsable results,
rule catalog, and stable `boardbench/index.html` landing page from the reviewed
YAML cards in each dated directory. `make boardbench`, the Pages deployment, and
the PR preview use that command. Pages publishes `dashboard/`; the PR workflow
copies `dashboard/boardbench/` into its downloadable `preview/` artifact.

The scored cards are snapshots. A dashboard build **does not rerun the OpenAI
judge**, and each report states its capture date. This keeps the frequent data
refresh and dashboard deployment fast and avoids putting the OpenAI key in a PR
workflow that checks out untrusted changes.

## Incremental judge refresh

For a future trusted refresh workflow, capture every view at a fixed viewport
and wait. Compute each view's fingerprint from its screenshot bytes, visible
page text, and console metadata, together with the rubric, brief, judge model,
and pinned evaluator version. Reuse a previous card only when that fingerprint
matches and its judge completed without errors. Judge changed views, then save
the cards and fingerprints as one reviewed snapshot. A capture failure should
be reported as a failure, never silently represented by an older card.

The OpenAI-enabled evaluator currently lives in the separate private Dataface
repository. This repository's GitHub Actions secrets do not include
`OPENAI_API_KEY`. Local GitHub access to Dataface is blocked by its SAML policy,
so cross-repository CI access remains unverified. Those dependencies must be
resolved before enabling an automated paid refresh job. Do not copy a personal
API key into source or logs.
