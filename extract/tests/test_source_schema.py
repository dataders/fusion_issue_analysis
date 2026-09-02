from github import github_reactions


def test_issue_schema_preserves_nullable_milestone_due_date():
    source = github_reactions("dbt-labs", "dbt-fusion", access_token="test")

    schema = source.resources["issues"].compute_table_schema()

    assert schema["columns"]["milestone__due_on"] == {
        "name": "milestone__due_on",
        "data_type": "timestamp",
        "nullable": True,
    }


def test_milestone_schema_preserves_nullable_columns():
    source = github_reactions("dbt-labs", "dbt-fusion", access_token="test")

    columns = source.resources["milestones"].compute_table_schema()["columns"]

    assert columns["due_on"]["data_type"] == "timestamp"
    assert columns["closed_at"]["data_type"] == "timestamp"
    assert columns["description"]["data_type"] == "text"
