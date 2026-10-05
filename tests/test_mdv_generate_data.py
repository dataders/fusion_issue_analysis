import unittest
from unittest.mock import patch

from dashboard.mdv import generate_data


class MdvGenerateDataTests(unittest.TestCase):
    def test_pct_bar_renders_text_progress(self) -> None:
        self.assertEqual(generate_data.pct_bar(50), "█████░░░░░ 50%")
        self.assertEqual(generate_data.pct_bar(None), "░░░░░░░░░░ 0%")

    def test_crosstab_pivots_categories_into_columns_with_total(self) -> None:
        rows = [
            {"area": "parser", "issue_category": "bug", "issue_count": 3, "area_total": 5},
            {"area": "parser", "issue_category": "feature", "issue_count": 2, "area_total": 5},
        ]
        written = {}

        with (
            patch.object(generate_data.tiles, "tile_rows", return_value=rows),
            patch.object(generate_data, "write_csv", side_effect=lambda name, data: written.update({name: data})),
        ):
            generate_data.crosstab("open_by_area", "area", "Area", total="area_total")

        (row,) = written["open_by_area.csv"]
        self.assertEqual(row["Area"], "parser")
        self.assertEqual(row["Total"], 5)
        self.assertEqual(row[generate_data.tiles.label("issue_category", "bug")], 3)
        self.assertEqual(row[generate_data.tiles.label("issue_category", "feature")], 2)


if __name__ == "__main__":
    unittest.main()
