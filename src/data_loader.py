"""
src/data_loader.py
------------------
Responsible for reading the raw CSV and renaming columns to
project-standard names. Supports both a local file path and
an in-memory uploaded file (Streamlit UploadedFile).
"""

import pandas as pd
import io
from typing import Union

# ── Column rename map (raw CSV → project standard) ────────────────────────
COLUMN_MAP: dict[str, str] = {
    "Children apprehended and placed in CBP custody*": "CBP_Apprehensions",
    "Children in CBP custody":                         "CBP_In_Custody",
    "Children transferred out of CBP custody":         "CBP_Transfers_Out",
    "Children in HHS Care":                            "HHS_In_Care",
    "Children discharged from HHS Care":               "HHS_Discharges",
}

REQUIRED_COLUMNS: list[str] = list(COLUMN_MAP.keys()) + ["Date"]


def load_data(filepath: str) -> pd.DataFrame:
    """
    Load dataset from a local file path.

    Parameters
    ----------
    filepath : str
        Absolute or relative path to the CSV file.

    Returns
    -------
    pd.DataFrame
        Raw dataframe with columns renamed to project standard.
    """
    df = pd.read_csv(filepath, encoding="utf-8")
    return _rename_and_validate(df)


def load_data_from_upload(uploaded_file) -> pd.DataFrame:
    """
    Load dataset from a Streamlit UploadedFile object.

    Parameters
    ----------
    uploaded_file : streamlit.runtime.uploaded_file_manager.UploadedFile

    Returns
    -------
    pd.DataFrame
        Raw dataframe with columns renamed to project standard.
    """
    content = uploaded_file.read()
    df = pd.read_csv(io.BytesIO(content), encoding="utf-8")
    return _rename_and_validate(df)


def _rename_and_validate(df: pd.DataFrame) -> pd.DataFrame:
    """Internal helper: rename columns and check required fields exist."""
    df.columns = df.columns.str.strip()
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"Dataset is missing expected columns: {missing}\n"
            f"Found columns: {list(df.columns)}"
        )
    df = df.rename(columns=COLUMN_MAP)
    return df
