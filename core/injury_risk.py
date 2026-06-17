import pandas as pd
import numpy as np


OPTIONAL_INJURY_COLUMNS = [
    "疼痛部位",
    "疼痛评分",
    "旧伤标记",
    "恢复状态",
    "睡眠时长_小时",
    "恢复训练类型",
]


def has_injury_data(df):
    return any(col in df.columns for col in OPTIONAL_INJURY_COLUMNS)


def missing_injury_columns(df):
    return [col for col in OPTIONAL_INJURY_COLUMNS if col not in df.columns]


def compute_injury_risk_score(row):
    score = 0.0
    if "疼痛评分" in row.index and pd.notna(row.get("疼痛评分")):
        try:
            pain = float(row["疼痛评分"])
        except (ValueError, TypeError):
            pain = 0.0
        score += pain * 3.0

    if "主观疲劳评分" in row.index and pd.notna(row.get("主观疲劳评分")):
        try:
            fatigue = float(row["主观疲劳评分"])
        except (ValueError, TypeError):
            fatigue = 0.0
        score += fatigue * 2.0

    if "旧伤标记" in row.index and row.get("旧伤标记") == "是":
        score += 15.0

    if "睡眠时长_小时" in row.index and pd.notna(row.get("睡眠时长_小时")):
        try:
            sleep = float(row["睡眠时长_小时"])
        except (ValueError, TypeError):
            sleep = 7.0
        if sleep < 5:
            score += 12.0
        elif sleep < 6:
            score += 7.0
        elif sleep < 7:
            score += 3.0

    if "训练时长_分钟" in row.index and pd.notna(row.get("训练时长_分钟")):
        try:
            duration = float(row["训练时长_分钟"])
        except (ValueError, TypeError):
            duration = 0.0
        if duration > 120:
            score += 8.0
        elif duration > 90:
            score += 4.0

    if "心率区间" in row.index and pd.notna(row.get("心率区间")):
        hr = row["心率区间"]
        if hr in ("无氧区(150-170)", "极限区(>170)"):
            score += 5.0

    if "动作完成度" in row.index and pd.notna(row.get("动作完成度")):
        try:
            comp = float(row["动作完成度"])
        except (ValueError, TypeError):
            comp = 80.0
        if comp < 50:
            score += 10.0
        elif comp < 60:
            score += 5.0

    return min(round(score, 1), 100.0)


def risk_level(score):
    if score >= 40:
        return "高风险"
    elif score >= 25:
        return "中风险"
    else:
        return "低风险"


