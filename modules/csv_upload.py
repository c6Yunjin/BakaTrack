# CSV upload with checks. If ANY check fails, nothing is saved.
import pandas as pd
from database.db import create_dataset_with_records, get_dataset_id

REQUIRED_COLUMNS = ["date", "head_count", "total_kilos", "price_per_kilo"]


def validate_csv(file_path):
    """Return (clean_dataframe, errors). If errors is not empty, the file is rejected."""
    errors = []

    try:
        df = pd.read_csv(file_path, dtype=str)   # read everything as text first
    except Exception as e:
        return None, [f"Cannot read the file: {e}"]

    df.columns = [c.strip().lower() for c in df.columns]

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        return None, [f"Missing column(s): {', '.join(missing)}"]

    df = df[REQUIRED_COLUMNS].copy()
    if df.empty:
        return None, ["The file has no records."]

    # Empty required values (row numbers match the spreadsheet: header is row 1)
    for col in REQUIRED_COLUMNS:
        blank = df[col].isna() | (df[col].str.strip() == "")
        for i in df.index[blank]:
            errors.append(f"Row {i + 2}: '{col}' is empty.")

    # Date must be YYYY-MM-DD
    parsed_dates = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")
    for i in df.index[parsed_dates.isna() & df["date"].notna() & (df["date"].str.strip() != "")]:
        errors.append(f"Row {i + 2}: date '{df.at[i, 'date']}' must be YYYY-MM-DD.")

    # Numbers must be numeric and not negative
    for col in ["head_count", "total_kilos", "price_per_kilo"]:
        nums = pd.to_numeric(df[col], errors="coerce")
        has_text = df[col].notna() & (df[col].str.strip() != "")
        for i in df.index[nums.isna() & has_text]:
            errors.append(f"Row {i + 2}: '{col}' must be a number, got '{df.at[i, col]}'.")
        for i in df.index[nums < 0]:
            errors.append(f"Row {i + 2}: '{col}' cannot be negative.")
        df[col] = nums

    if (df["head_count"].dropna() % 1 != 0).any():
        errors.append("head_count must be whole numbers.")

    if errors:
        return None, errors

    df["date"] = parsed_dates.dt.strftime("%Y-%m-%d")
    return df, []


def upload_dataset(file_path, name, source=""):
    """Validate, then save. Returns (dataset_id or None, list_of_errors)."""
    if get_dataset_id(name) is not None:
        return None, [f"A dataset named '{name}' already exists."]
    df, errors = validate_csv(file_path)
    if errors:
        return None, errors
    dataset_id = create_dataset_with_records(name, source, df)
    return dataset_id, []
