"""
Hospital records cleaning pipeline (Colab + Drive friendly)

- Mounts Google Drive (optional; works best in Colab)
- Finds the first CSV in data/raw
- Loads safely (fallback encoding)
- Cleans: columns, empty-like -> NaN, duplicates, trims text
- Auto-cleans: gender, age, date-like columns, phone columns, numeric-like text
- Caps outliers (IQR) for numeric columns (excluding id columns)
- Imputes missing values (numeric=median, text="unknown")
- Saves cleaned CSV + missing reports
"""

import os
import re
from pathlib import Path

import numpy as np
import pandas as pd


# ---------------------------
# Optional: Google Drive mount (Colab)
# ---------------------------
def try_mount_drive():
    try:
        from google.colab import drive  # type: ignore
        drive.mount("/content/drive")
        print("✅ Google Drive mounted at /content/drive")
    except Exception as e:
        print("ℹ️ Drive mount skipped (not running in Colab or mount failed).")
        print("   Details:", e)


# ---------------------------
# Helpers
# ---------------------------
def missing_report(dataframe: pd.DataFrame) -> pd.DataFrame:
    miss = dataframe.isna().sum()
    pct = (miss / len(dataframe)) * 100
    rep = pd.DataFrame({"missing": miss, "pct": pct})
    return rep.sort_values(by="missing", ascending=False)


def clean_column_name(col: str) -> str:
    col = str(col).strip().lower()
    col = re.sub(r"\s+", "_", col)
    col = re.sub(r"[^a-z0-9_]", "", col)
    return col


def find_cols(cols, keywords):
    return [c for c in cols if any(k in c for k in keywords)]


def clean_phone(x):
    if pd.isna(x):
        return np.nan
    digits = re.sub(r"\D", "", str(x))
    if len(digits) < 10 or len(digits) > 15:
        return np.nan
    return digits


def cap_outliers_iqr(series: pd.Series) -> pd.Series:
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


