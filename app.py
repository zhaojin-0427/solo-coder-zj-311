import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from io import BytesIO
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="古典舞训练负荷与动作完成度分析台", layout="wide", page_icon="🩰")

DANCE_TYPES = ["身韵", "水袖", "剑舞", "扇舞", "把杆", "毯技"]
MOVEMENT_TYPES = ["软开度", "旋转", "跳跃", "翻身", "控制", "步法"]
LEVELS = ["初级", "中级", "高级", "表演级"]
TEACHERS = ["张老师", "李老师", "王老师", "赵老师"]
COMPETITION_STAGES = ["日常训练", "赛前集训", "比赛周", "赛后恢复"]
HR_ZONES = ["热身区(<110)", "有氧区(110-130)", "混氧区(130-150)", "无氧区(150-170)", "极限区(>170)"]
METRICS = ["软开度", "旋转稳定度", "跳跃高度", "动作完成度"]


def generate_sample_data(n=600):
    np.random.seed(42)
    start_date = datetime(2025, 9, 1)
    records = []
    for i in range(n):
        date = start_date + timedelta(days=int(i * 90 / n))
        dance = np.random.choice(DANCE_TYPES)
        movement = np.random.choice(MOVEMENT_TYPES)
        level = np.random.choice(LEVELS, p=[0.25, 0.35, 0.25, 0.15])
        teacher = np.random.choice(TEACHERS)
        stage = np.random.choice(COMPETITION_STAGES, p=[0.4, 0.25, 0.2, 0.15])
        duration = np.random.randint(30, 150)
        hr_zone = np.random.choice(HR_ZONES, p=[0.15, 0.3, 0.25, 0.2, 0.1])
        avg_hr = {"热身区(<110)": 95, "有氧区(110-130)": 120, "混氧区(130-150)": 140, "无氧区(150-170)": 160, "极限区(>170)": 180}
        heart_rate = avg_hr[hr_zone] + np.random.randint(-8, 9)
        base_fatigue = np.random.randint(2, 8)
        duration_factor = (duration - 60) / 120
        hr_factor = (heart_rate - 100) / 100
        fatigue = np.clip(base_fatigue + duration_factor * 2 + hr_factor * 1.5, 1, 10)
        fatigue = round(fatigue, 1)

        base_soft = {"初级": 55, "中级": 68, "高级": 78, "表演级": 85}[level]
        base_rot = {"初级": 45, "中级": 60, "高级": 72, "表演级": 82}[level]
        base_jump = {"初级": 50, "中级": 62, "高级": 74, "表演级": 80}[level]
        base_comp = {"初级": 52, "中级": 65, "高级": 75, "表演级": 83}[level]

        fatigue_penalty = fatigue * 1.2
        duration_penalty = max(0, (duration - 90) * 0.15)
        hr_bonus = (heart_rate - 100) * 0.05 if heart_rate > 120 else 0

        soft = np.clip(base_soft - fatigue_penalty * 0.5 + hr_bonus + np.random.normal(0, 5), 0, 100)
        rot = np.clip(base_rot - fatigue_penalty * 0.8 + hr_bonus * 0.5 + np.random.normal(0, 6), 0, 100)
        jump = np.clip(base_jump - fatigue_penalty * 0.6 + np.random.normal(0, 5), 0, 100)
        comp = np.clip(base_comp - fatigue_penalty * 0.7 - duration_penalty + np.random.normal(0, 5), 0, 100)

        if dance == "身韵":
            comp += 3
        if movement == "软开度":
            soft += 5
        if movement == "旋转":
            rot += 5
        if movement == "跳跃":
            jump += 5

        if stage == "赛前集训":
            duration = int(duration * 1.3)
            fatigue = min(10, fatigue * 1.2)
        if stage == "比赛周":
            comp += 5
            fatigue = min(10, fatigue * 1.1)

        records.append({
            "日期": date.strftime("%Y-%m-%d"),
            "舞种": dance,
            "动作类型": movement,
            "学员级别": level,
            "指导老师": teacher,
            "比赛阶段": stage,
            "训练时长_分钟": duration,
            "心率区间": hr_zone,
            "平均心率": heart_rate,
            "主观疲劳评分": round(fatigue, 1),
            "软开度": round(soft, 1),
            "旋转稳定度": round(rot, 1),
            "跳跃高度": round(jump, 1),
            "动作完成度": round(comp, 1),
        })
    return pd.DataFrame(records)


