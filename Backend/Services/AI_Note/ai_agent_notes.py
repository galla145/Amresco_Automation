import pandas as pd
import ollama

file_path = r"C:\Users\allad\Desktop\job_offer\AGS\AMRESCO_Automation\AI_Note\American Polyfilm 2025 Monthly Production.xlsx"

def generate_note_local(row, month_name):

    prompt = f"""
You are an energy operations analyst.

Generate blended operational + performance commentary.

Month: {month_name}
Site: {row['Site']}
State: {row['State']}

Actual Production: {row['Actual']}
Forecasted Production: {row['Forecasted']}
Delta vs Forecast: {row['Delta']}
Performance %: {row['%']}

Write 2-3 professional executive-level sentences.
If performance is below forecast, suggest possible operational reasons.
If above forecast, highlight operational stability.
Do not repeat raw numbers exactly.
"""

    response = ollama.chat(
        model='llama3',
        messages=[{'role': 'user', 'content': prompt}]
    )

    return response['message']['content']


# -------------------------
# PROCESS EXCEL
# -------------------------

xls = pd.ExcelFile(file_path)

monthly_sheets = ["Jan","Feb","Mar","Apr","May","Jun",
                  "Jul","Aug","Sep","Oct","Nov","Dec"]

for sheet in xls.sheet_names:

    if sheet in monthly_sheets:

        raw_df = pd.read_excel(file_path, sheet_name=sheet, header=None)

        # Fix multi-row header structure
        raw_df.columns = raw_df.iloc[1]
        df = raw_df[2:].reset_index(drop=True)

        if "Notes" in df.columns:

            mask = df["Notes"].isna() | (df["Notes"].astype(str).str.strip() == "")

            if mask.any():

                print(f"\n===== Processing {sheet} =====")

                df.loc[mask, "Predicted_Note"] = df[mask].apply(
                    lambda row: generate_note_local(row, sheet),
                    axis=1
                )

                print(df[mask][[
                    "Site","State","Actual",
                    "Forecasted","Delta","%",
                    "Predicted_Note"
                ]])