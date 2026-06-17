import pandas as pd


def detect_patterns(df):
    patterns = []
    if df.empty:
        return patterns

    df_sorted = df.sort_values("日期")

    fatigue_high = df_sorted[df_sorted["主观疲劳评分"] >= 7.5]
    fatigue_low = df_sorted[df_sorted["主观疲劳评分"] <= 4.5]

    if len(fatigue_high) > 2 and len(fatigue_low) > 2:
        comp_high_f = fatigue_high["动作完成度"].mean()
        comp_low_f = fatigue_low["动作完成度"].mean()
        diff = comp_high_f - comp_low_f
        if diff < -3:
            patterns.append({
                "type": "warning",
                "title": "⚠️ 高疲劳 → 完成度下降",
                "detail": f"疲劳评分≥7.5时，动作完成度均值{comp_high_f:.1f}分；疲劳评分≤4.5时为{comp_low_f:.1f}分，差异{diff:.1f}分。高疲劳状态显著影响动作完成质量。"
            })

    waist_types = ["软开度", "控制"]
    waist_data = df_sorted[df_sorted["动作类型"].isin(waist_types)]
    if len(waist_data) > 5:
        waist_data = waist_data.copy()
        waist_data["cum_duration"] = waist_data["训练时长_分钟"].rolling(3, min_periods=1).sum()
        high_load = waist_data[waist_data["cum_duration"] >= 200]
        if len(high_load) > 2:
            comp_high_load = high_load["动作完成度"].mean()
            normal_load = waist_data[waist_data["cum_duration"] < 200]["动作完成度"].mean()
            if comp_high_load < normal_load - 5:
                patterns.append({
                    "type": "warning",
                    "title": "⚠️ 连续高强度腰部训练后完成度下降",
                    "detail": f"软开度/控制类动作连续3次累计≥200分钟时，完成度均值{comp_high_load:.1f}，正常负荷下{normal_load:.1f}，下降{normal_load - comp_high_load:.1f}分。建议分散腰部训练强度。"
                })

    rotation_data = df_sorted[df_sorted["动作类型"] == "旋转"]
    if len(rotation_data) > 4:
        rest_enough = rotation_data[rotation_data["主观疲劳评分"] <= 5]
        rest_tired = rotation_data[rotation_data["主观疲劳评分"] > 5]
        if len(rest_enough) > 1 and len(rest_tired) > 1:
            rot_rest = rest_enough["旋转稳定度"].mean()
            rot_tired = rest_tired["旋转稳定度"].mean()
            if rot_rest > rot_tired + 3:
                patterns.append({
                    "type": "success",
                    "title": "✅ 休息充足时转圈稳定度提升",
                    "detail": f"疲劳评分≤5时旋转稳定度{rot_rest:.1f}，疲劳评分>5时为{rot_tired:.1f}，差异{rot_rest - rot_tired:.1f}。充足的休息间隔显著提升旋转表现。"
                })

    if "训练时长_分钟" in df.columns:
        long_train = df_sorted[df_sorted["训练时长_分钟"] > 120]
        short_train = df_sorted[df_sorted["训练时长_分钟"] <= 90]
        if len(long_train) > 2 and len(short_train) > 2:
            soft_long = long_train["软开度"].mean()
            soft_short = short_train["软开度"].mean()
            comp_long = long_train["动作完成度"].mean()
            comp_short = short_train["动作完成度"].mean()
            if soft_long > soft_short + 3 and comp_long < comp_short - 2:
                patterns.append({
                    "type": "info",
                    "title": "💡 长时训练提升软开度但降低完成度",
                    "detail": f"训练>120分钟时软开度{soft_long:.1f}(vs {soft_short:.1f})提升，但完成度{comp_long:.1f}(vs {comp_short:.1f})下降。长时间训练有助于柔韧性但需注意疲劳管理。"
                })

    for dance in df_sorted["舞种"].unique():
        dance_df = df_sorted[df_sorted["舞种"] == dance]
        if len(dance_df) < 3:
            continue
        avg_comp = dance_df["动作完成度"].mean()
        avg_fatigue = dance_df["主观疲劳评分"].mean()
        overall_comp = df_sorted["动作完成度"].mean()
        if avg_comp > overall_comp + 5 and avg_fatigue < 6:
            patterns.append({
                "type": "success",
                "title": f"✅ {dance}高效训练模式",
                "detail": f"{dance}训练完成度{avg_comp:.1f}分(高于均值{overall_comp:.1f})，疲劳评分{avg_fatigue:.1f}(较低)，为高效益低负荷训练模式。"
            })

    df_sorted = df_sorted.copy()
    df_sorted["心率负荷指数"] = df_sorted["平均心率"] * df_sorted["训练时长_分钟"] / 1000
    corr_cols = ["主观疲劳评分", "软开度", "旋转稳定度", "跳跃高度", "动作完成度", "心率负荷指数"]
    if len(df_sorted) > 10:
        corr = df_sorted[corr_cols].corr()
        if abs(corr.loc["主观疲劳评分", "动作完成度"]) > 0.3:
            direction = "负相关" if corr.loc["主观疲劳评分", "动作完成度"] < 0 else "正相关"
            patterns.append({
                "type": "info",
                "title": f"📊 疲劳-完成度{direction}显著",
                "detail": f"主观疲劳评分与动作完成度的相关系数为{corr.loc['主观疲劳评分', '动作完成度']:.3f}，呈显著{direction}。疲劳管理是提升完成度的关键因素。"
            })

    return patterns
