import pandas as pd
import os

folder_path = "excel files/August"
target_keywords = ["energy", "kwh"]

print(f"Searching for {target_keywords} in {folder_path}...")

for file in os.listdir(folder_path):
    if file.endswith(".xlsx"):
        file_path = os.path.join(folder_path, file)
        try:
            # Read only header to speed up
            xl = pd.ExcelFile(file_path)
            for sheet in xl.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet, nrows=0)
                cols = [str(c).lower() for c in df.columns]
                for kw in target_keywords:
                    if any(kw in c for c in cols):
                        print(f"MATCH FOUND! File: {file}, Sheet: {sheet}, Keywords: {kw}")
                        print(f"Columns: {df.columns.tolist()}")
        except Exception as e:
            print(f"Could not read {file}: {e}")
