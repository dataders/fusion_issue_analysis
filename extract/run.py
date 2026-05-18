"""
Extract issues, comments, and reactions from dbt-labs/dbt-fusion using dlt's GitHub source.

Usage:
    uv run python run.py              # Extract to local parquet (data/raw/)
    uv run python run.py --motherduck # Extract directly to MotherDuck
"""

import argparse
import os

import dlt
from github import github_reactions


def main():
    parser = argparse.ArgumentParser(description="Extract dbt-fusion GitHub issues")
    parser.add_argument(
        "--motherduck",
        action="store_true",
        help="Write directly to MotherDuck instead of local parquet",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Cap the number of issues/PRs fetched (for quick testing).",
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
            pipeline_name="github_issues_md",
            destination=dlt.destinations.motherduck("md:fusion_issues"),
            dataset_name="raw_github",
        )
    else:
        raw_path = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
        os.makedirs(raw_path, exist_ok=True)
        pipeline = dlt.pipeline(
            pipeline_name="github_issues",
            destination=dlt.destinations.filesystem(raw_path),
            dataset_name="fusion_issues",
        )

    # Extract all issues (not PRs) from dbt-fusion
    source = github_reactions(
        owner="dbt-labs",
        name="dbt-fusion",
        access_token=access_token,
        # 50 keeps combined cost (issue + comments + reactions + timelineItems)
        # under GitHub's GraphQL resource-limits ceiling.
        items_per_page=50 if args.limit is None else min(50, args.limit),
        max_items=args.limit,
    ).with_resources("issues", "pull_requests")

    # dlt's merge disposition generates a SQL file that fails against a fresh
    # MotherDuck destination because it assumes child tables already exist.
    # Replace is safe here — PR data is small and fully replaced each run.
    if args.motherduck:
        source.resources["pull_requests"].apply_hints(write_disposition="replace")

    loader_kwargs = {}
    if not args.motherduck:
        loader_kwargs["loader_file_format"] = "parquet"

    load_info = pipeline.run(source, **loader_kwargs)
    print(load_info)


if __name__ == "__main__":
    main()
