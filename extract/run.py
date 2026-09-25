"""
Extract dbt Fusion (v2) issues and milestones using dlt's GitHub source.

Fusion issues were transferred from dbt-labs/dbt-fusion to dbt-labs/dbt-core
and are tracked there with the `engine:v2` label. GitHub transfers keep an
issue's created_at, comments and timeline, so dbt-core is the only source we
need. The old `raw_github` MotherDuck dataset is left as a frozen archive;
this pipeline writes to `raw_github_core` so the two never interfere.

Usage:
    uv run python run.py              # Extract to local parquet (data/raw/fusion_issues_core/)
    uv run python run.py --motherduck # Extract directly to MotherDuck
    uv run python run.py --limit 10   # Quick smoke test

The local filesystem destination appends, so wipe data/raw/fusion_issues_core/
before a fresh local run to avoid duplicate rows.
"""

import argparse
import os

import dlt
from github import github_reactions

OWNER = "dbt-labs"
REPO = "dbt-core"
LABELS = ["engine:v2"]


def main():
    parser = argparse.ArgumentParser(description="Extract dbt Fusion (v2) GitHub issues")
    parser.add_argument(
        "--motherduck",
        action="store_true",
        help="Write directly to MotherDuck instead of local parquet",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Cap the number of issues fetched (for quick testing).",
    )
    args = parser.parse_args()

    # GitHub token
    access_token = os.environ.get("GITHUB_TOKEN") or os.environ.get(
        "SOURCES__GITHUB__ACCESS_TOKEN"
    )
    if not access_token:
        raise ValueError("Set GITHUB_TOKEN or SOURCES__GITHUB__ACCESS_TOKEN env var")

    if args.motherduck:
        if not os.environ.get("MOTHERDUCK_TOKEN"):
            raise ValueError("Set MOTHERDUCK_TOKEN env var for MotherDuck destination")
        pipeline = dlt.pipeline(
            pipeline_name="github_issues_core_md",
            destination=dlt.destinations.motherduck("md:fusion_issues"),
            dataset_name="raw_github_core",
        )
    else:
        raw_path = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
        os.makedirs(raw_path, exist_ok=True)
        pipeline = dlt.pipeline(
            pipeline_name="github_issues_core",
            destination=dlt.destinations.filesystem(raw_path),
            dataset_name="fusion_issues_core",
        )

    source = github_reactions(
        owner=OWNER,
        name=REPO,
        access_token=access_token,
        # 50 keeps combined cost (issue + comments + reactions + timelineItems)
        # under GitHub's GraphQL resource-limits ceiling.
        items_per_page=50 if args.limit is None else min(50, args.limit),
        max_items=args.limit,
        labels=LABELS,
    ).with_resources("issues", "milestones")

    # Drop stuck pending packages so retried merge jobs from prior failed runs
    # don't resurface (the root cause of the MergeDispositionException).
    if args.motherduck:
        pipeline.drop_pending_packages()

    loader_kwargs = {}
    if not args.motherduck:
        loader_kwargs["loader_file_format"] = "parquet"

    load_info = pipeline.run(source, **loader_kwargs)
    print(load_info)


if __name__ == "__main__":
    main()
