"""
Extract issues, comments, and reactions from dbt-labs/dbt-fusion using dlt's GitHub source.
Writes parquet files to data/raw/.
"""

import os
import dlt
from github import github_reactions


def main():
    raw_path = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
    os.makedirs(raw_path, exist_ok=True)

    # Pass GITHUB_TOKEN as access_token directly
    access_token = os.environ.get("GITHUB_TOKEN") or os.environ.get(
        "SOURCES__GITHUB__ACCESS_TOKEN"
    )
    if not access_token:
        raise ValueError("Set GITHUB_TOKEN or SOURCES__GITHUB__ACCESS_TOKEN env var")

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
        items_per_page=100,
    ).with_resources("issues")

    load_info = pipeline.run(source, loader_file_format="parquet")
    print(load_info)


if __name__ == "__main__":
    main()
