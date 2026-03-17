import pandas as pd
import os

file_path = "excel files/August/LX International August 2024 Daily Production 3.xlsx"
full_path = os.path.join(os.getcwd(), file_path)

if os.path.exists(full_path):
    print(f"Loading: {file_path}")
    df = pd.read_excel(full_path, skiprows=3) # Assuming headers start at row 3
    print(f"\nDataFrame shape: {df.shape}")
    print("\nFirst 10 rows:")
    print(df.head(10))
    
    # Check for date duplicates (which would indicate hourly)
    # The first column seems to be 'Date Period' based on previous inspection
    date_col = df.columns[0]
    print(f"\nValue counts for {date_col}:")
    print(df[date_col].value_counts().head(10))
    
else:
    print(f"File NOT found at {full_path}")
