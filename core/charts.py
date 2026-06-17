import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from .constants import METRICS
from .injury_risk import compute_injury_risk_score, risk_level


def build_trend_chart(df_filtered):
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
    return fig


def build_hr_pie_chart(df_filtered):
    hr_dist = df_filtered["心率区间"].value_counts()
    fig_hr = px.pie(values=hr_dist.values, names=hr_dist.index, title="心率区间分布",
                    color_discrete_sequence=px.colors.sequential.Reds[1:])
    return fig_hr


def build_fatigue_completion_scatter(df_filtered):
    df_filtered_c = df_filtered.copy()
    df_filtered_c["心率数值"] = df_filtered_c["心率区间"].map({
        "热身区(<110)": 1, "有氧区(110-130)": 2, "混氧区(130-150)": 3, "无氧区(150-170)": 4, "极限区(>170)": 5
    })
    scatter = px.scatter(df_filtered_c, x="主观疲劳评分", y="动作完成度",
                        color="心率区间", size="训练时长_分钟",
                        title="疲劳-完成度-心率关联散点图",
                        color_discrete_sequence=px.colors.qualitative.Set2)
    return scatter


def build_dance_radar_chart(df_filtered):
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
    return fig_radar


def build_level_radar_chart(df_filtered):
    categories = METRICS
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
    return fig_radar2


def build_fatigue_radar_chart(df_filtered):
    categories = METRICS
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
    return fig_radar_f


def build_weekly_fatigue_heatmap(df_filtered):
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
    return fig_heat


def build_dance_movement_fatigue_heatmap(df_filtered):
    pivot_da = df_filtered.pivot_table(values="主观疲劳评分", index="舞种", columns="动作类型", aggfunc="mean")
    fig_heat2 = go.Figure(data=go.Heatmap(
        z=pivot_da.values, x=pivot_da.columns, y=pivot_da.index,
        colorscale="YlOrRd", zmin=1, zmax=10,
        text=np.round(pivot_da.values, 1), texttemplate="%{text}",
        colorbar=dict(title="疲劳评分")
    ))
    fig_heat2.update_layout(title="舞种×动作类型疲劳评分", height=400)
    return fig_heat2


def build_level_stage_completion_heatmap(df_filtered):
    pivot_ls = df_filtered.pivot_table(values="动作完成度", index="学员级别", columns="比赛阶段", aggfunc="mean")
    fig_heat3 = go.Figure(data=go.Heatmap(
        z=pivot_ls.values, x=pivot_ls.columns, y=pivot_ls.index,
        colorscale="RdYlGn", zmin=30, zmax=100,
        text=np.round(pivot_ls.values, 1), texttemplate="%{text}",
        colorbar=dict(title="完成度")
    ))
    fig_heat3.update_layout(title="级别×比赛阶段完成度", height=400)
    return fig_heat3


def build_dance_metrics_bar(df_filtered):
    dance_metrics = df_filtered.groupby("舞种")[METRICS].mean()
    fig_bar = go.Figure()
    colors = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12"]
    for i, m in enumerate(METRICS):
        fig_bar.add_trace(go.Bar(name=m, x=dance_metrics.index, y=dance_metrics[m], marker_color=colors[i]))
    fig_bar.update_layout(barmode="group", title="各舞种四维指标对比", yaxis=dict(range=[0, 100]), height=450)
    return fig_bar


def build_dance_summary_bar(df_filtered):
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
    return fig_bar2


def build_dance_quadrant_chart(df_filtered):
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
    return fig_quad


def build_correlation_heatmap(df_filtered):
    corr_cols = ["训练时长_分钟", "平均心率", "主观疲劳评分", "软开度", "旋转稳定度", "跳跃高度", "动作完成度"]
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
    return fig_corr


def build_injury_risk_trend_chart(df_filtered):
    df_copy = df_filtered.copy()
    df_copy["日期"] = pd.to_datetime(df_copy["日期"])
    df_copy = df_copy.sort_values("日期")
    df_copy["风险评分"] = df_copy.apply(compute_injury_risk_score, axis=1)
    daily_risk = df_copy.groupby("日期").agg(
        风险评分均值=("风险评分", "mean"),
        风险评分最大值=("风险评分", "max"),
    ).reset_index()

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        subplot_titles=("每日伤病风险评分趋势", "风险等级分布"),
                        vertical_spacing=0.12)

    fig.add_trace(go.Scatter(
        x=daily_risk["日期"], y=daily_risk["风险评分均值"],
        name="风险均值", line=dict(color="#e74c3c", width=2),
        mode="lines+markers", marker_size=4,
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=daily_risk["日期"], y=daily_risk["风险评分最大值"],
        name="风险最大值", line=dict(color="#f39c12", width=2, dash="dash"),
        mode="lines+markers", marker_size=4,
    ), row=1, col=1)

    risk_counts = df_copy["风险评分"].apply(risk_level).value_counts()
    fig.add_trace(go.Bar(
        x=risk_counts.index, y=risk_counts.values,
        marker_color=["#2ecc71", "#f39c12", "#e74c3c"][:len(risk_counts)],
        name="风险等级分布",
    ), row=2, col=1)

    fig.update_layout(height=650, title_text="伤病风险趋势分析", showlegend=True)
    fig.update_xaxes(title_text="日期", row=1, col=1)
    fig.update_yaxes(title_text="风险评分", row=1, col=1)
    fig.update_xaxes(title_text="风险等级", row=2, col=1)
    fig.update_yaxes(title_text="记录数", row=2, col=1)
    return fig


