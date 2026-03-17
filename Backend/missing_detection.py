import pandas as pd
from openpyxl.utils import get_column_letter

def analyze_missing_values(file_path):

    excel = pd.ExcelFile(file_path)

    issues = []
    total_cells_excel = 0
    total_incomplete_excel = 0

    for sheet in excel.sheet_names:

        if sheet.lower() == "sites":
            continue

        df = pd.read_excel(file_path, sheet_name=sheet, header=[0,1,2])

        total_cells_excel += df.shape[0] * df.shape[1]

        # use only 3rd header row as column name
        df.columns = [
            str(col[2]).strip() if str(col[2]) != "nan" else ""
            for col in df.columns
        ]

        for r in range(len(df)):

            site_name = df.iloc[r, 0]

            for c in range(len(df.columns)):

                value = df.iloc[r, c]
                column_name = df.columns[c]
                cell = f"{get_column_letter(c+1)}{r+4}"

                issue = None

                if pd.isna(value):
                    issue = "Missing"
                elif value == 0:
                    issue = "Zero"
                elif str(value).strip().upper() in ["N/A", "NA", "#N/A"]:
                    issue = "N/A"

                if issue:

                    total_incomplete_excel += 1

                    issues.append({
                        "sheet_name": sheet,
                        "site_name": str(site_name),
                        "column_name": column_name,
                        "cell": cell,
                        "issue_type": issue,
                        "value": str(value)
                    })

    percent_incomplete = (total_incomplete_excel / total_cells_excel) * 100

    return {
        "total_cells": total_cells_excel,
        "missing_values": total_incomplete_excel,
        "percentage": round(percent_incomplete, 2),
        "issues": issues
    }