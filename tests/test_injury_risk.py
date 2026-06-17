import unittest
import pandas as pd
import numpy as np
from _path import *
from core.injury_risk import (
    has_injury_data,
    missing_injury_columns,
    compute_injury_risk_score,
    risk_level,
    detect_injury_risk_patterns,
    build_old_injury_risk_list,
    build_recovery_tracking_table,
)


def _make_base_records(n=10, **overrides):
    records = []
    for i in range(n):
        record = {
            "日期": f"2025-09-{i+1:02d}",
            "舞种": "身韵",
            "动作类型": "软开度",
            "学员级别": "中级",
            "指导老师": "张老师",
            "比赛阶段": "日常训练",
            "训练时长_分钟": 60,
            "心率区间": "有氧区(110-130)",
            "平均心率": 120,
            "主观疲劳评分": 5.0,
            "软开度": 70.0,
            "旋转稳定度": 60.0,
            "跳跃高度": 65.0,
            "动作完成度": 75.0,
        }
        record.update(overrides)
        records.append(record)
    return pd.DataFrame(records)


def _make_injury_records(n=10, **overrides):
    records = []
    for i in range(n):
        record = {
            "日期": f"2025-09-{i+1:02d}",
            "舞种": "身韵",
            "动作类型": "软开度",
            "学员级别": "中级",
            "指导老师": "张老师",
            "比赛阶段": "日常训练",
            "训练时长_分钟": 60,
            "心率区间": "有氧区(110-130)",
            "平均心率": 120,
            "主观疲劳评分": 5.0,
            "软开度": 70.0,
            "旋转稳定度": 60.0,
            "跳跃高度": 65.0,
            "动作完成度": 75.0,
            "疼痛部位": "腰部",
            "疼痛评分": 3.0,
            "旧伤标记": "否",
            "恢复状态": "完全恢复",
            "睡眠时长_小时": 7.5,
            "恢复训练类型": "常规训练",
        }
        record.update(overrides)
        records.append(record)
    return pd.DataFrame(records)


class TestHasInjuryData(unittest.TestCase):

    def test_no_injury_columns(self):
        df = _make_base_records()
        self.assertFalse(has_injury_data(df))

    def test_with_injury_columns(self):
        df = _make_injury_records()
        self.assertTrue(has_injury_data(df))

    def test_partial_injury_columns(self):
        df = _make_base_records()
        df["疼痛部位"] = "腰部"
        self.assertTrue(has_injury_data(df))


class TestMissingInjuryColumns(unittest.TestCase):

    def test_all_missing(self):
        df = _make_base_records()
        missing = missing_injury_columns(df)
        self.assertEqual(len(missing), 6)

    def test_none_missing(self):
        df = _make_injury_records()
        missing = missing_injury_columns(df)
        self.assertEqual(len(missing), 0)

    def test_partial_missing(self):
        df = _make_base_records()
        df["疼痛部位"] = "腰部"
        df["疼痛评分"] = 3.0
        missing = missing_injury_columns(df)
        self.assertEqual(len(missing), 4)
        self.assertIn("旧伤标记", missing)


class TestComputeInjuryRiskScore(unittest.TestCase):

    def test_low_risk_score(self):
        row = pd.Series({
            "主观疲劳评分": 2.0,
            "动作完成度": 85.0,
            "训练时长_分钟": 60,
            "心率区间": "有氧区(110-130)",
        })
        score = compute_injury_risk_score(row)
        self.assertLess(score, 25)

    def test_high_risk_score(self):
        row = pd.Series({
            "主观疲劳评分": 9.0,
            "疼痛评分": 8.0,
            "旧伤标记": "是",
            "睡眠时长_小时": 4.5,
            "训练时长_分钟": 130,
            "心率区间": "极限区(>170)",
            "动作完成度": 45.0,
        })
        score = compute_injury_risk_score(row)
        self.assertGreaterEqual(score, 40)

    def test_old_injury_adds_score(self):
        row_no_injury = pd.Series({
            "主观疲劳评分": 5.0,
            "旧伤标记": "否",
        })
        row_with_injury = pd.Series({
            "主观疲劳评分": 5.0,
            "旧伤标记": "是",
        })
        score_no = compute_injury_risk_score(row_no_injury)
        score_with = compute_injury_risk_score(row_with_injury)
        self.assertGreater(score_with, score_no)
        self.assertAlmostEqual(score_with - score_no, 15.0)

    def test_low_sleep_adds_score(self):
        row_enough = pd.Series({
            "主观疲劳评分": 5.0,
            "睡眠时长_小时": 8.0,
        })
        row_low = pd.Series({
            "主观疲劳评分": 5.0,
            "睡眠时长_小时": 4.0,
        })
        score_enough = compute_injury_risk_score(row_enough)
        score_low = compute_injury_risk_score(row_low)
        self.assertGreater(score_low, score_enough)

    def test_score_capped_at_100(self):
        row = pd.Series({
            "主观疲劳评分": 10.0,
            "疼痛评分": 10.0,
            "旧伤标记": "是",
            "睡眠时长_小时": 3.0,
            "训练时长_分钟": 150,
            "心率区间": "极限区(>170)",
            "动作完成度": 30.0,
        })
        score = compute_injury_risk_score(row)
        self.assertLessEqual(score, 100.0)

    def test_nan_values_handled(self):
        row = pd.Series({
            "主观疲劳评分": np.nan,
            "疼痛评分": np.nan,
            "睡眠时长_小时": np.nan,
        })
        score = compute_injury_risk_score(row)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0)


