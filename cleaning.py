import re
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd


# -------------------------
# Utilities
# -------------------------
def clean_column_name(col: str) -> str:
    """Standardize column names to snake_case."""
    col = str(col).strip().lower()
    col = re.sub(r"\s+", "_", col)
    col = re.sub(r"[^a-z0-9_]", "", col)
    return col


def missing_report(df: pd.DataFrame) -> pd.DataFrame:
    """Create missing-value report (count + %)."""
    miss = df.isna().sum()
    pct = (miss / len(df)) * 100
    rep = pd.DataFrame({"missing_count": miss, "missing_pct": pct.round(2)})
    return rep.sort_values("missing_pct", ascending=False)


def clean_phone(x):
    """Keep digits only, validate length, else NaN."""
    if pd.isna(x):
        return np.nan
    digits = re.sub(r"\D", "", str(x))
    if len(digits) < 10 or len(digits) > 15:
        return np.nan
    return digits


def cap_outliers_iqr(series: pd.Series) -> pd.Series:
    """Cap outliers using the IQR method."""
    if series.dropna().shape[0] < 5:
        return series

    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1

    if iqr == 0 or pd.isna(iqr):
        return series

    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return series.clip(lower, upper)


def find_first_existing(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    """Return the first column name that exists in df from a candidate list."""
    for c in candidates:
        if c in df.columns:
            return c
    return None


# -------------------------
# Load / Save
# -------------------------
def load_csv_safe(path) -> pd.DataFrame:
    """Load CSV with encoding fallback (prevents common Kaggle decode errors)."""
    try:
        return pd.read_csv(path)
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="latin1")


# -------------------------
# Main cleaning pipeline
# -------------------------
def clean_hospital_records(df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    End-to-end cleaning.
    Returns:
      df_clean, missing_before, missing_after
    """
    df = df_raw.copy()

    # Report before
    missing_before = missing_report(df)

    # 1) Clean column names
    df.columns = [clean_column_name(c) for c in df.columns]

    # 2) Replace empty-like values with NaN
    empty_like = ["n/a", "na", "none", "null", "unknown", "?", "??", "-", "", " "]
    df = df.replace(empty_like, np.nan)

    # 3) Drop duplicate rows
    df = df.drop_duplicates().reset_index(drop=True)

    # 4) Trim text columns
    text_cols = df.select_dtypes(include=["object"]).columns.tolist()
    for col in text_cols:
        df[col] = df[col].astype("string").str.strip()

    # 5) Gender/sex cleaning (only if exists)
    gender_col = find_first_existing(df, ["gender", "sex"])
    if gender_col is not None:
        gender_map = {
            "m": "male", "male": "male", "man": "male",
            "f": "female", "female": "female", "woman": "female"
        }
        df[gender_col] = df[gender_col].astype("string").str.lower().map(gender_map)

    # 6) Age cleaning (only if exists)
    if "age" in df.columns:
        df["age"] = pd.to_numeric(df["age"], errors="coerce")
        df.loc[(df["age"] < 0) | (df["age"] > 120), "age"] = np.nan

    # 7) Parse date-like columns (auto detect)
    date_cols = [c for c in df.columns if any(k in c for k in ["date", "admission", "discharge", "dob"])]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    # Admission/Discharge logical check (optional if both exist)
    if "admission_date" in df.columns and "discharge_date" in df.columns:
        bad = df["discharge_date"] < df["admission_date"]
        df.loc[bad, ["admission_date", "discharge_date"]] = pd.NaT

    # 8) Phone cleaning (auto detect)
    phone_cols = [c for c in df.columns if any(k in c for k in ["phone", "mobile", "contact"])]
    for c in phone_cols:
        df[c] = df[c].apply(clean_phone)

    # 9) Convert numeric-looking text columns safely
    for col in df.columns:
        if df[col].dtype == "object" or str(df[col].dtype) == "string":
            converted = pd.to_numeric(df[col], errors="coerce")
            if converted.notna().mean() > 0.70:
                df[col] = converted

    # 10) Cap outliers for numeric columns (skip id columns)
    num_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
    for col in num_cols:
        if "id" not in col:
            df[col] = cap_outliers_iqr(df[col])

    # 11) Imputation
    # Numeric -> median
    for col in df.select_dtypes(include=["int64", "float64"]).columns:
        df[col] = df[col].fillna(df[col].median())

    # Text -> "unknown"
    for col in df.select_dtypes(include=["string", "object"]).columns:
        df[col] = df[col].fillna("unknown")

    # Report after
    missing_after = missing_report(df)

    return df, missing_before, missing_after
