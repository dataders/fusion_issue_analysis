# Graphene tab

This directory contains the Graphene project used for the bakeoff tab:

- `tables/fusion_issue_metrics.gsql` defines the semantic model over dashboard-ready extracts.
- `index.md` is the Graphene dashboard source.
- `build.py` materializes a local DuckDB snapshot, validates the Graphene project, and writes the GitHub Pages-compatible `index.html`.

Graphene currently serves pages through its local server rather than a static export command. The production tab therefore renders a static compatibility artifact from the same canonical dbt dashboard models while keeping the Graphene source files in the repo and validating them with the public Graphene CLI.
