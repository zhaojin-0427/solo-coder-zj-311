import unittest
import pandas as pd
import numpy as np
from _path import *
from core.patterns import detect_patterns


def _make_dataframe(records):
    return pd.DataFrame(records)


class TestDetectPatterns(unittest.TestCase):

    def test_empty_dataframe_returns_empty(self):
        df = pd.DataFrame()
        result = detect_patterns(df)
        self.assertEqual(result, [])

    def test_high_fatigue_low_completion_pattern(self):
        records = []
        for i in range(10):
            records.append({
                "日期": f"2025-09-{i+1:02d}",
                "舞种": "身韵",
                "动作类型": "软开度",
                "学员级别": "中级",
                "指导老师": "张老师",
                "比赛阶段": "日常训练",
                "训练时长_分钟": 60,
                "心率区间": "有氧区(110-130)",
                "平均心率": 120,
                "主观疲劳评分": 2.0 if i < 5 else 8.5,
                "软开度": 70.0,
                "旋转稳定度": 60.0,
                "跳跃高度": 65.0,
                "动作完成度": 80.0 if i < 5 else 60.0,
            })
        df = _make_dataframe(records)
        patterns = detect_patterns(df)
        titles = [p["title"] for p in patterns]
        self.assertTrue(any("高疲劳" in t and "完成度下降" in t for t in titles))

    def test_rest_improves_rotation_pattern(self):
        records = []
        for i in range(10):
            records.append({
                "日期": f"2025-09-{i+1:02d}",
                "舞种": "身韵",
                "动作类型": "旋转",
                "学员级别": "中级",
                "指导老师": "张老师",
                "比赛阶段": "日常训练",
                "训练时长_分钟": 60,
                "心率区间": "有氧区(110-130)",
                "平均心率": 120,
                "主观疲劳评分": 3.0 if i < 5 else 7.0,
                "软开度": 70.0,
                "旋转稳定度": 80.0 if i < 5 else 60.0,
                "跳跃高度": 65.0,
                "动作完成度": 70.0,
            })
        df = _make_dataframe(records)
        patterns = detect_patterns(df)
        titles = [p["title"] for p in patterns]
        self.assertTrue(any("休息充足" in t and "转圈稳定度" in t for t in titles))

    def test_pattern_structure(self):
        records = []
        for i in range(15):
            records.append({
                "日期": f"2025-09-{i+1:02d}",
                "舞种": "身韵",
                "动作类型": "软开度",
                "学员级别": "中级",
                "指导老师": "张老师",
                "比赛阶段": "日常训练",
                "训练时长_分钟": 80 + i * 5,
                "心率区间": "有氧区(110-130)",
                "平均心率": 120 + i,
                "主观疲劳评分": 2.0 + i * 0.5,
                "软开度": 70.0,
                "旋转稳定度": 60.0,
                "跳跃高度": 65.0,
                "动作完成度": 80.0 - i * 1.5,
            })
        df = _make_dataframe(records)
        patterns = detect_patterns(df)
        for p in patterns:
            self.assertIn("type", p)
            self.assertIn("title", p)
            self.assertIn("detail", p)
            self.assertIn(p["type"], ["warning", "success", "info"])

    def test_correlation_pattern(self):
        np.random.seed(42)
        n = 30
        fatigue = np.linspace(2, 9, n)
        completion = 85 - fatigue * 5 + np.random.normal(0, 2, n)
        records = []
        for i in range(n):
            records.append({
                "日期": f"2025-09-{i+1:02d}",
                "舞种": "身韵",
                "动作类型": "软开度",
                "学员级别": "中级",
                "指导老师": "张老师",
                "比赛阶段": "日常训练",
                "训练时长_分钟": 80,
                "心率区间": "有氧区(110-130)",
                "平均心率": 120,
                "主观疲劳评分": fatigue[i],
                "软开度": 70.0,
                "旋转稳定度": 60.0,
                "跳跃高度": 65.0,
                "动作完成度": completion[i],
            })
        df = _make_dataframe(records)
        patterns = detect_patterns(df)
        titles = [p["title"] for p in patterns]
        self.assertTrue(any("疲劳" in t and "相关" in t for t in titles))

    def test_efficient_dance_pattern(self):
        records = []
        dances = ["身韵", "水袖", "剑舞"]
        for d in dances:
            for i in range(5):
                is_efficient = d == "身韵"
                records.append({
                    "日期": f"2025-09-{i+1:02d}",
                    "舞种": d,
                    "动作类型": "软开度",
                    "学员级别": "中级",
                    "指导老师": "张老师",
                    "比赛阶段": "日常训练",
                    "训练时长_分钟": 60,
                    "心率区间": "有氧区(110-130)",
                    "平均心率": 120,
                    "主观疲劳评分": 3.0 if is_efficient else 7.0,
                    "软开度": 70.0,
                    "旋转稳定度": 60.0,
                    "跳跃高度": 65.0,
                    "动作完成度": 90.0 if is_efficient else 60.0,
                })
        df = _make_dataframe(records)
        patterns = detect_patterns(df)
        titles = [p["title"] for p in patterns]
        self.assertTrue(any("身韵" in t and "高效" in t for t in titles))


if __name__ == "__main__":
    unittest.main()
