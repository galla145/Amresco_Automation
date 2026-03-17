import pandas as pd
import os

file_path = "excel files/August/38D North 2024 Monthly Production.xlsx"
df = pd.read_excel(file_path, sheet_name='Aug', header=None, nrows=10)
print(df.to_string())
