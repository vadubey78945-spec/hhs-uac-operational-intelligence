"""
src/bottleneck.py
-----------------
Automatic bottleneck detection across the care transition pipeline.
"""

import pandas as pd
import numpy as np

SUSTAINED_THRESHOLD = 3
ALERT_PERCENTILE    = 90


def detect_bottlenecks(df: pd.DataFrame,
                       sustained_days: int = SUSTAINED_THRESHOLD) -> pd.DataFrame:
    """Append bottleneck flag columns to the dataframe."""
    df = df.copy()

    df["CBP_Bottleneck"] = (
        df["CBP_Apprehensions"].fillna(0) > df["CBP_Transfers_Out"].fillna(0)
    )
    df["HHS_Bottleneck"] = (
        df["HHS_In_Care"].fillna(0) > df["HHS_Discharges"].fillna(0)
    )
    df["Any_Bottleneck"] = df["CBP_Bottleneck"] | df["HHS_Bottleneck"]

    df["CBP_Sustained"] = _sustained_flag(df["CBP_Bottleneck"], sustained_days)
    df["HHS_Sustained"] = _sustained_flag(df["HHS_Bottleneck"], sustained_days)

    backlog_pos = df["Backlog_Rate"].clip(lower=0)
    max_bl = backlog_pos.max()
    df["Severity_Score"] = (
        (backlog_pos / max_bl * 10) if max_bl > 0 else 0.0
    ).round(2)

    threshold = df["Backlog_Rate"].quantile(ALERT_PERCENTILE / 100)
    df["Critical_Alert"] = df["Backlog_Rate"] >= threshold

    return df


def _sustained_flag(series: pd.Series, threshold: int) -> pd.Series:
    result = [False] * len(series)
    count = 0
    for i, val in enumerate(series):
        if val:
            count += 1
            result[i] = count > threshold
        else:
            count = 0
    return pd.Series(result, index=series.index, dtype=bool)


def get_bottleneck_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Return a clean summary table of all bottleneck periods."""
    cols = [
        "Date","CBP_Apprehensions","CBP_Transfers_Out","HHS_In_Care",
        "HHS_Discharges","Backlog_Rate","CBP_Bottleneck","HHS_Bottleneck",
        "CBP_Sustained","HHS_Sustained","Severity_Score","Critical_Alert",
    ]
    return (
        df.loc[df["Any_Bottleneck"], cols]
        .sort_values("Severity_Score", ascending=False)
        .reset_index(drop=True)
    )


def bottleneck_stats(df: pd.DataFrame) -> dict:
    """High-level bottleneck statistics for the insights panel."""
    n_total = len(df)
    n_cbp   = int(df["CBP_Bottleneck"].sum())
    n_hhs   = int(df["HHS_Bottleneck"].sum())
    n_sus   = int((df["CBP_Sustained"] | df["HHS_Sustained"]).sum())
    n_crit  = int(df["Critical_Alert"].sum())
    return {
        "pct_cbp_bottleneck":  round(n_cbp / n_total * 100, 1),
        "pct_hhs_bottleneck":  round(n_hhs / n_total * 100, 1),
        "n_sustained_periods": n_sus,
        "n_critical_alerts":   n_crit,
        "worst_severity":      round(df["Severity_Score"].max(), 2),
        "avg_severity":        round(df["Severity_Score"].mean(), 2),
    }