# ---------------------------
# Main
# ---------------------------
def main():
    # If you're in Colab, this helps access Drive paths.
    try_mount_drive()

    # Define the actual project root directory
    PROJECT_ROOT = Path("/content/drive/MyDrive/hospital-records-cleaning/")

    # Define the raw data directory within the project root
    RAW_DIR = PROJECT_ROOT / "data" / "raw"

    print("PROJECT_ROOT exists?", PROJECT_ROOT.exists())
    print("RAW_DIR exists?", RAW_DIR.exists())

    print("\nPROJECT_ROOT:")
    print(PROJECT_ROOT)

    print("\nRAW_DIR:")
    print(RAW_DIR)

    print("\nFiles inside data/raw:")
    if RAW_DIR.exists() and RAW_DIR.is_dir():
        for p in RAW_DIR.glob("*"):
            print("-", p.name)
    else:
        raise FileNotFoundError(f"Directory {RAW_DIR} does not exist or is not a directory.")

    csv_files = list(RAW_DIR.glob("*.csv"))
    if len(csv_files) == 0:
        raise FileNotFoundError(f"No CSV found in: {RAW_DIR}")

    RAW_PATH = csv_files[0]
    print("✅ Using raw file:", RAW_PATH)

    # LOAD CSV SAFELY
    try:
        df_raw = pd.read_csv(RAW_PATH)
    except UnicodeDecodeError:
        df_raw = pd.read_csv(RAW_PATH, encoding="latin1")

    df = df_raw.copy()
    print("✅ Loaded shape:", df.shape)

    # Change working directory to project root (optional)
    try:
        os.chdir(PROJECT_ROOT)
        print("✅ Current working directory:", os.getcwd())
    except Exception as e:
        print("ℹ️ Could not chdir to PROJECT_ROOT:", e)

    print("\nColumns (original):")
    print(df.columns.tolist())

    # Missing report BEFORE (on raw df)
    before_missing = missing_report(df)

    # ---------------------------
    # Standardize column names
    # ---------------------------
    df.columns = [clean_column_name(c) for c in df.columns]
    print("\n✅ Cleaned columns:")
    print(df.columns.tolist())

    # ---------------------------
    # Replace “empty-like” values with real NaN
    # ---------------------------
    EMPTY_LIKE = ["n/a", "na", "none", "null", "unknown", "?", "??", "-", "", " "]
    df = df.replace(EMPTY_LIKE, np.nan)
    print("\n✅ Converted empty-like values to NaN")

    # ---------------------------
    # Remove duplicates
    # ---------------------------
    dup_count = df.duplicated().sum()
    df = df.drop_duplicates().reset_index(drop=True)
    print("\n✅ Duplicate rows removed:", dup_count)
    print("New shape:", df.shape)

    # ---------------------------
    # Trim text columns
    # ---------------------------
    text_cols = df.select_dtypes(include=["object"]).columns.tolist()
    for col in text_cols:
        df[col] = df[col].astype("string").str.strip()
    print("\n✅ Trimmed text columns:", len(text_cols))

    # ---------------------------
    # Auto-detect important columns (prints only)
    # ---------------------------
    cols = df.columns.tolist()
    print("\nAuto-detected columns:")
    print("Possible ID columns:", find_cols(cols, ["id"]))
    print("Possible name columns:", find_cols(cols, ["name", "patient"]))
    print("Possible gender columns:", find_cols(cols, ["gender", "sex"]))
    print("Possible age columns:", find_cols(cols, ["age"]))
    print("Possible date columns:", find_cols(cols, ["date", "admission", "discharge", "dob"]))
    print("Possible phone columns:", find_cols(cols, ["phone", "mobile", "contact"]))
    print("Possible cost/bill columns:", find_cols(cols, ["bill", "cost", "charge", "amount", "price", "payment"]))

    # ---------------------------
    # Clean gender
    # ---------------------------
    gender_col = None
    for cand in ["gender", "sex"]:
        if cand in df.columns:
            gender_col = cand
            break

    if gender_col is None:
        print("\nℹ️ No gender/sex column found — skipping.")
    else:
        gender_map = {
            "m": "male",
            "male": "male",
            "man": "male",
            "f": "female",
            "female": "female",
            "woman": "female",
        }
        df[gender_col] = df[gender_col].astype("string").str.lower().map(gender_map)
        print(f"\n✅ Cleaned {gender_col}")
        print(df[gender_col].value_counts(dropna=False))

    # ---------------------------
    # Clean age (only if exists)
    # ---------------------------
    if "age" not in df.columns:
        print("\nℹ️ No age column found — skipping.")
    else:
        df["age"] = pd.to_numeric(df["age"], errors="coerce")
        df.loc[(df["age"] < 0) | (df["age"] > 120), "age"] = np.nan
        print("\n✅ Cleaned age")
        print(df["age"].describe())

    # ---------------------------
    # Parse date columns automatically
    # ---------------------------
    date_cols = [c for c in df.columns if any(k in c for k in ["date", "admission", "discharge", "dob"])]
    print("\nDetected date-like columns:", date_cols)

    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    print("✅ Parsed dates (bad dates become NaT)")

    # ---------------------------
    # Clean phone/contact columns (digits only)
    # ---------------------------
    phone_cols = [c for c in df.columns if any(k in c for k in ["phone", "mobile", "contact"])]
    if not phone_cols:
        print("\nℹ️ No phone-like columns found — skipping.")
    else:
        for c in phone_cols:
            df[c] = df[c].apply(clean_phone)
        print("\n✅ Cleaned phone columns:", phone_cols)

    # ---------------------------
    # Convert numeric-looking text columns safely
    # ---------------------------
    for col in df.columns:
        if df[col].dtype == "object" or str(df[col].dtype) == "string":
            converted = pd.to_numeric(df[col], errors="coerce")
            if converted.notna().mean() > 0.70:
                df[col] = converted
    print("\n✅ Converted numeric-like text columns where possible")

    # ---------------------------
    # Cap outliers (IQR) for numeric columns (excluding IDs)
    # ---------------------------
    num_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
    for col in num_cols:
        if "id" not in col:
            df[col] = cap_outliers_iqr(df[col])

    print("\n✅ Capped outliers for numeric columns (excluding id columns)")

    # ---------------------------
    # Impute missing values (safe defaults)
    # ---------------------------
    for col in df.select_dtypes(include=["int64", "float64"]).columns:
        df[col] = df[col].fillna(df[col].median())

    for col in df.select_dtypes(include=["string", "object"]).columns:
        df[col] = df[col].fillna("unknown")

    print("\n✅ Imputation done (numeric=median, text=unknown)")

    # Missing report AFTER
    after_missing = missing_report(df)

    # ---------------------------
    # Save cleaned CSV + reports
    # ---------------------------
    CLEAN_DIR = PROJECT_ROOT / "data" / "cleaned"
    REPORTS_DIR = PROJECT_ROOT / "reports"

    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    print("\nTop missing BEFORE:")
    print(before_missing.head(10))

    print("\nTop missing AFTER:")
    print(after_missing.head(10))

    before_missing.to_csv(REPORTS_DIR / "missing_report_before.csv")
    after_missing.to_csv(REPORTS_DIR / "missing_report_after.csv")

    CLEAN_PATH = CLEAN_DIR / "hospital_records_cleaned.csv"
    df.to_csv(CLEAN_PATH, index=False)

    print("\n✅ Saved cleaned CSV to:", CLEAN_PATH)
    print("✅ Saved reports to:", REPORTS_DIR)


if __name__ == "__main__":
    main()
