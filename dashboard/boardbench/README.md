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

The results page also shows a score status beside each view. Its 2026-10-14
cards have no recorded build fingerprint, so they start as **Freshness
unverified**. On the deployed site, a data-dependent view changes to **Needs
review · new data** when the latest source load is on a later day than the
capture. This is a conservative change signal, not a revised score or proof
that the visible page differs. Graphene's committed export and Shaper's source
preview are not rebuilt from that data load and remain unverified. A future
evaluation can record per-view input fingerprints to distinguish **Current**
from **Needs review** after code or generated-artifact changes.

## Incremental judge refresh

For a future trusted refresh workflow, start with the changes to each view's
inputs. Compare the built HTML, JavaScript, CSS, and data artifacts against the
last judged deployment, including shared code actually loaded by that view. A
source diff can identify likely candidates early, but the built artifacts are the
safer comparison: generated output and transitive dependencies may change even
when a view's own source file does not. Live views also need a data version or
snapshot digest; this repository deploys after extracts and on a daily schedule
even without code changes.

Skip views whose complete inputs are unchanged. For candidates, capture at a
fixed viewport and wait, then compare the screenshot, visible page text, and
console metadata locally. Reuse a previous card if the rendered evidence is
unchanged and its judge completed without errors. Call the judge only for
changed evidence, or when the rubric, brief, judge model, or evaluator version
changes. Save cards and fingerprints as one reviewed snapshot. A capture or
dependency-resolution failure should be reported as a failure, never silently
represented by an older card. The rubric still judges rendered output; code
diffs decide which views need another look, not their scores.

The OpenAI-enabled evaluator currently lives in the separate private Dataface
repository. This repository's GitHub Actions secrets do not include
`OPENAI_API_KEY`. Local GitHub access to Dataface is blocked by its SAML policy,
so cross-repository CI access remains unverified. Those dependencies must be
resolved before enabling an automated paid refresh job. Do not copy a personal
API key into source or logs.
