import unittest
import pandas as pd
from _path import *
from core.schedule import generate_schedule


def _make_sample_df(n=20, avg_fatigue=5.0, avg_duration=70):
    records = []
    dances = ["身韵", "水袖", "剑舞", "扇舞"]
    movements = ["软开度", "旋转", "跳跃", "翻身"]
    hr_zones = ["有氧区(110-130)", "混氧区(130-150)", "无氧区(150-170)"]
    for i in range(n):
        records.append({
            "日期": f"2025-09-{i+1:02d}",
            "舞种": dances[i % len(dances)],
            "动作类型": movements[i % len(movements)],
            "学员级别": "中级",
            "指导老师": "张老师",
            "比赛阶段": "日常训练",
            "训练时长_分钟": avg_duration + i % 10,
            "心率区间": hr_zones[i % len(hr_zones)],
            "平均心率": 120 + i % 30,
            "主观疲劳评分": avg_fatigue + (i % 5) * 0.3,
            "软开度": 65.0 + i % 10,
            "旋转稳定度": 55.0 + i % 10,
            "跳跃高度": 60.0 + i % 10,
            "动作完成度": 70.0 + i % 10,
        })
    return pd.DataFrame(records)


class TestGenerateSchedule(unittest.TestCase):

    def test_empty_dataframe_returns_empty(self):
        df = pd.DataFrame()
        result = generate_schedule(df)
        self.assertEqual(result, [])

    def test_returns_list_of_tuples(self):
        df = _make_sample_df()
        result = generate_schedule(df)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        for item in result:
            self.assertIsInstance(item, tuple)
            self.assertEqual(len(item), 3)

    def test_high_fatigue_suggests_reduction(self):
        df = _make_sample_df(n=30, avg_fatigue=8.0)
        result = generate_schedule(df)
        categories = [item[0] for item in result]
        self.assertIn("训练强度", categories)
        for cat, rec, detail in result:
            if cat == "训练强度":
                self.assertIn("降低", rec)

    def test_low_fatigue_suggests_increase(self):
        df = _make_sample_df(n=30, avg_fatigue=3.0)
        result = generate_schedule(df)
        for cat, rec, detail in result:
            if cat == "训练强度":
                self.assertIn("提升", rec)

    def test_moderate_fatigue_suggests_maintain(self):
        df = _make_sample_df(n=30, avg_fatigue=5.5)
        result = generate_schedule(df)
        for cat, rec, detail in result:
            if cat == "训练强度":
                self.assertIn("维持", rec)

    def test_suggests_weakest_metric_to_improve(self):
        df = _make_sample_df(n=30)
        df["软开度"] = 40.0
        df["旋转稳定度"] = 70.0
        df["跳跃高度"] = 65.0
        df["动作完成度"] = 72.0
        result = generate_schedule(df)
        categories = [item[0] for item in result]
        self.assertIn("重点加强", categories)
        for cat, rec, detail in result:
            if cat == "重点加强":
                self.assertIn("软开度", rec)

    def test_suggests_strongest_metric_to_maintain(self):
        df = _make_sample_df(n=30)
        df["软开度"] = 40.0
        df["旋转稳定度"] = 70.0
        df["跳跃高度"] = 65.0
        df["动作完成度"] = 90.0
        result = generate_schedule(df)
        categories = [item[0] for item in result]
        self.assertIn("保持优势", categories)
        for cat, rec, detail in result:
            if cat == "保持优势":
                self.assertIn("动作完成度", rec)

    def test_dance_arrangement_suggestion(self):
        df = _make_sample_df(n=30)
        result = generate_schedule(df)
        categories = [item[0] for item in result]
        self.assertIn("舞种安排", categories)

    def test_heart_rate_control_suggestion(self):
        df = _make_sample_df(n=30)
        result = generate_schedule(df)
        categories = [item[0] for item in result]
        self.assertIn("心率控制", categories)

    def test_duration_recommendation(self):
        df = _make_sample_df(n=30, avg_duration=80)
        result = generate_schedule(df)
        categories = [item[0] for item in result]
        self.assertIn("建议时长", categories)
        for cat, rec, detail in result:
            if cat == "建议时长":
                self.assertIn("分钟", rec)


if __name__ == "__main__":
    unittest.main()
