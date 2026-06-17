import pandas as pd


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
