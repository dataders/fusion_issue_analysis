import unittest
from unittest.mock import patch

from dashboard.mviz import generate_data


class FakeConnection:
    def close(self) -> None:
        pass


class MvizGenerateDataTests(unittest.TestCase):
    def test_triage_percentage_kpis_are_normalized_for_pct_format(self) -> None:
        writes = {}

        def fake_query(_con, sql: str):
            responses = {
                "SELECT * FROM summary_kpis": [{
                    "closed_4w": 10,
                    "opened_4w": 12,
                    "rolling_median_close_days": 4,
                    "pct_responded_48h": 82,
                    "open_issues": 30,
                    "stale_count": 3,
                }],
                "SELECT * FROM cumulative_flow": [],
                "SELECT * FROM bug_velocity": [],
                "SELECT * FROM enh_velocity": [],
                "SELECT * FROM response_pctiles": [],
                "SELECT * FROM age_distribution": [],
                "SELECT * FROM close_by_label": [],
                "SELECT * FROM assignee_workload": [],
                "triage_sql": [{
                    "pct_labeled": 94,
                    "pct_typed": 84,
                    "pct_assigned": 21,
                    "pct_milestoned": 3,
                }],
                "SELECT * FROM community_priorities": [],
            }
            return responses[sql]

        def capture_write(filename: str, data):
            writes[filename] = data

        with (
            patch.object(generate_data.os, "makedirs"),
            patch.object(generate_data, "get_connection", return_value=FakeConnection()),
            patch.object(generate_data, "load_sql", return_value="triage_sql"),
            patch.object(generate_data, "query", side_effect=fake_query),
            patch.object(generate_data, "write_json", side_effect=capture_write),
        ):
            generate_data.main()

        self.assertEqual(writes["kpi_triage_labeled.json"]["value"], 0.94)
        self.assertEqual(writes["kpi_triage_typed.json"]["value"], 0.84)
        self.assertEqual(writes["kpi_triage_assigned.json"]["value"], 0.21)
        self.assertEqual(writes["kpi_triage_milestoned.json"]["value"], 0.03)


if __name__ == "__main__":
    unittest.main()
