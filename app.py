import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

from core import (
    load_data,
    apply_filters,
    detect_patterns,
    generate_schedule,
    create_report,
    charts,
    METRICS,
    OPTIONAL_INJURY_COLUMNS,
    has_injury_data,
    missing_injury_columns,
    compute_injury_risk_score,
    risk_level,
    detect_injury_risk_patterns,
    build_old_injury_risk_list,
    build_recovery_tracking_table,
)
from core.data_loader import DataValidationError

st.set_page_config(page_title="古典舞训练负荷与动作完成度分析台", layout="wide", page_icon="🩰")


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
    .pattern-danger {background:#f8d7da; border-left:4px solid #dc3545; padding:0.8rem 1rem; border-radius:6px; margin:0.3rem 0;}
    .schedule-card {background:#f8f9fa; border-radius:10px; padding:1rem; margin:0.3rem 0; border:1px solid #e9ecef;}
    .missing-field-notice {background:#fff3cd; border-left:4px solid #ffc107; padding:1rem 1.2rem; border-radius:8px; margin:1rem 0;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-title">🩰 古典舞训练负荷与动作完成度分析台</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Training Load & Movement Completion Analysis for Chinese Classical Dance</div>', unsafe_allow_html=True)

    with st.sidebar:
        st.header("📁 数据导入")
        uploaded = st.file_uploader("上传训练记录 CSV", type=["csv"])
        use_sample = st.checkbox("使用示例数据", value=True)

    df = None
    load_error = None
    try:
        df = load_data(uploaded, use_sample)
    except DataValidationError as e:
        load_error = str(e)

    if load_error:
        st.error(f"❌ CSV 文件格式错误：\n\n{load_error}")
        st.markdown("### 📋 CSV格式要求")
        st.markdown("""
        所需列：`日期, 舞种, 动作类型, 学员级别, 指导老师, 比赛阶段, 训练时长_分钟, 心率区间, 平均心率, 主观疲劳评分, 软开度, 旋转稳定度, 跳跃高度, 动作完成度`

        - **舞种**: 身韵、水袖、剑舞、扇舞、把杆、毯技
        - **动作类型**: 软开度、旋转、跳跃、翻身、控制、步法
        - **学员级别**: 初级、中级、高级、表演级
        - **比赛阶段**: 日常训练、赛前集训、比赛周、赛后恢复
        - **心率区间**: 热身区/有氧区/混氧区/无氧区/极限区
        - **主观疲劳评分**: 1-10分

        可选伤病字段：`疼痛部位, 疼痛评分, 旧伤标记, 恢复状态, 睡眠时长_小时, 恢复训练类型`
        """)
        return

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

        可选伤病字段：`疼痛部位, 疼痛评分, 旧伤标记, 恢复状态, 睡眠时长_小时, 恢复训练类型`
        """)
        return

    injury_available = has_injury_data(df)
    missing_cols = missing_injury_columns(df) if not injury_available else []

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

    tab_names = ["📊 训练负荷趋势", "🕸️ 动作完成度雷达", "🔥 疲劳热力图", "🎭 舞种对比", "📋 规律识别与排课建议", "🏥 伤病风险预警与恢复跟踪"]
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(tab_names)

    with tab1:
        st.subheader("训练负荷趋势分析")
        fig = charts.build_trend_chart(df_filtered)
        st.plotly_chart(fig, width="stretch")

        st.subheader("心率区间分布与负荷关系")
        col_a, col_b = st.columns(2)
        with col_a:
            fig_hr = charts.build_hr_pie_chart(df_filtered)
            st.plotly_chart(fig_hr, width="stretch")
        with col_b:
            scatter = charts.build_fatigue_completion_scatter(df_filtered)
            st.plotly_chart(scatter, width="stretch")

    with tab2:
        st.subheader("动作完成度雷达图")
        col_r1, col_r2 = st.columns(2)

        with col_r1:
            st.markdown("**按舞种对比**")
            fig_radar = charts.build_dance_radar_chart(df_filtered)
            st.plotly_chart(fig_radar, width="stretch")

        with col_r2:
            st.markdown("**按学员级别对比**")
            fig_radar2 = charts.build_level_radar_chart(df_filtered)
            st.plotly_chart(fig_radar2, width="stretch")

        st.subheader("疲劳分组雷达图")
        fig_radar_f = charts.build_fatigue_radar_chart(df_filtered)
        st.plotly_chart(fig_radar_f, width="stretch")

    with tab3:
        st.subheader("疲劳评分热力图")
        fig_heat = charts.build_weekly_fatigue_heatmap(df_filtered)
        st.plotly_chart(fig_heat, width="stretch")

        col_h1, col_h2 = st.columns(2)
        with col_h1:
            st.markdown("**按舞种×动作类型的疲劳评分**")
            fig_heat2 = charts.build_dance_movement_fatigue_heatmap(df_filtered)
            st.plotly_chart(fig_heat2, width="stretch")

        with col_h2:
            st.markdown("**按学员级别×比赛阶段的完成度**")
            fig_heat3 = charts.build_level_stage_completion_heatmap(df_filtered)
            st.plotly_chart(fig_heat3, width="stretch")

    with tab4:
        st.subheader("舞种对比分析")
        col_d1, col_d2 = st.columns(2)

        with col_d1:
            fig_bar = charts.build_dance_metrics_bar(df_filtered)
            st.plotly_chart(fig_bar, width="stretch")

        with col_d2:
            fig_bar2 = charts.build_dance_summary_bar(df_filtered)
            st.plotly_chart(fig_bar2, width="stretch")

        st.subheader("舞种负荷-效益象限图")
        fig_quad = charts.build_dance_quadrant_chart(df_filtered)
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
        if len(df_filtered) > 5:
            fig_corr = charts.build_correlation_heatmap(df_filtered)
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
                if has_injury_data(df_filtered):
                    injury_risk_df = df_filtered.copy()
                    injury_risk_df["风险评分"] = injury_risk_df.apply(compute_injury_risk_score, axis=1)
                    injury_risk_df["风险等级"] = injury_risk_df["风险评分"].apply(risk_level)
                    injury_cols = ["日期", "舞种", "动作类型", "主观疲劳评分", "动作完成度", "风险评分", "风险等级"]
                    optional_injury_cols = [c for c in ["疼痛部位", "疼痛评分", "旧伤标记", "恢复状态", "睡眠时长_小时"] if c in injury_risk_df.columns]
                    all_injury_cols = injury_cols[:5] + optional_injury_cols + injury_cols[5:]
                    existing_cols = [c for c in all_injury_cols if c in injury_risk_df.columns]
                    injury_risk_df[existing_cols].to_excel(writer, sheet_name="伤病风险", index=False)
                    old_injury_list = build_old_injury_risk_list(df_filtered)
                    if not old_injury_list.empty:
                        old_injury_list.to_excel(writer, sheet_name="旧伤复发风险", index=False)
                    recovery_df = build_recovery_tracking_table(df_filtered)
                    if not recovery_df.empty:
                        recovery_df.to_excel(writer, sheet_name="恢复状态跟踪", index=False)
            st.download_button(
                label="📥 导出Excel数据报告 (.xlsx)",
                data=output.getvalue(),
                file_name=f"古典舞训练数据_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    with tab6:
        if not has_injury_data(df_filtered):
            st.markdown(
                '<div class="missing-field-notice">'
                '<strong>⚠️ 当前数据不包含伤病相关字段</strong><br><br>'
                '伤病风险预警与恢复跟踪功能需要 CSV 中包含以下可选字段：<br>'
                '• <code>疼痛部位</code>：如 腰部、膝盖、踝关节 等<br>'
                '• <code>疼痛评分</code>：0-10 分<br>'
                '• <code>旧伤标记</code>：是/否<br>'
                '• <code>恢复状态</code>：完全恢复/恢复中/未恢复<br>'
                '• <code>睡眠时长_小时</code>：如 7.5<br>'
                '• <code>恢复训练类型</code>：如 低强度拉伸、水中训练 等<br><br>'
                '请在 CSV 中添加以上字段后重新上传，即可使用伤病风险分析功能。'
                '</div>',
                unsafe_allow_html=True
            )
            st.info("现有分析功能（训练负荷趋势、动作完成度雷达、疲劳热力图、舞种对比、规律识别与排课建议）仍可正常使用，请查看其他 Tab。")
        else:
            missing = missing_injury_columns(df_filtered)
            if missing:
                st.markdown(
                    f'<div class="missing-field-notice">'
                    f'<strong>⚠️ 部分伤病字段缺失</strong><br>'
                    f'当前数据缺少以下字段：{", ".join(f"<code>{c}</code>" for c in missing)}<br>'
                    f'部分分析图表可能无法完整展示，建议补充缺失字段以获得完整分析。'
                    f'</div>',
                    unsafe_allow_html=True
                )

            st.subheader("📊 伤病风险趋势图")
            fig_injury_trend = charts.build_injury_risk_trend_chart(df_filtered)
            st.plotly_chart(fig_injury_trend, width="stretch")

            st.markdown("---")
            st.subheader("🦴 疼痛部位分布图")
            if "疼痛部位" in df_filtered.columns:
                fig_pain = charts.build_pain_location_distribution_chart(df_filtered)
                if fig_pain.data:
                    st.plotly_chart(fig_pain, width="stretch")
                else:
                    st.info("当前数据中无疼痛记录。")
            else:
                st.warning("数据中缺少「疼痛部位」字段，无法生成疼痛部位分布图。")

            st.markdown("---")
            st.subheader("⚡ 旧伤复发风险列表")
            if "旧伤标记" in df_filtered.columns:
                fig_old_injury = charts.build_old_injury_risk_chart(df_filtered)
                if fig_old_injury.data:
                    st.plotly_chart(fig_old_injury, width="stretch")

                old_injury_list = build_old_injury_risk_list(df_filtered)
                if not old_injury_list.empty:
                    st.markdown("**旧伤学员复发风险详情**")
                    st.dataframe(old_injury_list, use_container_width=True)
                else:
                    st.info("当前数据中无旧伤标记记录。")
            else:
                st.warning("数据中缺少「旧伤标记」字段，无法生成旧伤复发风险分析。")

            st.markdown("---")
            st.subheader("🔄 恢复状态跟踪表")
            if "恢复状态" in df_filtered.columns:
                fig_recovery = charts.build_recovery_tracking_chart(df_filtered)
                if fig_recovery.data:
                    st.plotly_chart(fig_recovery, width="stretch")

                recovery_table = build_recovery_tracking_table(df_filtered)
                if not recovery_table.empty:
                    st.markdown("**恢复状态跟踪详情**")
                    st.dataframe(recovery_table, use_container_width=True)
                else:
                    st.info("无恢复状态数据。")
            else:
                st.warning("数据中缺少「恢复状态」字段，无法生成恢复状态跟踪。")

            st.markdown("---")
            st.subheader("🚨 伤病风险模式识别")
            injury_patterns = detect_injury_risk_patterns(df_filtered)
            if injury_patterns:
                for p in injury_patterns:
                    css_class = f"pattern-{p['type']}"
                    st.markdown(f'<div class="{css_class}"><strong>{p["title"]}</strong><br>{p["detail"]}</div>',
                                unsafe_allow_html=True)
            else:
                st.info("当前数据未识别到显著伤病风险模式。")


if __name__ == "__main__":
    main()