def apply_filters(df, levels, cycles, teachers, stages, date_range):
    if levels:
        df = df[df["学员级别"].isin(levels)]
    if cycles:
        df = df[df["训练周期"].isin(cycles)] if "训练周期" in df.columns else df
    if teachers:
        df = df[df["指导老师"].isin(teachers)]
    if stages:
        df = df[df["比赛阶段"].isin(stages)]
    if date_range and len(date_range) == 2:
        df["日期"] = pd.to_datetime(df["日期"])
        df = df[(df["日期"] >= pd.to_datetime(date_range[0])) & (df["日期"] <= pd.to_datetime(date_range[1]))]
    return df


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


def create_report(df, patterns, schedule):
    from io import StringIO
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


def add_cycle_column(df):
    if "训练周期" not in df.columns:
        df = df.copy()
        df["日期_dt"] = pd.to_datetime(df["日期"])
        df = df.sort_values("日期_dt")
        dates_sorted = df["日期_dt"].unique()
        n = len(dates_sorted)
        cycle_size = max(1, n // 4)
        cycle_labels = []
        for i, d in enumerate(df["日期_dt"]):
            ci = min(i // cycle_size, 3)
            cycle_labels.append(f"第{ci+1}周期")
        df["训练周期"] = cycle_labels
        df = df.drop(columns=["日期_dt"])
    return df


def load_data(uploaded, use_sample):
    if uploaded is not None:
        df = pd.read_csv(uploaded)
    elif use_sample:
        df = generate_sample_data()
    else:
        return None
    df = add_cycle_column(df)
    return df


def main():
    st.markdown("""
    <style>
    .main-title {font-size:2.2rem; font-weight:700; color:#c0392b; text-align:center; margin-bottom:0.3rem;}
    .sub-title {font-size:1rem; color:#7f8c8d; text-align:center; margin-bottom:1.5rem;}
    .metric-card {background:linear-gradient(135deg,#fdf2e9,#fbeee6); border-radius:12px; padding:1.2rem; text-align:center; box-shadow:0 2px 8px rgba(0,0,0,0.08);}
    .metric-value {font-size:1.8rem; font-weight:700; color:#c0392b;}
    .metric-label {font-size:0.85rem; color:#7f8c8d;}
    .pattern-warning {background:#fff3cd; border-left:4px solid #ffc107; padding:0.8rem 1rem; border-radius:6px; margin:0.3rem 0;}
    .pattern-success {background:#d4edda; border-left:4px solid #28a745; padding:0.8rem 1rem; border-radius:6px; margin:0.3rem 0;}
    .pattern-info {background:#d1ecf1; border-left:4px solid #17a2b8; padding:0.8rem 1rem; border-radius:6px; margin:0.3rem 0;}
    .schedule-card {background:#f8f9fa; border-radius:10px; padding:1rem; margin:0.3rem 0; border:1px solid #e9ecef;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-title">🩰 古典舞训练负荷与动作完成度分析台</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Training Load & Movement Completion Analysis for Chinese Classical Dance</div>', unsafe_allow_html=True)

    with st.sidebar:
        st.header("📁 数据导入")
        uploaded = st.file_uploader("上传训练记录 CSV", type=["csv"])
        use_sample = st.checkbox("使用示例数据", value=True)

    df = load_data(uploaded, use_sample)

    if df is None:
        st.info("👈 请上传CSV文件或勾选「使用示例数据」开始分析")
        st.markdown("### 📋 CSV格式要求")
        st.markdown("""
        所需列：`日期, 舞种, 动作类型, 学员级别, 指导老师, 比赛阶段, 训练时长_分钟, 心率区间, 平均心率, 主观疲劳评分, 软开度, 旋转稳定度, 跳跃高度, 动作完成度`

        - **舞种**: 身韵、水袖、剑舞、扇舞、把杆、毯技
        - **动作类型**: 软开度、旋转、跳跃、翻身、控制、步法
        - **学员级别**: 初级、中级、高级、表演级
        - **比赛阶段**: 日常训练、赛前集训、比赛周、赛后恢复
        - **心率区间**: 热身区/有氧区/混氧区/无氧区/极限区
        - **主观疲劳评分**: 1-10分
        """)
        return

    with st.sidebar:
        st.divider()
        st.header("🔍 数据筛选")

        levels = st.multiselect("学员级别", sorted(df["学员级别"].unique()) if "学员级别" in df.columns else [])
        teachers = st.multiselect("指导老师", sorted(df["指导老师"].unique()) if "指导老师" in df.columns else [])
        stages = st.multiselect("比赛阶段", sorted(df["比赛阶段"].unique()) if "比赛阶段" in df.columns else [])
        cycles = st.multiselect("训练周期", sorted(df["训练周期"].unique()) if "训练周期" in df.columns else [])

        dates = pd.to_datetime(df["日期"]) if "日期" in df.columns else None
        if dates is not None:
            min_d, max_d = dates.min(), dates.max()
            date_range = st.date_input("日期范围", value=(min_d, max_d), min_value=min_d, max_value=max_d)
        else:
            date_range = None

    df_filtered = apply_filters(df, levels, cycles, teachers, stages, date_range)

    if df_filtered.empty:
        st.warning("当前筛选条件下无数据，请调整筛选条件")
        return

    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{df_filtered["动作完成度"].mean():.1f}</div><div class="metric-label">动作完成度均值</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{df_filtered["主观疲劳评分"].mean():.1f}</div><div class="metric-label">平均疲劳评分</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{df_filtered["训练时长_分钟"].mean():.0f}</div><div class="metric-label">平均训练时长(分)</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{len(df_filtered)}</div><div class="metric-label">筛选后记录数</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 训练负荷趋势", "🕸️ 动作完成度雷达", "🔥 疲劳热力图", "🎭 舞种对比", "📋 规律识别与排课建议"])

    with tab1:
        st.subheader("训练负荷趋势分析")
        df_trend = df_filtered.copy()
        df_trend["日期"] = pd.to_datetime(df_trend["日期"])
        df_trend = df_trend.sort_values("日期")
        daily = df_trend.groupby("日期").agg({
            "训练时长_分钟": "sum",
            "主观疲劳评分": "mean",
            "平均心率": "mean",
            "动作完成度": "mean",
        }).reset_index()

        fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                            subplot_titles=("每日训练总时长", "日均疲劳评分 & 平均心率", "日均动作完成度"),
                            vertical_spacing=0.08)

        fig.add_trace(go.Bar(x=daily["日期"], y=daily["训练时长_分钟"], name="训练时长(min)",
                             marker_color="#e74c3c", opacity=0.7), row=1, col=1)

        fig.add_trace(go.Scatter(x=daily["日期"], y=daily["主观疲劳评分"], name="疲劳评分",
                                 line=dict(color="#f39c12", width=2), mode="lines+markers", marker_size=4), row=2, col=1)
        fig.add_trace(go.Scatter(x=daily["日期"], y=daily["平均心率"], name="平均心率",
                                 line=dict(color="#3498db", width=2), mode="lines+markers", marker_size=4, yaxis="y2"), row=2, col=1)

        fig.add_trace(go.Scatter(x=daily["日期"], y=daily["动作完成度"], name="完成度",
                                 line=dict(color="#2ecc71", width=2.5), mode="lines+markers", marker_size=5), row=3, col=1)

        fig.update_layout(height=700, showlegend=True, title_text="训练负荷与完成度时间趋势")
        fig.update_xaxes(title_text="日期", row=3, col=1)
        st.plotly_chart(fig, width="stretch")

        st.subheader("心率区间分布与负荷关系")
        col_a, col_b = st.columns(2)
        with col_a:
            hr_dist = df_filtered["心率区间"].value_counts()
            fig_hr = px.pie(values=hr_dist.values, names=hr_dist.index, title="心率区间分布",
                            color_discrete_sequence=px.colors.sequential.Reds[1:])
            st.plotly_chart(fig_hr, width="stretch")
        with col_b:
            df_filtered_c = df_filtered.copy()
            df_filtered_c["心率数值"] = df_filtered_c["心率区间"].map({
                "热身区(<110)": 1, "有氧区(110-130)": 2, "混氧区(130-150)": 3, "无氧区(150-170)": 4, "极限区(>170)": 5
            })
            scatter = px.scatter(df_filtered_c, x="主观疲劳评分", y="动作完成度",
                                color="心率区间", size="训练时长_分钟",
                                title="疲劳-完成度-心率关联散点图",
                                color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(scatter, width="stretch")

    with tab2:
        st.subheader("动作完成度雷达图")
        col_r1, col_r2 = st.columns(2)

        with col_r1:
            st.markdown("**按舞种对比**")
            categories = METRICS
            fig_radar = go.Figure()
            for dance in df_filtered["舞种"].unique():
                dance_df = df_filtered[df_filtered["舞种"] == dance]
                values = [dance_df[m].mean() for m in categories]
                fig_radar.add_trace(go.Scatterpolar(
                    r=values + [values[0]],
                    theta=categories + [categories[0]],
                    fill="toself",
                    name=dance,
                    opacity=0.6
                ))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True,
                                    title="各舞种四维指标雷达图", height=500)
            st.plotly_chart(fig_radar, width="stretch")

        with col_r2:
            st.markdown("**按学员级别对比**")
            fig_radar2 = go.Figure()
            for lv in df_filtered["学员级别"].unique() if "学员级别" in df_filtered.columns else []:
                lv_df = df_filtered[df_filtered["学员级别"] == lv]
                values = [lv_df[m].mean() for m in categories]
                fig_radar2.add_trace(go.Scatterpolar(
                    r=values + [values[0]],
                    theta=categories + [categories[0]],
                    fill="toself",
                    name=lv,
                    opacity=0.6
                ))
            fig_radar2.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True,
                                     title="各学员级别四维指标雷达图", height=500)
            st.plotly_chart(fig_radar2, width="stretch")

        st.subheader("疲劳分组雷达图")
        df_radar_f = df_filtered.copy()
        df_radar_f["疲劳等级"] = pd.cut(df_radar_f["主观疲劳评分"], bins=[0, 3, 5, 7, 10],
                                        labels=["低疲劳(1-3)", "中疲劳(3-5)", "高疲劳(5-7)", "极高疲劳(7-10)"])
        fig_radar_f = go.Figure()
        for fg in df_radar_f["疲劳等级"].unique():
            if pd.isna(fg):
                continue
            fg_df = df_radar_f[df_radar_f["疲劳等级"] == fg]
            values = [fg_df[m].mean() for m in categories]
            fig_radar_f.add_trace(go.Scatterpolar(
                r=values + [values[0]],
                theta=categories + [categories[0]],
                fill="toself",
                name=str(fg),
                opacity=0.5
            ))
        fig_radar_f.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True,
                                  title="不同疲劳等级下的四维表现", height=500)
        st.plotly_chart(fig_radar_f, width="stretch")

    with tab3:
        st.subheader("疲劳评分热力图")
        df_heat = df_filtered.copy()
        df_heat["日期"] = pd.to_datetime(df_heat["日期"])
        df_heat["周"] = df_heat["日期"].dt.isocalendar().week.astype(int)
        df_heat["星期"] = df_heat["日期"].dt.dayofweek

        pivot_fatigue = df_heat.pivot_table(values="主观疲劳评分", index="星期", columns="周", aggfunc="mean")
        day_names = {0: "周一", 1: "周二", 2: "周三", 3: "周四", 4: "周五", 5: "周六", 6: "周日"}
        pivot_fatigue.index = [day_names.get(i, str(i)) for i in pivot_fatigue.index]

        fig_heat = go.Figure(data=go.Heatmap(
            z=pivot_fatigue.values,
            x=[f"第{w}周" for w in pivot_fatigue.columns],
            y=pivot_fatigue.index,
            colorscale="YlOrRd",
            zmin=1, zmax=10,
            text=np.round(pivot_fatigue.values, 1),
            texttemplate="%{text}",
            colorbar=dict(title="疲劳评分")
        ))
        fig_heat.update_layout(title="每周每日疲劳评分热力图", xaxis_title="周次", yaxis_title="星期", height=450)
        st.plotly_chart(fig_heat, width="stretch")

        col_h1, col_h2 = st.columns(2)
        with col_h1:
            st.markdown("**按舞种×动作类型的疲劳评分**")
            pivot_da = df_filtered.pivot_table(values="主观疲劳评分", index="舞种", columns="动作类型", aggfunc="mean")
            fig_heat2 = go.Figure(data=go.Heatmap(
                z=pivot_da.values, x=pivot_da.columns, y=pivot_da.index,
                colorscale="YlOrRd", zmin=1, zmax=10,
                text=np.round(pivot_da.values, 1), texttemplate="%{text}",
                colorbar=dict(title="疲劳评分")
            ))
            fig_heat2.update_layout(title="舞种×动作类型疲劳评分", height=400)
            st.plotly_chart(fig_heat2, width="stretch")

        with col_h2:
            st.markdown("**按学员级别×比赛阶段的完成度**")
            pivot_ls = df_filtered.pivot_table(values="动作完成度", index="学员级别", columns="比赛阶段", aggfunc="mean")
            fig_heat3 = go.Figure(data=go.Heatmap(
                z=pivot_ls.values, x=pivot_ls.columns, y=pivot_ls.index,
                colorscale="RdYlGn", zmin=30, zmax=100,
                text=np.round(pivot_ls.values, 1), texttemplate="%{text}",
                colorbar=dict(title="完成度")
            ))
            fig_heat3.update_layout(title="级别×比赛阶段完成度", height=400)
            st.plotly_chart(fig_heat3, width="stretch")

    with tab4:
        st.subheader("舞种对比分析")
        col_d1, col_d2 = st.columns(2)

        with col_d1:
            dance_metrics = df_filtered.groupby("舞种")[METRICS].mean()
            fig_bar = go.Figure()
            colors = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12"]
            for i, m in enumerate(METRICS):
                fig_bar.add_trace(go.Bar(name=m, x=dance_metrics.index, y=dance_metrics[m], marker_color=colors[i]))
            fig_bar.update_layout(barmode="group", title="各舞种四维指标对比", yaxis=dict(range=[0, 100]), height=450)
            st.plotly_chart(fig_bar, width="stretch")

        with col_d2:
            dance_summary = df_filtered.groupby("舞种").agg({
                "训练时长_分钟": "mean",
                "主观疲劳评分": "mean",
                "动作完成度": "mean"
            }).round(1)
            dance_summary.columns = ["平均时长", "平均疲劳", "平均完成度"]
            fig_bar2 = go.Figure()
            fig_bar2.add_trace(go.Bar(name="平均时长(min)", x=dance_summary.index, y=dance_summary["平均时长"],
                                      marker_color="#9b59b6"))
            fig_bar2.add_trace(go.Bar(name="平均疲劳", x=dance_summary.index, y=dance_summary["平均疲劳"],
                                      marker_color="#e67e22"))
            fig_bar2.add_trace(go.Bar(name="平均完成度", x=dance_summary.index, y=dance_summary["平均完成度"],
                                      marker_color="#1abc9c"))
            fig_bar2.update_layout(barmode="group", title="舞种综合指标对比", height=450)
            st.plotly_chart(fig_bar2, width="stretch")

        st.subheader("舞种负荷-效益象限图")
        dance_quadrant = df_filtered.groupby("舞种").agg({
            "主观疲劳评分": "mean",
            "动作完成度": "mean"
        }).reset_index()
        fig_quad = px.scatter(dance_quadrant, x="主观疲劳评分", y="动作完成度", text="舞种",
                              size_max=30, color="舞种",
                              title="负荷(疲劳)-效益(完成度)象限分析")
        mid_fat = dance_quadrant["主观疲劳评分"].mean()
        mid_comp = dance_quadrant["动作完成度"].mean()
        fig_quad.add_hline(y=mid_comp, line_dash="dash", line_color="gray", annotation_text="完成度均值")
        fig_quad.add_vline(x=mid_fat, line_dash="dash", line_color="gray", annotation_text="疲劳均值")
        fig_quad.add_annotation(x=mid_fat - 0.5, y=dance_quadrant["动作完成度"].max() + 2,
                                text="低负荷高效益", showarrow=False, font=dict(color="green"))
        fig_quad.add_annotation(x=mid_fat + 0.5, y=dance_quadrant["动作完成度"].max() + 2,
                                text="高负荷高效益", showarrow=False, font=dict(color="orange"))
        fig_quad.add_annotation(x=mid_fat - 0.5, y=dance_quadrant["动作完成度"].min() - 2,
                                text="低负荷低效益", showarrow=False, font=dict(color="gray"))
        fig_quad.add_annotation(x=mid_fat + 0.5, y=dance_quadrant["动作完成度"].min() - 2,
                                text="高负荷低效益", showarrow=False, font=dict(color="red"))
        fig_quad.update_traces(textposition="top center", marker_size=15)
        fig_quad.update_layout(height=500)
        st.plotly_chart(fig_quad, width="stretch")

    with tab5:
        st.subheader("🔍 自动识别训练规律")
        patterns = detect_patterns(df_filtered)
        if patterns:
            for p in patterns:
                css_class = f"pattern-{p['type']}"
                st.markdown(f'<div class="{css_class}"><strong>{p["title"]}</strong><br>{p["detail"]}</div>',
                            unsafe_allow_html=True)
        else:
            st.info("当前数据未识别到显著规律，请扩大筛选范围或增加数据量。")

        st.markdown("---")
        st.subheader("📅 下周排课建议")
        schedule = generate_schedule(df_filtered)
        if schedule:
            for cat, rec, detail in schedule:
                st.markdown(f'<div class="schedule-card"><strong>{cat}</strong>: {rec}<br><small>{detail}</small></div>',
                            unsafe_allow_html=True)
        else:
            st.info("数据不足，无法生成排课建议。")

        st.markdown("---")
        st.subheader("📊 关联分析矩阵")
        corr_cols = ["训练时长_分钟", "平均心率", "主观疲劳评分", "软开度", "旋转稳定度", "跳跃高度", "动作完成度"]
        if len(df_filtered) > 5:
            corr_matrix = df_filtered[corr_cols].corr()
            fig_corr = go.Figure(data=go.Heatmap(
                z=corr_matrix.values,
                x=corr_cols,
                y=corr_cols,
                colorscale="RdBu",
                zmin=-1, zmax=1,
                text=np.round(corr_matrix.values, 2),
                texttemplate="%{text}",
                colorbar=dict(title="相关系数")
            ))
            fig_corr.update_layout(title="训练指标关联矩阵", height=550)
            st.plotly_chart(fig_corr, width="stretch")

        st.markdown("---")
        st.subheader("📄 导出阶段训练报告")
        report_text = create_report(df_filtered, patterns, schedule)

        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            st.download_button(
                label="📥 导出文本报告 (.txt)",
                data=report_text,
                file_name=f"古典舞训练报告_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )
        with col_exp2:
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df_filtered.to_excel(writer, sheet_name="筛选数据", index=False)
                dance_summary_xl = df_filtered.groupby("舞种")[METRICS].mean().round(1)
                dance_summary_xl.to_excel(writer, sheet_name="舞种对比")
                if patterns:
                    pat_df = pd.DataFrame(patterns)
                    pat_df.to_excel(writer, sheet_name="识别规律", index=False)
            st.download_button(
                label="📥 导出Excel数据报告 (.xlsx)",
                data=output.getvalue(),
                file_name=f"古典舞训练数据_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )


if __name__ == "__main__":
    main()
