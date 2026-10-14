import unittest
from unittest.mock import patch

from dashboard.mviz import generate_data


class MvizGenerateDataTests(unittest.TestCase):
    def test_percentage_columns_are_normalized_for_pct_format(self) -> None:
        specs = {}
        meta = {"as_of_date": "2026-01-01", "source_repo": "r", "source_label": "l", "days_stale": 0}

        def fake_tile_rows(tile_id: str):
            return {"response_weekly": [{"week": "2026-01-01", "pct_responded_48h": 82}]}.get(tile_id, [])

        with (
            patch.object(generate_data, "DATA_DIR", generate_data.DATA_DIR),
            patch.object(generate_data.Path, "mkdir"),
            patch.object(generate_data, "write_theme"),
            patch.object(generate_data, "write_json"),
            patch.object(generate_data.tiles, "one", return_value=meta),
            patch.object(generate_data.tiles, "kpis", return_value=[]),
            patch.object(generate_data.tiles, "tile_rows", side_effect=fake_tile_rows),
            patch.object(generate_data, "spec", side_effect=lambda tile_id, **kw: specs.update({tile_id: kw})),
            patch.object(generate_data, "category_bars"),
            patch.object(generate_data, "issue_table"),
        ):
            generate_data.main()

        self.assertEqual(specs["response_weekly"]["data"], [{"week": "2026-01-01", "answered_48h": 0.82}])


if __name__ == "__main__":
    unittest.main()
