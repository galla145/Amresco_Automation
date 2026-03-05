import pandas as pd
import os
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder
import joblib
import json
import argparse
import sqlite3

def load_and_preprocess(file_path, sheet_name='Aug'):
    # Headers start at row 2 (0-indexed)
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=2, engine="openpyxl")
    except Exception as e:
        print(f"Error loading sheet {sheet_name}: {e}")
        return None
    
    # Standardize column names
    df.columns = [str(c).strip() for c in df.columns]
    return df

def process_file_sites(file_path):
    # For now, we'll look at the 'Aug' sheet as per the report
    df = load_and_preprocess(file_path, 'Aug')
    if df is None:
        return

    # Filter for valid sites (exclude 'Total' and empty rows)
    df_sites = df.dropna(subset=['Site'])
    df_sites = df_sites[df_sites['Site'] != 'Total']
    
    results = []
    
    for _, row in df_sites.iterrows():
        site = row['Site']
        actual = pd.to_numeric(row['Actual'], errors='coerce')
        expected = pd.to_numeric(row['Expected'], errors='coerce')
        
        # Original values from sheet
        orig_delta = row['Delta']
        orig_perf = row['%']
        
        # Recomputed values
        comp_delta = actual - expected if not (pd.isna(actual) or pd.isna(expected)) else 0
        comp_perf = (comp_delta / expected) * 100 if expected and expected != 0 else 0
        
        results.append({
            "Site": site,
            "Actual": actual,
            "Expected": expected,
            "Orig Delta": orig_delta,
            "Comp Delta": round(comp_delta, 1),
            "Orig %": orig_perf,
            "Comp %": f"{round(comp_perf, 1)}%"
        })
        
    return results

CONFIG_PATH = "config.json"
DB_PATH = "data/solar_production.db"

