import unittest
import pandas as pd
from _path import *
from core.filters import apply_filters
from core.cycles import add_cycle_column


class TestApplyFilters(unittest.TestCase):

    def setUp(self):
        data = {
            "日期": ["2025-09-01", "2025-09-05", "2025-09-10", "2025-09-15", "2025-09-20"],
            "舞种": ["身韵", "水袖", "剑舞", "扇舞", "把杆"],
            "动作类型": ["软开度", "旋转", "跳跃", "翻身", "控制"],
            "学员级别": ["初级", "中级", "高级", "表演级", "中级"],
            "指导老师": ["张老师", "李老师", "王老师", "赵老师", "张老师"],
            "比赛阶段": ["日常训练", "赛前集训", "比赛周", "赛后恢复", "日常训练"],
            "训练时长_分钟": [60, 90, 120, 45, 75],
            "心率区间": ["热身区(<110)", "有氧区(110-130)", "混氧区(130-150)", "无氧区(150-170)", "极限区(>170)"],
            "平均心率": [95, 120, 140, 160, 180],
            "主观疲劳评分": [3.0, 5.0, 7.5, 8.0, 4.5],
            "软开度": [60.0, 70.0, 80.0, 85.0, 65.0],
            "旋转稳定度": [50.0, 65.0, 75.0, 80.0, 55.0],
            "跳跃高度": [55.0, 68.0, 78.0, 82.0, 60.0],
            "动作完成度": [58.0, 70.0, 78.0, 82.0, 62.0],
        }
        self.df = pd.DataFrame(data)
        self.df_with_cycle = add_cycle_column(self.df)

    def test_no_filters_returns_all(self):
        result = apply_filters(self.df_with_cycle, [], [], [], [], None)
        self.assertEqual(len(result), 5)

    def test_filter_by_level(self):
        result = apply_filters(self.df_with_cycle, ["中级"], [], [], [], None)
        self.assertEqual(len(result), 2)
        self.assertTrue(all(result["学员级别"] == "中级"))

    def test_filter_by_teacher(self):
        result = apply_filters(self.df_with_cycle, [], [], ["张老师"], [], None)
        self.assertEqual(len(result), 2)
        self.assertTrue(all(result["指导老师"] == "张老师"))

    def test_filter_by_stage(self):
        result = apply_filters(self.df_with_cycle, [], [], [], ["日常训练"], None)
        self.assertEqual(len(result), 2)
        self.assertTrue(all(result["比赛阶段"] == "日常训练"))

    def test_filter_by_cycle(self):
        df = self.df_with_cycle
        cycle_name = df["训练周期"].iloc[0]
        result = apply_filters(df, [], [cycle_name], [], [], None)
        self.assertGreater(len(result), 0)
        self.assertTrue(all(result["训练周期"] == cycle_name))

    def test_filter_by_date_range(self):
        date_range = ("2025-09-05", "2025-09-15")
        result = apply_filters(self.df_with_cycle, [], [], [], [], date_range)
        self.assertEqual(len(result), 3)

    def test_combined_filters(self):
        result = apply_filters(
            self.df_with_cycle,
            ["中级"],
            [],
            ["张老师"],
            ["日常训练"],
            None,
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["学员级别"], "中级")
        self.assertEqual(result.iloc[0]["指导老师"], "张老师")

    def test_empty_result_filters(self):
        result = apply_filters(self.df_with_cycle, ["不存在的级别"], [], [], [], None)
        self.assertTrue(result.empty)

    def test_filter_without_cycle_column(self):
        df_no_cycle = self.df.copy()
        result = apply_filters(df_no_cycle, [], ["第1周期"], [], [], None)
        self.assertEqual(len(result), len(df_no_cycle))


if __name__ == "__main__":
    unittest.main()
