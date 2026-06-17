import unittest
import pandas as pd
from _path import *
from core.cycles import add_cycle_column


class TestAddCycleColumn(unittest.TestCase):

    def test_adds_cycle_column_when_missing(self):
        dates = [f"2025-09-{i:02d}" for i in range(1, 21)]
        df = pd.DataFrame({"日期": dates, "值": range(20)})
        result = add_cycle_column(df)
        self.assertIn("训练周期", result.columns)

    def test_keeps_existing_cycle_column(self):
        df = pd.DataFrame({
            "日期": ["2025-09-01", "2025-09-02"],
            "训练周期": ["自定义周期1", "自定义周期2"],
        })
        result = add_cycle_column(df)
        self.assertListEqual(list(result["训练周期"]), ["自定义周期1", "自定义周期2"])

    def test_cycle_labels_format(self):
        dates = [f"2025-09-{i:02d}" for i in range(1, 21)]
        df = pd.DataFrame({"日期": dates, "值": range(20)})
        result = add_cycle_column(df)
        unique_cycles = sorted(result["训练周期"].unique())
        self.assertEqual(len(unique_cycles), 4)
        for i, cycle in enumerate(unique_cycles):
            self.assertEqual(cycle, f"第{i+1}周期")

    def test_sorted_by_date(self):
        dates = ["2025-09-20", "2025-09-01", "2025-09-10", "2025-09-05"]
        df = pd.DataFrame({"日期": dates, "值": [4, 1, 3, 2]})
        result = add_cycle_column(df)
        self.assertIn("训练周期", result.columns)
        self.assertEqual(len(result), 4)

    def test_small_dataset_cycles(self):
        dates = ["2025-09-01", "2025-09-02", "2025-09-03"]
        df = pd.DataFrame({"日期": dates, "值": range(3)})
        result = add_cycle_column(df)
        unique_cycles = result["训练周期"].unique()
        self.assertGreaterEqual(len(unique_cycles), 1)
        self.assertLessEqual(len(unique_cycles), 4)

    def test_does_not_modify_original(self):
        dates = [f"2025-09-{i:02d}" for i in range(1, 11)]
        df = pd.DataFrame({"日期": dates, "值": range(10)})
        original_cols = list(df.columns)
        add_cycle_column(df)
        self.assertListEqual(list(df.columns), original_cols)

    def test_date_types(self):
        dates = [f"2025-09-{i:02d}" for i in range(1, 11)]
        df = pd.DataFrame({"日期": dates, "值": range(10)})
        result = add_cycle_column(df)
        self.assertIn("训练周期", result.columns)
        self.assertNotIn("日期_dt", result.columns)


if __name__ == "__main__":
    unittest.main()
