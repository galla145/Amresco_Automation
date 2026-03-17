import pandas as pd
import os

file_path = "excel files/August/38D North 2024 Monthly Production.xlsx"

if os.path.exists(file_path):
    df = pd.read_excel(file_path, sheet_name='Aug', skiprows=1)
    print("Columns found:")
    print(df.columns.tolist())
    
    # Clean data: remove 'Total' row and NaN sites
    df_clean = df.dropna(subset=['Site'])
    df_clean = df_clean[df_clean['Site'].str.strip() != 'Total']
    
    # Ensure they are numeric
    df_clean['Actual'] = pd.to_numeric(df_clean['Actual'], errors='coerce')
    df_clean['Expected'] = pd.to_numeric(df_clean['Expected'], errors='coerce')
    
    actual = df_clean['Actual'].sum()
    expected = df_clean['Expected'].sum()
    
    delta = actual - expected
    performance = (actual / expected) * 100 if expected != 0 else 0
    
    print("\n--- RESULTS ---")
    print(f"System Actual: {actual}")
    print(f"Expected: {expected}")
    print(f"Delta: {delta}")
    print(f"Performance %: {performance}")
else:
    print("File not found.")
