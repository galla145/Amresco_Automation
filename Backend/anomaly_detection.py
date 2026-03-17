# anomaly_detection.py

import os
import pandas as pd
import numpy as np
import joblib

# -----------------------------
# Load saved model
# -----------------------------
MODEL_PATH = os.path.join(os.path.dirname(__file__), "anomaly_model.joblib")
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Saved model not found at '{MODEL_PATH}'")

model = joblib.load(MODEL_PATH)
print("Anomaly detection model loaded successfully.")

# -----------------------------
# Convert percent values
# -----------------------------
def convert_percent(val):
    """
    Convert Excel percent strings (e.g., '50%', '-12.3%') to float.
    """
    if pd.isna(val):
        return None
    if isinstance(val, str):
        val = val.replace("%", "").replace(",", "").strip()
        try:
            return float(val) / 100
        except:
            return None
    try:
        return float(val)
    except:
        return None

# -----------------------------
# Extract percent values from Excel
# -----------------------------
def extract_percent_values(file):
    """
    Extract all percent values from Excel sheets.
    Only considers columns containing '%' in the header and rows with 'Site'.
    """
    try:
        sheets = pd.read_excel(file, sheet_name=None, header=2)
    except Exception as e:
        raise ValueError(f"Error reading {file}: {e}")

    data = []
    for sheet_name, df in sheets.items():
        if "Site" not in df.columns:
            continue
        percent_cols = [c for c in df.columns if "%" in str(c)]
        if not percent_cols:
            continue

        for i, row in df.iterrows():
            site = row["Site"]
            if pd.isna(site):
                continue

            for col in percent_cols:
                p = convert_percent(row[col])
                if p is None:
                    continue

                data.append({
                    "sheet": sheet_name,
                    "site": site,
                    "column": col,
                    "row": i,
                    "value": p
                })

    return pd.DataFrame(data)

# -----------------------------
# Helper: Convert column index to Excel letters
# -----------------------------
def col_idx_to_excel(col_idx):
    """
    Convert zero-based column index to Excel column letters.
    e.g., 0 -> 'A', 1 -> 'B', 26 -> 'AA'
    """
    letters = ""
    while col_idx >= 0:
        letters = chr(col_idx % 26 + 65) + letters
        col_idx = col_idx // 26 - 1
    return letters

# -----------------------------
# Analyze Excel for anomalies
# -----------------------------
def analyze_file(file_path):
    """
    Analyze the Excel file for:
    - Abnormal values (>100% or <-100%)
    - Underperforming sites (<= -10%)
    - ML anomalies
    Returns a list of dicts with issues, with actual Excel cell numbers.
    """
    df = extract_percent_values(file_path)
    if df.empty:
        return []

    results = []

    # ML anomaly prediction
    preds = model.predict(df["value"].values.reshape(-1, 1))
    df["anomaly"] = preds

    # Column name mapping
    col_name_map = {"%": "Expected%", "%.1": "Forecasted%"}

    # Load Excel file for column positions
    xls = pd.ExcelFile(file_path)

    for idx, row in df.iterrows():
        sheet_name = row["sheet"]
        site = row["site"]
        col_name = row["column"]
        value = row["value"]
        row_index = row["row"]  # zero-based index in pandas

        # Map column names
        display_col = col_name_map.get(col_name, col_name)

        # Get sheet DataFrame
        sheet_df = pd.read_excel(xls, sheet_name=sheet_name, header=2)
        if col_name not in sheet_df.columns:
            continue

        # Get Excel column letter
        col_idx = list(sheet_df.columns).index(col_name)
        excel_col_letter = col_idx_to_excel(col_idx)

        # Excel row number (header offset + pandas index + 1)
        excel_row_number = row_index + 3 + 1  # header=2, pandas index starts 0
        cell_address = f"{excel_col_letter}{excel_row_number}"

        # Abnormal rule (>100% or < -100%)
        if value > 1 or value < -1:
            results.append({
                "sheet": sheet_name,
                "site": site,
                "column_name": display_col,
                "cell_number": cell_address,
                "issue_type": "abnormal value"
            })

        # Underperform rule (<= -10%)
        if value <= -0.10:
            results.append({
                "sheet": sheet_name,
                "site": site,
                "column_name": display_col,
                "cell_number": cell_address,
                "issue_type": "underperforming site"
            })

        # ML anomaly
        if row["anomaly"] == -1:
            results.append({
                "sheet": sheet_name,
                "site": site,
                "column_name": display_col,
                "cell_number": cell_address,
                "issue_type": "anomaly value"
            })

    return results