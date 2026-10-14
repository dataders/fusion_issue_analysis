"""Verify the assignee chart's population and top-15 cutoff against real SQL."""

from pathlib import Path

import duckdb
from jinja2 import Environment


def test_assignee_ranking_excludes_unassigned_before_limit():
    model = Path(__file__).resolve().parents[1] / "transform/models/dashboard/assignee_workload.sql"
    sql = Environment().from_string(model.read_text()).render(ref=lambda name: name)
    with duckdb.connect() as con:
        con.execute("create table fct_issues (issue_dlt_id varchar, issue_category varchar, state varchar)")
        con.execute("create table stg_issue_assignees (issue_dlt_id varchar, assignee_login varchar)")
        # Unassigned work is larger than any person's workload and must not take
        # a place in the top 15. Ties resolve by login for a stable cutoff.
        issues = [(f"unassigned{i}", "bug", "OPEN") for i in range(30)]
        issues += [(f"assigned{i}", "bug", "OPEN") for i in range(16)]
        issues += [
            ("multi", "feature", "OPEN"),
            ("closed", "bug", "CLOSED"),
            ("epic", "epic", "OPEN"),
            ("null", "bug", "OPEN"),
        ]
        assignments = [(f"assigned{i}", f"user{i:02d}") for i in range(16)]
        assignments += [
            ("multi", "user00"),
            ("multi", "user01"),
            ("closed", "user15"),
            ("epic", "user15"),
            ("null", None),
        ]
        con.executemany("insert into fct_issues values (?, ?, ?)", issues)
        con.executemany("insert into stg_issue_assignees values (?, ?)", assignments)
        rows = con.execute(sql).fetchall()

    expected = [("user00", "bug", 1, 2), ("user00", "feature", 1, 2)]
    expected += [("user01", "bug", 1, 2), ("user01", "feature", 1, 2)]
    expected += [(f"user{i:02d}", "bug", 1, 1) for i in range(2, 15)]
    assert rows == expected
