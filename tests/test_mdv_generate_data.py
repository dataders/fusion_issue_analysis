import unittest

from dashboard.mdv import generate_data


class MdvGenerateDataTests(unittest.TestCase):
    def test_build_stats_formats_dashboard_values(self) -> None:
        rows = generate_data.build_stats(
            {
                "closed_4w": 17,
                "opened_4w": 12,
                "open_issues": 1234,
                "rolling_median_close_days": 6.25,
                "pct_responded_48h": 82,
            },
            {"pct_typed": 94},
        )

        self.assertEqual(rows[0], {"label": "Net flow (4wk)", "value": "+5", "delta": ""})
        self.assertEqual(rows[1], {"label": "Open issues", "value": "1,234", "delta": ""})
        self.assertEqual(rows[2], {"label": "Median close (4wk)", "value": "6.2d", "delta": ""})
        self.assertEqual(rows[3], {"label": "48h response SLA", "value": "82%", "delta": ""})
        self.assertEqual(rows[4], {"label": "Typed open issues", "value": "94%", "delta": ""})


if __name__ == "__main__":
    unittest.main()