def load_config():
    if not os.path.exists(CONFIG_PATH):
        # Create default config if missing
        default_config = {
            "thresholds": {
                "math_mismatch": 2.0,
                "max_perf": 500.0
            },
            "month_map": {
                "January": "Jan", "February": "Feb", "March": "Mar", "April": "Apr",
                "May": "May", "June": "Jun", "July": "Jul", "August": "Aug",
                "September": "Sep", "October": "Oct", "November": "Nov", "December": "Dec"
            }
        }
        with open(CONFIG_PATH, 'w') as f:
            json.dump(default_config, f, indent=4)
        return default_config
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def save_to_db(records):
    """Saves production records to SQLite and returns their IDs."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    record_ids = []
    
    for r in records:
        cursor.execute('''
            INSERT INTO production_records (
                site_name, month, actual, expected, orig_delta, comp_delta, orig_perf, comp_perf, file_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            r['Site'], r['Month'], r['Actual'], r['Expected'], 
            r['Orig Delta'], r['Comp Delta'], r['Orig %'], r['Comp %'], r['File']
        ))
        record_ids.append(cursor.lastrowid)
        r['db_id'] = cursor.lastrowid
        
    conn.commit()
    conn.close()
    return record_ids

def save_anomaly_to_db(record_id, fault_type):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO flagged_anomalies (record_id, fault_type)
        VALUES (?, ?)
    ''', (record_id, fault_type))
    conn.commit()
    conn.close()

def process_all_files(root_folder, config):
    all_results = {}
    month_map = config['month_map']

    for root, dirs, files in os.walk(root_folder):
        folder_name = os.path.basename(root)
        target_sheet = month_map.get(folder_name)

        for file in files:
            if file.endswith(".xlsx") and "~$" not in file:
                file_path = os.path.join(root, file)
                print(f"--- Processing: {folder_name}/{file} ---")
                
                try:
                    xl = pd.ExcelFile(file_path)
                    
                    # Smart sheet selection
                    sheet_to_use = None
                    if target_sheet and target_sheet in xl.sheet_names:
                        sheet_to_use = target_sheet
                    elif 'Aug' in xl.sheet_names:
                        sheet_to_use = 'Aug'
                    else:
                        sheet_to_use = xl.sheet_names[0]
                    
                    df = pd.read_excel(file_path, sheet_name=sheet_to_use, header=2, engine="openpyxl")
                    df.columns = [str(c).strip() for c in df.columns]
                    
                    if 'Site' not in df.columns or 'Actual' not in df.columns or 'Expected' not in df.columns:
                        df = pd.read_excel(file_path, sheet_name=sheet_to_use, header=1, engine="openpyxl")
                        df.columns = [str(c).strip() for c in df.columns]
                        if 'Site' not in df.columns:
                            continue
                        
                    df_sites = df.dropna(subset=['Site'])
                    df_sites = df_sites[df_sites['Site'] != 'Total']
                    
                    perc_col = None
                    for c in ['%', 'Delta %', '%.1']:
                        if c in df.columns:
                            perc_col = c
                            break

                    file_results = []
                    for _, row in df_sites.iterrows():
                        actual = pd.to_numeric(row['Actual'], errors='coerce')
                        expected = pd.to_numeric(row['Expected'], errors='coerce')
                        
                        if pd.isna(actual) or pd.isna(expected):
                            continue
                            
                        comp_delta = actual - expected
                        comp_perf = (comp_delta / expected) * 100 if expected != 0 else 0
                        orig_delta = pd.to_numeric(row.get('Delta', 0), errors='coerce')
                        
                        orig_perc = 0
                        if perc_col:
                            orig_perc = pd.to_numeric(row.get(perc_col, 0), errors='coerce')
                        
                        file_results.append({
                            "Site": row['Site'],
                            "Actual": actual,
                            "Expected": expected,
                            "Orig Delta": orig_delta,
                            "Comp Delta": comp_delta,
                            "Orig %": orig_perc,
                            "Comp %": comp_perf,
                            "Month": folder_name,
                            "File": f"{folder_name}/{file}"
                        })
                    
                    if file_results:
                        all_results[f"{folder_name}/{file}"] = file_results
                        
                except Exception as e:
                    print(f"  [Error] {file}: {e}")
                    
    return all_results

MODEL_PATH = "models/detector_v1.pkl"
ENCODER_PATH = "models/site_encoder.pkl"

def train_cold_model(all_results_dict):
    """
    COLD TRAINING: Processes all historical data to learn 'Normal' behavior.
    Saves the 'Brain' (Model + Encoder) to disk.
    """
    print("\n[COLD TRAINING] Building historical baseline...")
    flat_data = []
    month_map = {
        "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
        "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12
    }

    for file_key, sites in all_results_dict.items():
        for site in sites:
            flat_data.append({
                "site_name": site['Site'],
                "month_num": month_map.get(site['Month'], 0),
                "features": [site['Actual'], site['Expected'], site['Comp Delta'], site['Comp %']]
            })
    
    if not flat_data:
        print("[ERROR] No data found for training.")
        return

    # Encode Site Names so the model 'remembers' Site A vs Site B
    le = LabelEncoder()
    all_site_names = [d['site_name'] for d in flat_data]
    le.fit(all_site_names)
    encoded_sites = le.transform(all_site_names)

    # Build Feature Matrix: [Actual, Expected, Delta, Perf %, Month, SiteID]
    X = []
    for i, d in enumerate(flat_data):
        X.append(d['features'] + [d['month_num'], encoded_sites[i]])
    X = np.array(X)

    # Train Isolation Forest (Contamination=0.03 to keep baseline clean)
    clf = IsolationForest(contamination=0.03, random_state=42)
    clf.fit(X)

    # Persist the Brain
    os.makedirs("models", exist_ok=True)
    joblib.dump(clf, MODEL_PATH)
    joblib.dump(le, ENCODER_PATH)
    print(f"✅ Training Complete. Baseline saved to: {MODEL_PATH}")

def run_hot_inference(results_dict):
    """
    HOT INFERENCE: Uses the pre-trained 'Brain' to flag anomalies in milliseconds.
    """
    if not os.path.exists(MODEL_PATH) or not os.path.exists(ENCODER_PATH):
        print("No trained model found. Running first-time detection on current batch only.")
        return results_dict

    clf = joblib.load(MODEL_PATH)
    le = joblib.load(ENCODER_PATH)
    
    month_map = {
        "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
        "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12
    }

    print(f"\n[HOT INFERENCE] Comparing {len(results_dict)} reports against historical 'Normal'...")

    for file_key, sites in results_dict.items():
        for site in sites:
            # 1. Prepare Features
            features = [site['Actual'], site['Expected'], site['Comp Delta'], site['Comp %']]
            month_num = month_map.get(site['Month'], 0)
            
            # 2. Check if Site is Known
            site_name = site['Site']
            if site_name in le.classes_:
                site_id = le.transform([site_name])[0]
                is_unknown_site = False
            else:
                # Assign a dummy ID for unknown sites to trigger anomaly if behavior is wild
                site_id = -1 
                is_unknown_site = True
            
            X_input = np.array([features + [month_num, site_id]])
            
            # 3. Predict abnormality
            prediction = clf.predict(X_input)[0] # 1 = Normal, -1 = Abnormality
            
            # Flag as anomaly if model says so OR if it's a completely new site name
            site['Is Anomaly'] = (prediction == -1)
            if is_unknown_site:
                site['Is Anomaly'] = True # Always flag new sites for validation
                site['Anomaly Reason'] = "New Site/No History"
            
    return results_dict

def print_structured_output(filename, results):
    RED = "\033[91m"
    RESET = "\033[0m"
    
    header = f"{'Site':<35} | {'Actual':<10} | {'Expected':<10} | {'Org Delta':<10} | {'Comp Delta':<10} | {'Org %':<6} | {'Comp %':<6}"
    print(f"\nFILE: {filename}")
    print(header)
    print("-" * len(header))
    
    for res in results:
        actual_str = f"{res['Actual']:,.0f}"
        expected_str = f"{res['Expected']:,.0f}"
        comp_delta_str = f"{res['Comp Delta']:,.0f}"
        
        orig_delta_val = res['Orig Delta']
        orig_delta_str = f"{orig_delta_val:,.0f}" if not pd.isna(orig_delta_val) else "N/A"
        
       
        orig_p_val = res['Orig %']
        if pd.isna(orig_p_val):
             orig_p_str = "N/A"
        elif abs(orig_p_val) < 1.1 and orig_p_val != 0: # Likely a decimal like -0.218
             orig_p_str = f"{round(orig_p_val * 100):.0f}%"
        else: 
             orig_p_str = f"{round(orig_p_val):.0f}%"

        
        comp_p_str = f"{round(res['Comp %']):.0f}%"

        
        # Check for discrepancies (Math check)
        # Using a threshold of 2 for minor rounding differences in Excel
        has_mismatch = abs(res['Comp Delta'] - res['Orig Delta']) > 2
        is_anomaly = res.get('Is Anomaly', False)
        
        flag = ""
        if has_mismatch:
            flag += f" {RED}[MATH MISMATCH]{RESET}"
        if is_anomaly:
            flag += f" {RED}🚩 [ANOMALY]{RESET}"

        print(f"{res['Site']:<35} | {actual_str:<10} | {expected_str:<10} | {orig_delta_str:<10} | {comp_delta_str:<10} | {orig_p_str:<6} | {comp_p_str:<6}{flag}")

def print_final_summary_table(mismatches):
    """Prints a clean table of only the sites that need attention from the 2024 batch."""
    RED = "\033[91m"
    RESET = "\033[0m"
    
    print("\n" + "="*125)
    print(f"{RED}FINAL SUMMARY: 2024 RECORDS REQUIRING REVIEW / ATTENTION{RESET}")
    print("="*125)
    
    if not mismatches:
        print("✅ No math mismatches or statistical anomalies detected in the 2024 batch.")
        return

    header = f"{'Site':<35} | {'Source File':<30} | {'Month':<10} | {'Type':<10} | {'Perf %'}"
    print(header)
    print("-" * len(header))
    
    for m in mismatches:
        err_types = []
        if m.get('has_math_error'): err_types.append("MATH")
        if m.get('is_anomaly'): err_types.append("ANOMALY")
        
        type_str = "/".join(err_types)
        perf_str = f"{round(m['Comp %']):.0f}%"
        month = m.get('Month', 'N/A')
        
        # Truncate long filenames for clarity
        fname = m['File']
        if len(fname) > 29: fname = fname[:26] + "..."
        
        print(f"{m['Site']:<35} | {fname:<30} | {month:<10} | {type_str:<10} | {perf_str}")
    
    print("="*125)
    print(f"Total problematic sites flagged in 2024: {len(mismatches)}")
    
    # Save to JSON for frontend
    os.makedirs('data', exist_ok=True)
    with open('data/flagged_sites.json', 'w') as f:
        json.dump(mismatches, f, indent=4, default=str)
    print(f"\n[INFO] 2024 Flagged data exported to: data/flagged_sites.json")

def process_individual_file(file_path, config, month_name=None):
    """
    Processes a single Excel file, recomputes metrics, and returns a list of site results.
    """
    try:
        xl = pd.ExcelFile(file_path)
        month_map = config['month_map']
        
        # Determine target sheet
        sheet_to_use = None
        if month_name and month_map.get(month_name) in xl.sheet_names:
            sheet_to_use = month_map[month_name]
        else:
            # Fallback logic
            possible_sheets = list(month_map.values()) + ['Aug', 'Total']
            for ps in possible_sheets:
                if ps in xl.sheet_names:
                    sheet_to_use = ps
                    break
            if not sheet_to_use:
                sheet_to_use = xl.sheet_names[0]

        df = pd.read_excel(file_path, sheet_name=sheet_to_use, header=2, engine="openpyxl")
        df.columns = [str(c).strip() for c in df.columns]
        
        if 'Site' not in df.columns or 'Actual' not in df.columns or 'Expected' not in df.columns:
            df = pd.read_excel(file_path, sheet_name=sheet_to_use, header=1, engine="openpyxl")
            df.columns = [str(c).strip() for c in df.columns]
            if 'Site' not in df.columns:
                return None

        df_sites = df.dropna(subset=['Site'])
        df_sites = df_sites[df_sites['Site'] != 'Total']
        
        perc_col = None
        for c in ['%', 'Delta %', '%.1']:
            if c in df.columns:
                perc_col = c
                break

        file_results = []
        for _, row in df_sites.iterrows():
            actual = pd.to_numeric(row['Actual'], errors='coerce')
            expected = pd.to_numeric(row['Expected'], errors='coerce')
            
            if pd.isna(actual) or pd.isna(expected):
                continue
                
            comp_delta = actual - expected
            comp_perf = (comp_delta / expected) * 100 if expected != 0 else 0
            orig_delta = pd.to_numeric(row.get('Delta', 0), errors='coerce')
            
            orig_perc = 0
            if perc_col:
                orig_perc = pd.to_numeric(row.get(perc_col, 0), errors='coerce')
            
            file_results.append({
                "Site": row['Site'],
                "Actual": actual,
                "Expected": expected,
                "Orig Delta": orig_delta,
                "Comp Delta": comp_delta,
                "Orig %": orig_perc,
                "Comp %": comp_perf,
                "Month": month_name or "Unknown",
                "File": os.path.basename(file_path)
            })
        return file_results
    except Exception as e:
        print(f"Error processing file: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Ameresco Solar Anomaly Detector")
    parser.add_argument("--train", action="store_true", help="Run COLD training on historical folder")
    parser.add_argument("--folder", type=str, help="Folder for training (e.g., 'excel files')")
    parser.add_argument("--file", type=str, help="Single file for hot inference")
    parser.add_argument("--month", type=str, help="Month name for the single file (e.g., 'August')")
    args = parser.parse_args()

    config = load_config()
    thresholds = config['thresholds']

    print("\n" + "="*110)
    if args.train:
        print("AI PERFORMANCE ENGINE - COLD TRAINING MODE")
        print("="*110)
        if not args.folder:
            print("[ERROR] --folder is required for training.")
            return
        
        all_data = process_all_files(args.folder, config)
        train_cold_model(all_data)
        
        # Save historical batch to DB
        flat_records = []
        for f, sites in all_data.items(): flat_records.extend(sites)
        save_to_db(flat_records)
        return

    # HOT INFERENCE MODE
    print("AI PERFORMANCE ENGINE - HOT INFERENCE MODE")
    print("="*110)

    if not args.file:
        print("[USAGE] Provide a file to inspect: python main.py --file 'path/to/report.xlsx' --month 'August'")
        return

    if not os.path.exists(args.file):
        print(f"[ERROR] File not found: {args.file}")
        return

    # 1. Process just the one file
    single_results = process_individual_file(args.file, config, args.month)
    if not single_results:
        print("[ERROR] Could not extract data from the provide file.")
        return

    # 2. Run the "Brain" on just this one sheet
    input_data = {os.path.basename(args.file): single_results}
    input_data = run_hot_inference(input_data)
    
    # 3. Save ALL records from this upload to SQLite
    save_to_db(single_results)

    mismatches = []
    # 4. Identify and Link anomalies in SQLite
    for file_key, results in input_data.items():
        print_structured_output(file_key, results)
        
        for res in results:
            has_math_error = abs(res['Comp Delta'] - res['Orig Delta']) > thresholds['math_mismatch']
            is_stat_anomaly = res.get('Is Anomaly', False)
            is_data_error = (res['Expected'] == 0 and res['Actual'] > 0) or (abs(res['Comp %']) > thresholds['max_perf'])
            
            if has_math_error or is_stat_anomaly or is_data_error:
                res['has_math_error'] = has_math_error
                res['is_anomaly'] = is_stat_anomaly
                res['is_data_error'] = is_data_error
                mismatches.append(res)
                
                # Flag the anomaly in SQLite using the record ID we just got
                fault_types = []
                if has_math_error: fault_types.append("MATH")
                if is_stat_anomaly: fault_types.append("STAT")
                if is_data_error: fault_types.append("DATA")
                
                # Save just the pointer to the already-saved record
                save_anomaly_to_db(res['db_id'], "/".join(fault_types))

    # 5. Final Report for the specific sheet
    print_final_summary_table(mismatches)

def print_final_summary_table(mismatches):
    """Prints a detailed comparison table of only the flagged sites."""
    RED = "\033[91m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"
    
    print("\n" + "!"*135)
    print(f"{RED}{'!!! MISMATCHED & ANOMALOUS RECORDS DETECTED !!!':^135}{RESET}")
    print("!"*135)
    
    if not mismatches:
        print(f"✅ {YELLOW}No suspicious records found in this batch.{RESET}")
        return

    # Updated Header to show the actual comparison the user wants to see
    header = f"{'Site Name':<35} | {'Actual':<10} | {'Expected':<10} | {'Org Delta':<10} | {'Comp Delta':<10} | {'Fault Type'}"
    print(header)
    print("-" * len(header))
    
    for m in mismatches:
        faults = []
        if m.get('has_math_error'): faults.append("MATH")
        if m.get('is_anomaly'): faults.append("STAT")
        if m.get('is_data_error'): faults.append("DATA")
        
        fault_str = "/".join(faults)
        
        actual_str = f"{m['Actual']:,.0f}"
        expected_str = f"{m['Expected']:,.0f}"
        org_delta_str = f"{m['Orig Delta']:,.0f}"
        comp_delta_str = f"{m['Comp Delta']:,.0f}"
        
        # Color specific faults
        line_color = RED if "MATH" in fault_str or "DATA" in fault_str else YELLOW
        
        print(f"{line_color}{m['Site'][:34]:<35} | {actual_str:<10} | {expected_str:<10} | {org_delta_str:<10} | {comp_delta_str:<10} | {fault_str}{RESET}")
    
    print("="*135)
    print(f"Total Flags: {len(mismatches)} sites require manual validation.")
    
    # Save to JSON for frontend
    os.makedirs('data', exist_ok=True)
    with open('data/flagged_sites.json', 'w') as f:
        json.dump(mismatches, f, indent=4, default=str)
    print(f"\n[INFO] Decision Engine results exported to: data/flagged_sites.json")

if __name__ == "__main__":
    main()
