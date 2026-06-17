import pandas as pd


def add_cycle_column(df):
    if "训练周期" not in df.columns:
        df = df.copy()
        df["日期_dt"] = pd.to_datetime(df["日期"])
        df = df.sort_values("日期_dt").reset_index(drop=True)
        unique_dates = sorted(df["日期_dt"].unique())
        n = len(unique_dates)
        cycle_size = max(1, n // 4)
        date_to_cycle = {}
        for idx, d in enumerate(unique_dates):
            ci = min(idx // cycle_size, 3)
            date_to_cycle[d] = f"第{ci+1}周期"
        df["训练周期"] = df["日期_dt"].map(date_to_cycle)
        df = df.drop(columns=["日期_dt"])
    return df