def detect_injury_risk_patterns(df):
    patterns = []
    if df.empty:
        return patterns

    df_sorted = df.sort_values("日期") if "日期" in df.columns else df

    if all(c in df_sorted.columns for c in ["主观疲劳评分", "动作完成度", "疼痛评分"]):
        high_fatigue_pain = df_sorted[
            (df_sorted["主观疲劳评分"] >= 7) & (df_sorted["疼痛评分"] >= 6)
        ]
        low_fatigue_pain = df_sorted[
            (df_sorted["主观疲劳评分"] <= 4) & (df_sorted["疼痛评分"] <= 3)
        ]
        if len(high_fatigue_pain) > 2 and len(low_fatigue_pain) > 2:
            comp_high = high_fatigue_pain["动作完成度"].mean()
            comp_low = low_fatigue_pain["动作完成度"].mean()
            diff = comp_high - comp_low
            if diff < -5:
                patterns.append({
                    "type": "warning",
                    "title": "⚠️ 高疲劳叠加高疼痛后完成度下降",
                    "detail": (
                        f"疲劳≥7且疼痛≥6时，动作完成度均值{comp_high:.1f}分；"
                        f"疲劳≤4且疼痛≤3时为{comp_low:.1f}分，"
                        f"差异{diff:.1f}分。高疲劳与高疼痛叠加显著影响动作完成质量，"
                        f"建议及时降低训练强度并关注疼痛部位恢复。"
                    ),
                })

    if "旧伤标记" in df_sorted.columns and "动作类型" in df_sorted.columns:
        old_injury = df_sorted[df_sorted["旧伤标记"] == "是"]
        if len(old_injury) > 2:
            jump_old = old_injury[old_injury["动作类型"] == "跳跃"]
            if len(jump_old) > 1:
                avg_dur = jump_old["训练时长_分钟"].mean() if "训练时长_分钟" in jump_old.columns else 0
                avg_fat = jump_old["主观疲劳评分"].mean() if "主观疲劳评分" in jump_old.columns else 0
                if avg_dur > 100 or avg_fat > 6:
                    patterns.append({
                        "type": "warning",
                        "title": "⚠️ 旧伤学员连续高强度跳跃训练风险升高",
                        "detail": (
                            f"旧伤学员跳跃训练平均时长{avg_dur:.0f}分钟、"
                            f"平均疲劳评分{avg_fat:.1f}，高强度跳跃训练可能加剧旧伤复发风险，"
                            f"建议减少跳跃训练频次并加强保护性训练。"
                        ),
                    })

    if "睡眠时长_小时" in df_sorted.columns and "旋转稳定度" in df_sorted.columns:
        low_sleep = df_sorted[df_sorted["睡眠时长_小时"] < 6]
        enough_sleep = df_sorted[df_sorted["睡眠时长_小时"] >= 7]
        if len(low_sleep) > 2 and len(enough_sleep) > 2:
            rot_low_sleep = low_sleep["旋转稳定度"]
            rot_enough_sleep = enough_sleep["旋转稳定度"]
            std_low = rot_low_sleep.std()
            std_enough = rot_enough_sleep.std()
            mean_diff = rot_enough_sleep.mean() - rot_low_sleep.mean()
            if std_low > std_enough * 1.3 and mean_diff > 2:
                patterns.append({
                    "type": "warning",
                    "title": "⚠️ 睡眠不足时旋转稳定度波动增大",
                    "detail": (
                        f"睡眠<6小时时旋转稳定度标准差{std_low:.1f}，"
                        f"睡眠≥7小时时为{std_enough:.1f}；"
                        f"均值差异{mean_diff:.1f}分。睡眠不足导致旋转动作稳定性显著波动，"
                        f"建议保证充足睡眠以降低受伤风险。"
                    ),
                })

    if "疼痛部位" in df_sorted.columns and "疼痛评分" in df_sorted.columns:
        pain_by_part = df_sorted.groupby("疼痛部位").agg(
            avg_pain=("疼痛评分", "mean"),
            count=("疼痛评分", "count"),
        ).reset_index()
        high_freq_parts = pain_by_part[pain_by_part["count"] >= 3]
        for _, row in high_freq_parts.iterrows():
            if row["avg_pain"] >= 5:
                patterns.append({
                    "type": "info",
                    "title": f"💡 {row['疼痛部位']}频繁疼痛预警",
                    "detail": (
                        f"{row['疼痛部位']}出现{int(row['count'])}次疼痛记录，"
                        f"平均疼痛评分{row['avg_pain']:.1f}分，建议关注该部位恢复情况。"
                    ),
                })

    return patterns


def build_old_injury_risk_list(df):
    if "旧伤标记" not in df.columns:
        return pd.DataFrame()

    old_injury = df[df["旧伤标记"] == "是"].copy()
    if old_injury.empty:
        return pd.DataFrame()

    result_rows = []
    for date, grp in old_injury.groupby("日期"):
        for _, row in grp.iterrows():
            pain_score = row.get("疼痛评分", np.nan)
            fatigue = row.get("主观疲劳评分", np.nan)
            duration = row.get("训练时长_分钟", np.nan)
            movement = row.get("动作类型", "")
            recovery = row.get("恢复状态", "")

            risk_score = 15.0
            if pd.notna(pain_score):
                try:
                    risk_score += float(pain_score) * 3.0
                except (ValueError, TypeError):
                    pass
            if pd.notna(fatigue):
                try:
                    risk_score += float(fatigue) * 2.0
                except (ValueError, TypeError):
                    pass
            if pd.notna(duration):
                try:
                    if float(duration) > 120:
                        risk_score += 8.0
                    elif float(duration) > 90:
                        risk_score += 4.0
                except (ValueError, TypeError):
                    pass
            if movement == "跳跃":
                risk_score += 8.0
            if recovery in ("未恢复", "恢复中"):
                risk_score += 10.0

            risk_score = min(round(risk_score, 1), 100.0)
            result_rows.append({
                "日期": date,
                "疼痛部位": row.get("疼痛部位", "未知"),
                "疼痛评分": pain_score,
                "动作类型": movement,
                "训练时长_分钟": duration,
                "恢复状态": recovery,
                "复发风险评分": risk_score,
                "风险等级": risk_level(risk_score),
            })

    return pd.DataFrame(result_rows).sort_values("复发风险评分", ascending=False)


def build_recovery_tracking_table(df):
    injury_tracking_cols = ["疼痛部位", "疼痛评分", "恢复状态", "恢复训练类型", "睡眠时长_小时"]
    available_cols = [c for c in injury_tracking_cols if c in df.columns]
    if not available_cols:
        return pd.DataFrame()
    display_cols = ["日期"] + available_cols if "日期" in df.columns else available_cols
    return df[display_cols].copy()
