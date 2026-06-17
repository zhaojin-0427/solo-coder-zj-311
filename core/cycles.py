import pandas as pd


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
