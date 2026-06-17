from datetime import datetime
from io import StringIO
from .constants import METRICS


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

    buf.write("=" * 60 + "\n")
    buf.write("                    — 报告结束 —\n")
    buf.write("=" * 60 + "\n")
    return buf.getvalue()
