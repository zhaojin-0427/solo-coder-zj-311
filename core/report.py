from datetime import datetime
from io import StringIO
from .constants import METRICS
from .injury_risk import (
    has_injury_data,
    compute_injury_risk_score,
    risk_level,
    detect_injury_risk_patterns,
    build_old_injury_risk_list,
    build_recovery_tracking_table,
)


def create_report(df, patterns, schedule):
    buf = StringIO()
    buf.write("=" * 60 + "\n")
    buf.write("       古典舞训练负荷与动作完成度 - 阶段训练报告\n")
    buf.write("=" * 60 + "\n\n")
    buf.write(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    buf.write(f"数据范围: {df['日期'].min()} ~ {df['日期'].max()}\n")
    buf.write(f"总记录数: {len(df)}\n\n")

    buf.write("-" * 40 + "\n")
    buf.write("一、总体数据概览\n")
    buf.write("-" * 40 + "\n")
    for m in METRICS:
        buf.write(f"  {m}: 均值{df[m].mean():.1f} / 最高{df[m].max():.1f} / 最低{df[m].min():.1f}\n")
    buf.write(f"  平均疲劳评分: {df['主观疲劳评分'].mean():.1f}\n")
    buf.write(f"  平均训练时长: {df['训练时长_分钟'].mean():.0f}分钟\n")
    buf.write(f"  平均心率: {df['平均心率'].mean():.0f}bpm\n\n")

    buf.write("-" * 40 + "\n")
    buf.write("二、舞种表现对比\n")
    buf.write("-" * 40 + "\n")
    for dance, grp in df.groupby("舞种"):
        buf.write(f"  {dance}: 完成度{grp['动作完成度'].mean():.1f} | 疲劳{grp['主观疲劳评分'].mean():.1f} | 时长{grp['训练时长_分钟'].mean():.0f}min\n")
    buf.write("\n")

    buf.write("-" * 40 + "\n")
    buf.write("三、识别的训练规律\n")
    buf.write("-" * 40 + "\n")
    for i, p in enumerate(patterns, 1):
        buf.write(f"  {i}. {p['title']}\n     {p['detail']}\n\n")

    buf.write("-" * 40 + "\n")
    buf.write("四、下周训练建议\n")
    buf.write("-" * 40 + "\n")
    for cat, rec, detail in schedule:
        buf.write(f"  [{cat}] {rec}\n    {detail}\n\n")

    if has_injury_data(df):
        buf.write("-" * 40 + "\n")
        buf.write("五、伤病风险与恢复建议\n")
        buf.write("-" * 40 + "\n")

        df_copy = df.copy()
        df_copy["风险评分"] = df_copy.apply(compute_injury_risk_score, axis=1)
        avg_risk = df_copy["风险评分"].mean()
        max_risk = df_copy["风险评分"].max()
        high_risk_count = (df_copy["风险评分"] >= 40).sum()
        buf.write(f"  整体风险概况: 均值{avg_risk:.1f}分 / 最高{max_risk:.1f}分 / 高风险记录{high_risk_count}条\n\n")

        if "疼痛部位" in df.columns:
            pain_data = df[df["疼痛部位"] != "无"] if "疼痛部位" in df.columns else pd.DataFrame()
            if not pain_data.empty:
                buf.write("  【疼痛部位统计】\n")
                for part, grp in pain_data.groupby("疼痛部位"):
                    cnt = len(grp)
                    avg_pain = grp["疼痛评分"].mean() if "疼痛评分" in grp.columns else 0
                    buf.write(f"    {part}: {cnt}次记录, 平均疼痛评分{avg_pain:.1f}\n")
                buf.write("\n")

        old_injury_df = build_old_injury_risk_list(df)
        if not old_injury_df.empty:
            buf.write("  【旧伤复发风险列表】\n")
            for _, row in old_injury_df.head(10).iterrows():
                buf.write(f"    {row['日期']} | {row['疼痛部位']} | 风险评分{row['复发风险评分']} | {row['风险等级']}\n")
            buf.write("\n")

        recovery_df = build_recovery_tracking_table(df)
        if not recovery_df.empty and "恢复状态" in recovery_df.columns:
            buf.write("  【恢复状态概况】\n")
            for status, grp in recovery_df.groupby("恢复状态"):
                buf.write(f"    {status}: {len(grp)}条记录\n")
            buf.write("\n")

        injury_patterns = detect_injury_risk_patterns(df)
        if injury_patterns:
            buf.write("  【识别的伤病风险模式】\n")
            for i, p in enumerate(injury_patterns, 1):
                buf.write(f"    {i}. {p['title']}\n       {p['detail']}\n\n")

        buf.write("  【建议】\n")
        if avg_risk >= 30:
            buf.write("    - 整体伤病风险偏高，建议降低训练强度、增加恢复日\n")
        if high_risk_count > 0:
            buf.write("    - 存在高风险记录，需重点关注旧伤部位恢复情况\n")
        if not old_injury_df.empty and any(old_injury_df["风险等级"] == "高风险"):
            buf.write("    - 旧伤学员中存在高风险个体，建议安排针对性恢复训练\n")
        buf.write("\n")

    buf.write("=" * 60 + "\n")
    buf.write("                    — 报告结束 —\n")
    buf.write("=" * 60 + "\n")
    return buf.getvalue()
