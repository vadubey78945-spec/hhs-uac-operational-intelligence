"""
src/metrics.py
--------------
Computes KPIs safely without breaking graphs.
"""
import pandas as pd
import numpy as np

def compute_kpis(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Calculate KPIs with safety checks to prevent crashes from missing or non-numeric data
    if "CBP_Transfers_Out" in df.columns and "CBP_In_Custody" in df.columns:
        df["Transfer_Efficiency"] = np.where(df["CBP_In_Custody"] > 0, df["CBP_Transfers_Out"] / df["CBP_In_Custody"], np.nan)
    else:
        df["Transfer_Efficiency"] = np.nan

    if "HHS_Discharges" in df.columns and "HHS_In_Care" in df.columns:
        df["Discharge_Effectiveness"] = np.where(df["HHS_In_Care"] > 0, df["HHS_Discharges"] / df["HHS_In_Care"], np.nan)
    else:
        df["Discharge_Effectiveness"] = np.nan

    if "HHS_Discharges" in df.columns and "CBP_Apprehensions" in df.columns:
        df["Pipeline_Throughput"] = np.where(df["CBP_Apprehensions"] > 0, df["HHS_Discharges"] / df["CBP_Apprehensions"], np.nan)
    else:
        df["Pipeline_Throughput"] = np.nan

    if "CBP_Apprehensions" in df.columns and "HHS_Discharges" in df.columns:
        df["Backlog_Rate"] = df["CBP_Apprehensions"] - df["HHS_Discharges"]
    else:
        df["Backlog_Rate"] = np.nan

    if "HHS_Discharges" in df.columns:
        df["Outcome_Stability"] = df["HHS_Discharges"].rolling(window=7, min_periods=2).std().round(2)
    else:
        df["Outcome_Stability"] = np.nan

    return df

def kpi_summary(df: pd.DataFrame) -> dict:
    def safe_mean(series):
        # Calculates average ignoring NaNs so it doesn't crash
        series = series.replace([np.inf, -np.inf], np.nan).dropna()
        return float(series.mean()) if not series.empty else 0.0

    return {
        "avg_transfer_eff": safe_mean(df.get("Transfer_Efficiency", pd.Series())),
        "avg_discharge_eff": safe_mean(df.get("Discharge_Effectiveness", pd.Series())),
        "avg_throughput": safe_mean(df.get("Pipeline_Throughput", pd.Series())),
        "current_backlog": int(df["Backlog_Rate"].dropna().iloc[-1]) if "Backlog_Rate" in df.columns and not df["Backlog_Rate"].dropna().empty else 0,
        "avg_stability": safe_mean(df.get("Outcome_Stability", pd.Series())),
        "total_apprehensions": int(df["CBP_Apprehensions"].sum()) if "CBP_Apprehensions" in df.columns else 0,
        "total_discharges": int(df["HHS_Discharges"].sum()) if "HHS_Discharges" in df.columns else 0,
        "total_transfers": int(df["CBP_Transfers_Out"].sum()) if "CBP_Transfers_Out" in df.columns else 0,
        "peak_backlog": int(df["Backlog_Rate"].max()) if "Backlog_Rate" in df.columns and not df["Backlog_Rate"].dropna().empty else 0,
        "peak_backlog_date": df.loc[df["Backlog_Rate"].idxmax(), "Date"].strftime("%Y-%m-%d") if "Backlog_Rate" in df.columns and not df["Backlog_Rate"].dropna().empty else "N/A"
    }

def monthly_kpi_table(df: pd.DataFrame) -> pd.DataFrame:
    if "YearMonth" not in df.columns: return pd.DataFrame()
    monthly = (
        df.groupby("YearMonth")
        .agg(
            Transfer_Efficiency=("Transfer_Efficiency", "mean") if "Transfer_Efficiency" in df.columns else None,
            Discharge_Effectiveness=("Discharge_Effectiveness", "mean") if "Discharge_Effectiveness" in df.columns else None,
            Pipeline_Throughput=("Pipeline_Throughput", "mean") if "Pipeline_Throughput" in df.columns else None,
            Backlog_Rate=("Backlog_Rate", "mean") if "Backlog_Rate" in df.columns else None,
            Outcome_Stability=("Outcome_Stability", "mean") if "Outcome_Stability" in df.columns else None,
            Date=("Date", "first") if "Date" in df.columns else None,
        )
        .reset_index()
        .sort_values("Date")
        .round(4)
    )
    
    # Fill any missing KPI values with 0 to prevent issues in the UI, but only for the KPI columns, not the Date or YearMonth
    for col in ["Transfer_Efficiency", "Discharge_Effectiveness", "Pipeline_Throughput"]:
        if col in monthly.columns:
            monthly[col] = monthly[col].fillna(0.0)
            
    return monthly