"""
src/preprocessing.py
---------------------
Cleans and prepares the raw DataFrame for analysis.
"""
import pandas as pd

NUMERIC_COLS = [
    "CBP_Apprehensions",
    "CBP_In_Custody",
    "CBP_Transfers_Out",
    "HHS_In_Care",
    "HHS_Discharges",
]

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 1. SMART COLUMN RENAMING (Handles variations in column names by looking for keywords, not exact matches)
    df.columns = df.columns.str.strip()
    mapping = {}
    for col in df.columns:
        c_low = str(col).lower()
        if "date" in c_low: 
            mapping[col] = "Date"
        elif "discharged" in c_low: 
            mapping[col] = "HHS_Discharges"
        elif "hhs care" in c_low: 
            mapping[col] = "HHS_In_Care"
        elif "transferred" in c_low: 
            mapping[col] = "CBP_Transfers_Out"
        elif "apprehended" in c_low: 
            mapping[col] = "CBP_Apprehensions"
        elif "cbp custody" in c_low and "apprehended" not in c_low: 
            mapping[col] = "CBP_In_Custody"
    df = df.rename(columns=mapping)

    # 2. PARSE DATE SAFELY (Handles different date formats and invalid entries without crashing)
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"])

    # 3. CLEAN NUMERIC COLUMNS SAFELY (Handles non-numeric characters, converts to numeric, and prevents crashes from bad data)
    for col in NUMERIC_COLS:
        if col in df.columns:
            if df[col].dtype == object:
                # Sirf numbers aur decimals allow karega, baki sab (jaise commas) hata dega
                df[col] = df[col].astype(str).str.replace(r'[^\d.-]', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 4. SORT AND FILL
    if "Date" in df.columns:
        df = df.sort_values("Date").reset_index(drop=True)

    existing_cols = [c for c in NUMERIC_COLS if c in df.columns]
    if existing_cols:
        df[existing_cols] = df[existing_cols].ffill(limit=3)

    # 5. TIME FEATURES
    if "Date" in df.columns:
        df["Year"]      = df["Date"].dt.year
        df["Month"]     = df["Date"].dt.month
        df["MonthName"] = df["Date"].dt.strftime("%b %Y")
        df["YearMonth"] = df["Date"].dt.to_period("M").astype(str)
        df["DayOfWeek"] = df["Date"].dt.day_name()
        df["Week"]      = df["Date"].dt.isocalendar().week.astype(int)

    return df


def filter_by_date(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    if "Date" not in df.columns: return df
    mask = (df["Date"] >= pd.Timestamp(start)) & (df["Date"] <= pd.Timestamp(end))
    return df.loc[mask].reset_index(drop=True)


def get_monthly_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    if "YearMonth" not in df.columns: return pd.DataFrame()
    monthly = (
        df.groupby("YearMonth")
        .agg(
            CBP_Apprehensions=("CBP_Apprehensions", "sum") if "CBP_Apprehensions" in df.columns else None,
            CBP_In_Custody=("CBP_In_Custody", "mean") if "CBP_In_Custody" in df.columns else None,
            CBP_Transfers_Out=("CBP_Transfers_Out", "sum") if "CBP_Transfers_Out" in df.columns else None,
            HHS_In_Care=("HHS_In_Care", "mean") if "HHS_In_Care" in df.columns else None,
            HHS_Discharges=("HHS_Discharges", "sum") if "HHS_Discharges" in df.columns else None,
            Date=("Date", "first") if "Date" in df.columns else None,
        )
        .reset_index()
        .sort_values("Date")
    )
    return monthly