import unittest
import pandas as pd
from _path import *
from core.report import create_report


def _make_sample_df():
    records = []
    dances = ["身韵", "水袖", "剑舞"]
    for i, dance in enumerate(dances):
        for j in range(5):
            records.append({
                "日期": f"2025-09-{j+1:02d}",
                "舞种": dance,
                "动作类型": "软开度",
                "学员级别": "中级",
                "指导老师": "张老师",
                "比赛阶段": "日常训练",
                "训练时长_分钟": 60 + j * 5,
                "心率区间": "有氧区(110-130)",
                "平均心率": 120 + j,
                "主观疲劳评分": 4.0 + j * 0.5,
                "软开度": 65.0 + j,
                "旋转稳定度": 55.0 + j,
                "跳跃高度": 60.0 + j,
                "动作完成度": 70.0 + j,
            })
    return pd.DataFrame(records)


class TestCreateReport(unittest.TestCase):

    def test_returns_string(self):
        df = _make_sample_df()
        patterns = []
        schedule = []
        result = create_report(df, patterns, schedule)
        self.assertIsInstance(result, str)

    def test_report_header(self):
        df = _make_sample_df()
        result = create_report(df, [], [])
        self.assertIn("古典舞训练负荷与动作完成度", result)
        self.assertIn("阶段训练报告", result)

    def test_report_contains_data_range(self):
        df = _make_sample_df()
        result = create_report(df, [], [])
        self.assertIn("数据范围", result)
        self.assertIn("2025-09-01", result)
        self.assertIn("2025-09-05", result)

    def test_report_contains_total_count(self):
        df = _make_sample_df()
        result = create_report(df, [], [])
        self.assertIn("总记录数", result)
        self.assertIn(str(len(df)), result)

    def test_report_contains_metrics_overview(self):
        df = _make_sample_df()
        result = create_report(df, [], [])
        self.assertIn("总体数据概览", result)
        self.assertIn("软开度", result)
        self.assertIn("旋转稳定度", result)
        self.assertIn("跳跃高度", result)
        self.assertIn("动作完成度", result)
        self.assertIn("平均疲劳评分", result)
        self.assertIn("平均训练时长", result)
        self.assertIn("平均心率", result)

    def test_report_contains_dance_comparison(self):
        df = _make_sample_df()
        result = create_report(df, [], [])
        self.assertIn("舞种表现对比", result)
        self.assertIn("身韵", result)
        self.assertIn("水袖", result)
        self.assertIn("剑舞", result)

    def test_report_contains_patterns(self):
        df = _make_sample_df()
        patterns = [
            {"type": "warning", "title": "⚠️ 测试规律1", "detail": "测试详情1"},
            {"type": "success", "title": "✅ 测试规律2", "detail": "测试详情2"},
        ]
        result = create_report(df, patterns, [])
        self.assertIn("识别的训练规律", result)
        self.assertIn("测试规律1", result)
        self.assertIn("测试规律2", result)
        self.assertIn("测试详情1", result)
        self.assertIn("测试详情2", result)

    def test_report_contains_schedule(self):
        df = _make_sample_df()
        schedule = [
            ("训练强度", "⬇️ 降低", "详情1"),
            ("重点加强", "🎯 软开度", "详情2"),
        ]
        result = create_report(df, [], schedule)
        self.assertIn("下周训练建议", result)
        self.assertIn("训练强度", result)
        self.assertIn("重点加强", result)
        self.assertIn("详情1", result)
        self.assertIn("详情2", result)

    def test_report_ending(self):
        df = _make_sample_df()
        result = create_report(df, [], [])
        self.assertIn("报告结束", result)

    def test_report_sections_order(self):
        df = _make_sample_df()
        patterns = [{"type": "info", "title": "测试", "detail": "详情"}]
        schedule = [("测试", "测试", "测试")]
        result = create_report(df, patterns, schedule)

        pos_overview = result.find("总体数据概览")
        pos_dance = result.find("舞种表现对比")
        pos_patterns = result.find("识别的训练规律")
        pos_schedule = result.find("下周训练建议")

        self.assertGreater(pos_dance, pos_overview)
        self.assertGreater(pos_patterns, pos_dance)
        self.assertGreater(pos_schedule, pos_patterns)


if __name__ == "__main__":
    unittest.main()