def build_pain_location_distribution_chart(df_filtered):
    if "疼痛部位" not in df_filtered.columns:
        return go.Figure()

    pain_data = df_filtered[df_filtered["疼痛部位"] != "无"].copy()
    if pain_data.empty:
        return go.Figure()

    pain_dist = pain_data["疼痛部位"].value_counts().reset_index()
    pain_dist.columns = ["疼痛部位", "出现次数"]

    if "疼痛评分" in pain_data.columns:
        avg_pain = pain_data.groupby("疼痛部位")["疼痛评分"].mean().reset_index()
        avg_pain.columns = ["疼痛部位", "平均疼痛评分"]
        pain_dist = pain_dist.merge(avg_pain, on="疼痛部位", how="left")

    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=("疼痛部位出现频次", "各部位平均疼痛评分"),
                        specs=[[{"type": "pie"}, {"type": "bar"}]])

    fig.add_trace(go.Pie(
        labels=pain_dist["疼痛部位"],
        values=pain_dist["出现次数"],
        marker_colors=px.colors.qualitative.Set2[:len(pain_dist)],
    ), row=1, col=1)

    if "平均疼痛评分" in pain_dist.columns:
        fig.add_trace(go.Bar(
            x=pain_dist["疼痛部位"],
            y=pain_dist["平均疼痛评分"],
            marker_color="#e74c3c",
            name="平均疼痛评分",
        ), row=1, col=2)

    fig.update_layout(height=450, title_text="疼痛部位分布分析", showlegend=True)
    return fig


def build_old_injury_risk_chart(df_filtered):
    if "旧伤标记" not in df_filtered.columns:
        return go.Figure()

    old_injury = df_filtered[df_filtered["旧伤标记"] == "是"].copy()
    if old_injury.empty:
        return go.Figure()

    old_injury["风险评分"] = old_injury.apply(compute_injury_risk_score, axis=1)
    old_injury["风险等级"] = old_injury["风险评分"].apply(risk_level)

    risk_by_level = old_injury["风险等级"].value_counts()

    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=("旧伤学员风险等级分布", "旧伤学员风险评分分布"),
                        specs=[[{"type": "pie"}, {"type": "histogram"}]])

    colors_map = {"低风险": "#2ecc71", "中风险": "#f39c12", "高风险": "#e74c3c"}
    fig.add_trace(go.Pie(
        labels=risk_by_level.index,
        values=risk_by_level.values,
        marker_colors=[colors_map.get(l, "#95a5a6") for l in risk_by_level.index],
    ), row=1, col=1)

    fig.add_trace(go.Histogram(
        x=old_injury["风险评分"],
        nbinsx=15,
        marker_color="#e67e22",
        name="风险评分分布",
    ), row=1, col=2)

    fig.update_layout(height=450, title_text="旧伤复发风险分析", showlegend=True)
    fig.update_xaxes(title_text="风险评分", row=1, col=2)
    fig.update_yaxes(title_text="人数", row=1, col=2)
    return fig


def build_recovery_tracking_chart(df_filtered):
    if "恢复状态" not in df_filtered.columns:
        return go.Figure()

    recovery_dist = df_filtered["恢复状态"].value_counts()

    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=("恢复状态分布", "恢复训练类型分布"),
                        specs=[[{"type": "pie"}, {"type": "bar"}]])

    recovery_colors = {"完全恢复": "#2ecc71", "恢复中": "#f39c12", "未恢复": "#e74c3c"}
    fig.add_trace(go.Pie(
        labels=recovery_dist.index,
        values=recovery_dist.values,
        marker_colors=[recovery_colors.get(l, "#95a5a6") for l in recovery_dist.index],
    ), row=1, col=1)

    if "恢复训练类型" in df_filtered.columns:
        training_dist = df_filtered[df_filtered["恢复状态"] != "完全恢复"]["恢复训练类型"].value_counts()
        fig.add_trace(go.Bar(
            x=training_dist.index,
            y=training_dist.values,
            marker_color="#3498db",
            name="恢复训练类型",
        ), row=1, col=2)

    fig.update_layout(height=450, title_text="恢复状态跟踪", showlegend=True)
    return fig