class TestRiskLevel(unittest.TestCase):

    def test_low_risk(self):
        self.assertEqual(risk_level(10), "低风险")

    def test_medium_risk(self):
        self.assertEqual(risk_level(30), "中风险")

    def test_high_risk(self):
        self.assertEqual(risk_level(50), "高风险")

    def test_boundary_at_25(self):
        self.assertEqual(risk_level(24.9), "低风险")
        self.assertEqual(risk_level(25.0), "中风险")

    def test_boundary_at_40(self):
        self.assertEqual(risk_level(39.9), "中风险")
        self.assertEqual(risk_level(40.0), "高风险")


class TestDetectInjuryRiskPatterns(unittest.TestCase):

    def test_empty_dataframe_returns_empty(self):
        df = pd.DataFrame()
        result = detect_injury_risk_patterns(df)
        self.assertEqual(result, [])

    def test_high_fatigue_high_pain_low_completion(self):
        records = []
        for i in range(10):
            is_high = i < 5
            records.append({
                "日期": f"2025-09-{i+1:02d}",
                "舞种": "身韵",
                "动作类型": "软开度",
                "训练时长_分钟": 60,
                "心率区间": "有氧区(110-130)",
                "主观疲劳评分": 8.5 if is_high else 3.0,
                "疼痛评分": 7.0 if is_high else 2.0,
                "动作完成度": 55.0 if is_high else 80.0,
                "旋转稳定度": 60.0,
            })
        df = pd.DataFrame(records)
        patterns = detect_injury_risk_patterns(df)
        titles = [p["title"] for p in patterns]
        self.assertTrue(any("高疲劳叠加高疼痛" in t for t in titles))

    def test_old_injury_high_intensity_jump(self):
        records = []
        for i in range(5):
            records.append({
                "日期": f"2025-09-{i+1:02d}",
                "舞种": "身韵",
                "动作类型": "跳跃",
                "训练时长_分钟": 120,
                "主观疲劳评分": 7.5,
                "旧伤标记": "是",
                "疼痛评分": 5.0,
                "疼痛部位": "膝盖",
            })
        df = pd.DataFrame(records)
        patterns = detect_injury_risk_patterns(df)
        titles = [p["title"] for p in patterns]
        self.assertTrue(any("旧伤学员" in t and "跳跃" in t for t in titles))

    def test_low_sleep_rotation_instability(self):
        records = []
        for i in range(15):
            is_low_sleep = i < 8
            records.append({
                "日期": f"2025-09-{i+1:02d}",
                "舞种": "身韵",
                "动作类型": "旋转",
                "训练时长_分钟": 60,
                "主观疲劳评分": 5.0,
                "睡眠时长_小时": 4.5 if is_low_sleep else 8.0,
                "旋转稳定度": np.random.normal(50, 15) if is_low_sleep else np.random.normal(70, 3),
            })
        df = pd.DataFrame(records)
        patterns = detect_injury_risk_patterns(df)
        titles = [p["title"] for p in patterns]
        self.assertTrue(any("睡眠不足" in t and "旋转稳定度" in t for t in titles))

    def test_frequent_pain_location(self):
        records = []
        for i in range(10):
            records.append({
                "日期": f"2025-09-{i+1:02d}",
                "疼痛部位": "膝盖",
                "疼痛评分": 6.0,
            })
        df = pd.DataFrame(records)
        patterns = detect_injury_risk_patterns(df)
        titles = [p["title"] for p in patterns]
        self.assertTrue(any("膝盖" in t and "频繁" in t for t in titles))

    def test_pattern_structure(self):
        records = []
        for i in range(10):
            records.append({
                "日期": f"2025-09-{i+1:02d}",
                "舞种": "身韵",
                "动作类型": "软开度",
                "训练时长_分钟": 60,
                "心率区间": "有氧区(110-130)",
                "主观疲劳评分": 5.0,
                "动作完成度": 70.0,
                "疼痛部位": "腰部",
                "疼痛评分": 3.0,
                "旧伤标记": "否",
                "恢复状态": "完全恢复",
                "睡眠时长_小时": 7.0,
            })
        df = pd.DataFrame(records)
        patterns = detect_injury_risk_patterns(df)
        for p in patterns:
            self.assertIn("type", p)
            self.assertIn("title", p)
            self.assertIn("detail", p)
            self.assertIn(p["type"], ["warning", "success", "info"])


class TestBuildOldInjuryRiskList(unittest.TestCase):

    def test_no_old_injury_column(self):
        df = _make_base_records()
        result = build_old_injury_risk_list(df)
        self.assertTrue(result.empty)

    def test_with_old_injury(self):
        df = _make_injury_records(n=5, 旧伤标记="是", 恢复状态="恢复中", 动作类型="跳跃")
        result = build_old_injury_risk_list(df)
        self.assertFalse(result.empty)
        self.assertIn("复发风险评分", result.columns)
        self.assertIn("风险等级", result.columns)

    def test_no_old_injury_records(self):
        df = _make_injury_records(n=5, 旧伤标记="否")
        result = build_old_injury_risk_list(df)
        self.assertTrue(result.empty)


class TestBuildRecoveryTrackingTable(unittest.TestCase):

    def test_no_recovery_columns(self):
        df = _make_base_records()
        result = build_recovery_tracking_table(df)
        self.assertTrue(result.empty)

    def test_with_recovery_data(self):
        df = _make_injury_records()
        result = build_recovery_tracking_table(df)
        self.assertFalse(result.empty)
        self.assertIn("恢复状态", result.columns)


if __name__ == "__main__":
    unittest.main()
