import pandas as pd
import os
import sqlite3
import sys

# Add current dir to path to import local modules if needed
sys.path.append(os.getcwd())

DB_PATH = "data/solar_production.db"
EXCEL_ROOTS = ["excel files/2024", "excel files/2025"]

# Map sheet keywords to our internal "month" names
SHEET_MAP = {
    "Year to Date": "YTD",
    "1st Qtr": "Q1",
    "2nd Qtr": "Q2",
    "3rd Qtr": "Q3",
    "4th Qtr": "Q4",
    "Jan": "January",
    "Feb": "February",
    "Mar": "March",
    "Apr": "April",
    "May": "May",
    "Jun": "June",
    "Jul": "July",
    "Aug": "August",
    "Sep": "September",
    "Oct": "October",
    "Nov": "November",
    "Dec": "December"
}

def clean_num(val):
    if pd.isna(val) or str(val).strip() in ['-', '']: return 0.0
    try:
        return float(pd.to_numeric(val, errors='coerce'))
    except: return 0.0

def ingest():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create table if not exists (just in case)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS production_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_name TEXT,
            month TEXT,
            actual REAL,
            expected REAL,
            orig_delta REAL,
            comp_delta REAL,
            orig_perf REAL,
            comp_perf REAL,
            file_source TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
    ''')
    
    # Clear old 2024 industrial data to avoid duplicates if re-running
    # Actually, we might want to keep what we have. Let's just append but skip duplicates?
    # For simplicity, let's just append for now.
    
    extracted_count = 0
    
    # Walk through the directories
    for excel_root in EXCEL_ROOTS:
        if not os.path.exists(excel_root): continue
        for root, dirs, files in os.walk(excel_root):
            for file in files:
                if not file.endswith(".xlsx") or "~$" in file: continue
                file_path = os.path.join(root, file)
                print(f"Processing: {file}")
            
            try:
                xl = pd.ExcelFile(file_path)
                for sheet_keyword, internal_name in SHEET_MAP.items():
                    # Find sheet that starts with the keyword (e.g. "Jan" matches "Jan")
                    target_sheet = next((s for s in xl.sheet_names if s.lower().startswith(sheet_keyword.lower())), None)
                    if not target_sheet: continue
                    
                    print(f"  -> Sheet: {target_sheet} ({internal_name})")
                    
                    # Read header
                    df_raw = pd.read_excel(file_path, sheet_name=target_sheet, header=None, engine="openpyxl", nrows=20)
                    header_row = 0
                    found = False
                    for i, row in df_raw.iterrows():
                        row_list = [str(val).strip().lower() for val in row if pd.notna(val)]
                        if 'site' in row_list and 'actual' in row_list:
                            header_row = i
                            found = True
                            break
                    if not found: continue
                    
                    df = pd.read_excel(file_path, sheet_name=target_sheet, header=header_row, engine="openpyxl")
                    df.columns = [str(c).strip() for c in df.columns]
                    
                    if 'Site' not in df.columns: continue
                    df = df.dropna(subset=['Site'])
                    df = df[~df['Site'].str.contains('Total', case=False, na=False)]
                    
                    perc_col = next((c for c in ['%', 'Delta %', '%.1', 'Performance'] if c in df.columns), None)
                    delta_col = next((c for c in ['Delta', 'Difference'] if c in df.columns), None)
                    notes_col = next((c for c in ['Notes', 'Comments', 'Reason', 'Faults', 'Service Requests', 'SR'] if c in df.columns), None)
                    
                    for _, row in df.iterrows():
                        actual = clean_num(row.get('Actual'))
                        expected = clean_num(row.get('Expected'))
                        orig_delta = clean_num(row.get(delta_col))
                        
                        raw_orig_perc = row.get(perc_col)
                        try:
                            orig_perc = pd.to_numeric(raw_orig_perc, errors='coerce') or 0.0
                            if abs(orig_perc) < 1.1 and orig_perc != 0: orig_perc *= 100
                        except: orig_perc = 0.0
                        
                        comp_delta = actual - expected
                        comp_perf = (comp_delta / expected * 100) if expected != 0 else 0.0
                        
                        notes = str(row.get(notes_col)).strip() if notes_col and pd.notna(row.get(notes_col)) else ""
                        
                        cursor.execute('''
                            INSERT INTO production_records (
                                site_name, month, actual, expected, orig_delta, comp_delta, orig_perf, comp_perf, file_source, notes
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            str(row['Site']).strip(), internal_name, actual, expected,
                            orig_delta, comp_delta, round(orig_perc, 1), round(comp_perf, 1),
                            file, notes
                        ))
                        extracted_count += 1
                
                conn.commit()
            except Exception as e:
                print(f"  [ERROR] Failed to process {file}: {e}")
                
    conn.close()
    print(f"\n[DONE] Extracted {extracted_count} records into {DB_PATH}")

if __name__ == "__main__":
    ingest()
