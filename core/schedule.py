from .constants import METRICS


def generate_schedule(df):
    suggestions = []
    if df.empty:
        return suggestions

    recent = df.sort_values("日期").tail(min(50, len(df)))
    avg_fatigue = recent["主观疲劳评分"].mean()
    avg_duration = recent["训练时长_分钟"].mean()

    metric_avg = {m: recent[m].mean() for m in METRICS}
    weakest = min(metric_avg, key=metric_avg.get)
    strongest = max(metric_avg, key=metric_avg.get)

    if avg_fatigue >= 7:
        suggestions.append(("训练强度", "⬇️ 降低", f"近期平均疲劳{avg_fatigue:.1f}偏高，建议下周训练时长减少10-15%，增加休息日。"))
    elif avg_fatigue <= 4:
        suggestions.append(("训练强度", "⬆️ 可适度提升", f"近期平均疲劳{avg_fatigue:.1f}较低，有提升空间，建议逐步增加训练量。"))
    else:
        suggestions.append(("训练强度", "➡️ 维持", f"近期平均疲劳{avg_fatigue:.1f}适中，建议维持当前训练节奏。"))

    movement_map = {"软开度": "软开度训练", "旋转稳定度": "旋转训练", "跳跃高度": "跳跃训练", "动作完成度": "综合训练"}
    suggestions.append(("重点加强", f"🎯 {weakest}", f"{weakest}均值为{metric_avg[weakest]:.1f}分(四项最低)，建议下周增加{movement_map[weakest]}频次至每周3-4次。"))
    suggestions.append(("保持优势", f"🌟 {strongest}", f"{strongest}均值为{metric_avg[strongest]:.1f}分(四项最高)，保持现有训练量即可。"))

    dance_comp = recent.groupby("舞种")["动作完成度"].mean()
    worst_dance = dance_comp.idxmin()
    best_dance = dance_comp.idxmax()
    suggestions.append(("舞种安排", f"➕{worst_dance} ➖{best_dance}", f"完成度最低的舞种是{worst_dance}({dance_comp[worst_dance]:.1f}分)，建议增加训练；{best_dance}表现最好({dance_comp[best_dance]:.1f}分)可维持。"))

    hr_dist = recent["心率区间"].value_counts(normalize=True)
    anaerobic_ratio = hr_dist.get("无氧区(150-170)", 0) + hr_dist.get("极限区(>170)", 0)
    if anaerobic_ratio > 0.35:
        suggestions.append(("心率控制", "⚠️ 高强度占比过高", f"无氧+极限区间占比{anaerobic_ratio:.0%}，建议增加有氧区训练比例，控制在25%以内。"))
    else:
        suggestions.append(("心率控制", "✅ 分布合理", f"无氧+极限区间占比{anaerobic_ratio:.0%}，心率分布合理。"))

    suggestions.append(("建议时长", f"⏱️ {int(avg_duration * 0.9)}-{int(avg_duration * 1.1)}分钟/次", f"基于近期训练数据，推荐单次训练时长在{int(avg_duration * 0.9)}-{int(avg_duration * 1.1)}分钟。"))

    return suggestions
