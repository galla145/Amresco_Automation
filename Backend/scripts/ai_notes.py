import pandas as pd
import os
import numpy as np
import json
import argparse
import sqlite3
import joblib
import pickle
from sklearn.metrics.pairwise import cosine_similarity
import google.generativeai as genai
from dotenv import load_dotenv
import concurrent.futures

load_dotenv()

CONFIG_PATH = r"C:\Users\allad\Desktop\job_offer\AGS\AMRESCO_Automation\Backend\config.json"
DB_PATH = r"C:\Users\allad\Desktop\job_offer\AGS\AMRESCO_Automation\Backend\data\solar_production.db"
MODEL_PATH = r"C:\Users\allad\Desktop\job_offer\AGS\AMRESCO_Automation\Backend\models\detector_v1.pkl"
ENCODER_PATH = r"C:\Users\allad\Desktop\job_offer\AGS\AMRESCO_Automation\Backend\models\site_encoder.pkl"
BASELINES_PATH = r"C:\Users\allad\Desktop\job_offer\AGS\AMRESCO_Automation\Backend\models\site_month_baselines.json"
RAG_INDEX_PATH = r"C:\Users\allad\Desktop\job_offer\AGS\AMRESCO_Automation\Backend\data\rag_index_2024.pkl"

def load_config():
    if not os.path.exists(CONFIG_PATH):
        default_config = {
            "thresholds": {"math_mismatch": 2.0, "max_perf": 100.0},
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
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for r in records:
        cursor.execute('''
            INSERT INTO production_records (
                site_name, month, actual, expected, orig_delta, comp_delta, orig_perf, comp_perf, file_source, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            r['Site'], r['Month'], r['Actual'], r['Expected'], 
            r['Orig Delta'], r['Comp Delta'], r['Orig %'], r['Comp %'], r['File'], r['Notes']
        ))
        r['db_id'] = cursor.lastrowid
    conn.commit()
    conn.close()

def save_anomaly_to_db(record_id, fault_type):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO flagged_anomalies (record_id, fault_type) VALUES (?, ?)', (record_id, fault_type))
    conn.commit()
    conn.close()

def get_historical_suggestion(site_name, comp_perf, current_month, current_file):
    """Finds a suggestion using a fallback chain, excluding the current file/month to ensure its truly historical."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. BEST MATCH: This site + Similar performance (from PREVIOUS reports)
        cursor.execute('''
            SELECT notes FROM production_records 
            WHERE site_name = ? 
              AND comp_perf BETWEEN ? AND ? 
              AND notes NOT IN ('', 'nan', 'None', '-', 'service requests')
              AND (month != ? OR file_source != ?)
            GROUP BY notes ORDER BY COUNT(*) DESC LIMIT 1
        ''', (site_name, comp_perf - 5.0, comp_perf + 5.0, current_month, current_file))
        res = cursor.fetchone()
        if res:
            conn.close()
            return f"[Site Pattern] {res[0]}"

        # 2. SITE MATCH: Any historical note for this site
        cursor.execute('''
            SELECT notes FROM production_records 
            WHERE site_name = ? 
              AND notes NOT IN ('', 'nan', 'None', '-', 'service requests')
              AND (month != ? OR file_source != ?)
            ORDER BY timestamp DESC LIMIT 1
        ''', (site_name, current_month, current_file))
        res = cursor.fetchone()
        if res:
            conn.close()
            return f"[Previous Note] {res[0]}"

        # 3. GLOBAL MATCH: Most common reason for this performance range across all sites (Historical)
        cursor.execute('''
            SELECT notes FROM production_records 
            WHERE comp_perf BETWEEN ? AND ?
              AND notes NOT IN ('', 'nan', 'None', '-', 'service requests')
              AND (month != ? OR file_source != ?)
            GROUP BY notes ORDER BY COUNT(*) DESC LIMIT 1
        ''', (comp_perf - 5.0, comp_perf + 5.0, current_month, current_file))
        res = cursor.fetchone()
        conn.close()
        
        if res:
            return f"[Historical Trend] {res[0]}"
            
        return None
    except:
        return None

def get_rag_suggestion(rag_index, site_name, comp_perf):
    """Uses semantic similarity (TF-IDF) to find the best match in the 2024 indexed notes."""
    if not rag_index: return None
    try:
        # Create query string similar to the indexed document format
        query = f"Site: {site_name} | Perf: {comp_perf}%"
        
        vectorizer = rag_index['vectorizer']
        matrix = rag_index['tfidf_matrix']
        raw_data = rag_index['raw_data']
        
        # Transform query and calculate similarity
        query_vec = vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, matrix).flatten()
        
        # Get top result
        top_idx = np.argmax(similarities)
        score = similarities[top_idx]
        
        if score > 0.25: # Minimum confidence threshold
            match = raw_data[top_idx]
            return f"Site: {match['site']}, Perf: {match['perf']}%, Note: {match['note']}"
        return None
    except:
        return None

def get_llm_suggestion(site_name, comp_perf, rag_context, current_note=None):
    """Generates a one-liner suggestion using Gemini based on historical RAG context and current note."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "GOOGLE_API_KEY":
        return None
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""
        As a solar energy performance analyst, provide a single concise action sentence for a performance issue.
        Site: {site_name}
        Current Performance: {comp_perf}%
        
        Current Note from Operator: {current_note if current_note else "None"}
        
        Extra Context (Historical or Missing Data flags):
        {rag_context if rag_context else "No extra context found."}
        
        Requirements:
        1. Output EXACTLY one concise sentence.
        2. Start the sentence with "Check the weather station" if the issue relates to data or sensors, otherwise start with a direct action.
        3. Do NOT mention the site name.
        4. Focus on the most likely cause and the immediate next step.
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error: {str(e)}"

def _normalize_for_compare(text):
    """Normalize text for comparison - collapses whitespace and lowercase."""
    import re
    t = text.lower().strip()
    t = re.sub(r'\s+', ' ', t)
    return t

def fix_grammar(note_text):
    """Fixes grammar and spelling of a given note using Gemini. Returns (corrected_text, was_changed)."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "GOOGLE_API_KEY" or not note_text.strip() or len(note_text) < 4:
        return note_text, False
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = f"""STRICT CORRECTION ONLY:
1. Fix spelling mistakes (e.g., 'forcasted' -> 'forecasted').
2. Fix punctuation and grammar.
3. Preserve all technical details, site names, and numbers exactly.
4. DO NOT add any new information, dates, or facts not present in the original note.
5. DO NOT add preambles or labels like 'Note:'.
6. If the note is already correct, respond with: NO_CHANGE
7. Return ONLY the polished version of the original text.

Original Note: {note_text}"""
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith(('"', "'")) and text.endswith(('"', "'")): text = text[1:-1]
        
        if text.upper() == 'NO_CHANGE':
            return note_text, False
        
        # Post-process: Aggressively remove common LLM preambles/labels
        # Matches "Note:", "Corrected:", "Fixed Note:", "1. Note:", etc. at start of string
        import re
        text = re.sub(r'^(?:note|corrected|fixed|revised|note|corrected note|suggestion)\s*[:\-]\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^[\d\.]+\s*(?:note|corrected|fixed|revised|suggestion)\s*[:\-]\s*', '', text, flags=re.IGNORECASE)
        text = text.strip()
        
        if text == note_text:
            return note_text, False
        
        print(f"[fix_grammar] UPDATED: {note_text[:30]}... -> {text[:30]}...")
        return text, True
    except Exception as e:
        import traceback
        print(f"[fix_grammar] CRITICAL ERROR: {e}")
        traceback.print_exc()
        return note_text, False

def process_individual_file(file_path, config, month_name):
    try:
        xl = pd.ExcelFile(file_path)
        target_sheet = config['month_map'].get(month_name)
        
        if not target_sheet or target_sheet not in xl.sheet_names:
            matches = [s for s in xl.sheet_names if s.startswith(target_sheet or "???")]
            if matches:
                target_sheet = matches[0]
            elif month_name in xl.sheet_names:
                # Direct sheet name match (e.g. 'Year to Date', '1st Qtr')
                target_sheet = month_name
            else:
                print(f"[ERROR] Could not find sheet for {month_name}")
                return None

        df_raw = pd.read_excel(file_path, sheet_name=target_sheet, header=None, engine="openpyxl")
        header_row = 0
        found_header = False
        for i, row in df_raw.iterrows():
            row_list = [str(val).strip().lower() for val in row if pd.notna(val)]
            has_site = any('site' in s for s in row_list)
            has_actual = any('actual' in s for s in row_list)
            if has_site and has_actual:
                header_row = i
                found_header = True
                break
        
        if not found_header: return None

        # Load the data with the detected header row
        try:
            df = pd.read_excel(file_path, sheet_name=target_sheet, header=header_row, engine="openpyxl", engine_kwargs={'data_only': True})
        except:
            # Fallback if engine_kwargs is not supported or fails
            df = pd.read_excel(file_path, sheet_name=target_sheet, header=header_row, engine="openpyxl")
        df.columns = [str(c).strip() for c in df.columns]
        df = df.dropna(subset=['Site'])
        df = df[~df['Site'].str.contains('Total', case=False, na=False)]

        results = []
        
        # Robust Column Detection: Find the column that actually contains data
        def get_best_column(possible_names, df, preferred_near=None):
            found_cols = [c for c in df.columns if str(c).strip() in possible_names or 
                          any(str(c).strip().startswith(p + ".") for p in possible_names)]
            if not found_cols:
                # Fallback to loose match
                found_cols = [c for c in df.columns if any(p.lower() in str(c).lower() for p in possible_names)]
            
            if not found_cols: return None
            if len(found_cols) == 1: return found_cols[0]
            
            # If we have a preferred near column index, pick the one closest to it (after it)
            if preferred_near is not None:
                df_cols = list(df.columns)
                # Filter for columns that appear AFTER preferred_near
                after_cols = [c for c in found_cols if df_cols.index(c) > preferred_near]
                if after_cols:
                    return after_cols[0] # Pick the first one after the reference column

            # If multiple, pick the one with the most numeric/non-null data
            best = found_cols[0]
            max_val = -1
            for c in found_cols:
                count = df[c].apply(lambda x: pd.to_numeric(x, errors='coerce')).count()
                if count > max_val:
                    max_val = count
                    best = c
            return best

        actual_col = get_best_column(['Actual'], df)
        expected_col = get_best_column(['Expected'], df)
        forecasted_col = get_best_column(['Forecasted'], df)
        
        # Detect Expected Delta and %
        exp_idx = list(df.columns).index(expected_col) if expected_col in df.columns else None
        delta_col = get_best_column(['Delta', 'Difference'], df, preferred_near=exp_idx)
        perc_col = get_best_column(['%', 'Delta %', 'Performance'], df, preferred_near=exp_idx)
        
        # Detect Forecasted Delta and %
        fore_idx = list(df.columns).index(forecasted_col) if forecasted_col in df.columns else None
        f_delta_col = get_best_column(['Delta', 'Difference'], df, preferred_near=fore_idx)
        f_perc_col = get_best_column(['%', 'Delta %', 'Performance'], df, preferred_near=fore_idx)
        
        notes_col = get_best_column(['Notes', 'Comments', 'Reason', 'Faults', 'Service Requests', 'SR'], df)

        for _, row in df.iterrows():
            site = str(row.get('Site', 'Unknown')).strip()
            def clean_num(val):
                if pd.isna(val) or str(val).strip() in ['-', '', 'nan']: return 0.0
                if isinstance(val, (int, float)): return float(val)
                try:
                    s = str(val).replace(',', '').replace('$', '').strip()
                    return float(pd.to_numeric(s, errors='coerce'))
                except: return 0.0

            raw_actual = row.get(actual_col) if actual_col else 0.0
            raw_expected = row.get(expected_col) if expected_col else 0.0
            
            def is_missing(val):
                if pd.isna(val) or str(val).strip() in ['-', '', '0', '0.0']:
                    return True
                try:
                    return float(val) == 0.0
                except:
                    return False
            
            actual_missing = is_missing(raw_actual)
            expected_missing = is_missing(raw_expected)
            if "Paso" in site:
                print(f"[DEBUG-ROW] Site: {site}, RawActual: {repr(raw_actual)}, RawExpected: {repr(raw_expected)}, ActualMissing: {actual_missing}, ExpectedMissing: {expected_missing}")

            actual = clean_num(raw_actual)
            expected = clean_num(raw_expected)
            forecasted = clean_num(row.get(forecasted_col)) if forecasted_col else 0.0
            
            orig_delta = clean_num(row.get(delta_col)) if delta_col else 0.0
            f_orig_delta = clean_num(row.get(f_delta_col)) if f_delta_col else 0.0
            
            def get_perc(val):
                if pd.isna(val) or str(val).strip() in ['-', '']: return 0.0
                p = pd.to_numeric(val, errors='coerce') or 0.0
                if abs(p) < 1.1 and p != 0: p *= 100
                return p

            orig_perc = get_perc(row.get(perc_col))
            f_orig_perc = get_perc(row.get(f_perc_col))

            comp_delta = actual - expected
            comp_perf = (comp_delta / expected * 100) if expected != 0 else 0.0
            
            f_comp_delta = actual - forecasted
            f_comp_perf = (f_comp_delta / forecasted * 100) if forecasted != 0 else 0.0
            
            notes = str(row.get(notes_col)).strip() if notes_col and pd.notna(row.get(notes_col)) else ""

            results.append({
                "Site": site,
                "Actual": actual,
                "Actual Missing": actual_missing,
                "Expected": expected,
                "Expected Missing": expected_missing,
                "Forecasted": forecasted,
                "Forecasted Missing": is_missing(row.get(forecasted_col)),
                "Orig Delta": orig_delta,
                "Comp Delta": round(comp_delta, 2),
                "Orig %": round(orig_perc, 1),
                "Comp %": round(comp_perf, 1),
                "F Orig Delta": f_orig_delta,
                "F Comp Delta": round(f_comp_delta, 2),
                "F Orig %": round(f_orig_perc, 1),
                "F Comp %": round(f_comp_perf, 1),
                "Month": month_name,
                "File": os.path.basename(file_path),
                "Notes": notes,
                "Orig Notes": notes,
                "grammar_fixed": False
            })
        return results
    except Exception as e:
        print(f"[ERROR] {e}")
        return None

def analyze_file(file_path, month_name):
    """
    Core analysis function used by both CLI and API.
    Processes the file, recomputes metrics, flags anomalies, and generates suggestions.
    month_name can be a full name ('August'), a short name ('Aug'), or a raw sheet name ('Year to Date').
    """
    config = load_config()
    
    # Build reverse map: short name -> full name (e.g. 'Aug' -> 'August')
    reverse_map = {v: k for k, v in config['month_map'].items()}
    
    # If given a short name like 'Aug', convert to full name 'August'
    if month_name in reverse_map:
        resolved_month = reverse_map[month_name]
    elif month_name in config['month_map']:
        resolved_month = month_name
    else:
        # Raw sheet name like 'Year to Date', '1st Qtr' — pass it directly
        resolved_month = month_name
    
    results = process_individual_file(file_path, config, resolved_month)
    if not results:
        return None, None
    
    # Determine if this is an actual month sheet (vs quarter/YTD)
    monthly_names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    is_monthly_sheet = resolved_month in monthly_names
    
    save_to_db(results)

    # Statistical Model Loading
    try:
        model = joblib.load(MODEL_PATH)
        encoder = joblib.load(ENCODER_PATH)
        month_to_num = {
            "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
            "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12,
            "Q1": 13, "Q2": 14, "Q3": 15, "Q4": 16, "YTD": 17
        }
        month_num = month_to_num.get(resolved_month, 1) # Use resolved_month here
    except:
        model = None
        encoder = None
        month_num = 1

    # Baselines Loading
    try:
        with open(BASELINES_PATH, 'r') as f:
            site_baselines = json.load(f)
    except:
        site_baselines = {}

    # RAG Index Loading
    try:
        with open(RAG_INDEX_PATH, 'rb') as f:
            rag_index = pickle.load(f)
    except:
        rag_index = None

    # Quarters Summation Pre-calculation
    quarter_to_months = {
        "Q1": ["January", "February", "March"],
        "Q2": ["April", "May", "June"],
        "Q3": ["July", "August", "September"],
        "Q4": ["October", "November", "December"]
    }
    
    quarterly_ref_sums = {}
    if resolved_month in quarter_to_months:
        print(f"[QUARTER-CHECK] Aggregating monthly data for {resolved_month} ({quarter_to_months[resolved_month]})")
        for m in quarter_to_months[resolved_month]:
            # Translate full name "April" to sheet alias "Apr" using config
            sheet_alias = config['month_map'].get(m, m)
            print(f"  -> Reading monthly sheet: {sheet_alias}")
            m_data = process_individual_file(file_path, config, m)
            if m_data:
                print(f"    - Found {len(m_data)} rows")
                for row in m_data:
                    site_raw = row['Site']
                    if 'total' in site_raw.lower():
                        continue
                    norm_site = _normalize_for_compare(site_raw)
                    if norm_site not in quarterly_ref_sums:
                        quarterly_ref_sums[norm_site] = {'Actual': 0.0, 'Expected': 0.0, 'count': 0}
                    quarterly_ref_sums[norm_site]['Actual'] += row['Actual']
                    quarterly_ref_sums[norm_site]['Expected'] += row['Expected']
                    quarterly_ref_sums[norm_site]['count'] += 1
            else:
                print(f"  -> [WARNING] No data found in {sheet_alias} sheet")

    # Grammar Check Logic (Monthly sheets only)
    if is_monthly_sheet:
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            # Map futures to their respective indices in results
            future_to_idx = {}
            for i, r in enumerate(results):
                if r.get('Notes'):
                    future = executor.submit(fix_grammar, r['Notes'])
                    future_to_idx[future] = i
            
            for future in concurrent.futures.as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    corrected, changed = future.result()
                    if changed:
                        results[idx]['Notes'] = corrected
                        results[idx]['grammar_fixed'] = True
                except Exception as e:
                    print(f"[ERROR] Parallel fix_grammar failed for {results[idx].get('Site')}: {e}")

    mismatches = []
    # We will process suggestions in parallel as well
    suggestion_futures = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        for r in results:
            r['faults'] = [] # Reset faults for each run
            site_name = r['Site']
            
            # Math Mismatch Check (Both Expected and Forecasted)
            has_math_error_exp = abs(r['Comp Delta'] - r['Orig Delta']) > config.get('thresholds', {}).get('math_mismatch', 2.0)
            has_math_error_fore = abs(r['F Comp Delta'] - r['F Orig Delta']) > config.get('thresholds', {}).get('math_mismatch', 2.0)
            has_math_error = has_math_error_exp or has_math_error_fore
            
            # Quarters Formula Check (Sum of months must match)
            # (Checking Expected, as that's the primary audit value)
            has_quarterly_mismatch = False
            norm_site = _normalize_for_compare(site_name)
            if resolved_month in quarter_to_months and norm_site in quarterly_ref_sums:
                ref = quarterly_ref_sums[norm_site]
                mismatch_thresh = config.get('thresholds', {}).get('math_mismatch', 2.0)
                if abs(r['Actual'] - ref['Actual']) > mismatch_thresh or abs(r['Expected'] - ref['Expected']) > mismatch_thresh:
                    has_quarterly_mismatch = True
                    corr_delta = ref['Actual'] - ref['Expected']
                    corr_perf = (corr_delta / ref['Expected'] * 100) if ref['Expected'] != 0 else 0.0
                    r['quarter_correction'] = f"Expected: {ref['Expected']:,.0f}, Delta: {corr_delta:,.0f}, Perf: {corr_perf:.1f}%"
                    print(f"[QUARTER-FAIL] {site_name}: Sheet({r['Actual']}/{r['Expected']}) vs MonthsSum({ref['Actual']}/{ref['Expected']})")
            
            # Bad Performance Check (DELTA ALERT) - Check both
            max_perf = config.get('thresholds', {}).get('max_perf', 100.0)
            is_bad_perf_exp = round(abs(r['Comp %']), 1) >= max_perf
            is_bad_perf_fore = round(abs(r['F Comp %']), 1) >= max_perf
            is_bad_perf = is_bad_perf_exp or is_bad_perf_fore
            
            # Missing Notes Check — only for monthly sheets
            has_no_notes = False
            if is_monthly_sheet:
                # Use Expected % for the threshold
                has_no_notes = (r['Comp %'] <= -10.0) and (not r['Notes'] or str(r['Notes']).lower() in ['nan', 'none', '-', 'service requests', '/'])
            
            # Missing Values Check - Check all three
            has_missing_values = r.get('Actual Missing') or r.get('Expected Missing') or r.get('Forecasted Missing')
            
            # Statistical Anomaly Check (Historical Baseline)
            is_stat_anomaly = False
            
            # 1. Primary: Check against site-month specific historical mean/std
            if site_name in site_baselines and resolved_month in site_baselines[site_name]:
                stats = site_baselines[site_name][resolved_month]
                threshold = stats['mean'] - (2 * stats['std'])
                if r['Comp %'] < threshold and r['Comp %'] < stats['mean'] - 10.0:
                    is_stat_anomaly = True
            
            # 2. Simple Performance-based Anomaly (The "Excel Red Text" Rule: -10% to -99%)
            if not is_stat_anomaly:
                if -99.9 <= r['Comp %'] <= -10.0:
                    is_stat_anomaly = True
            
            # 3. Fallback: IsolationForest
            if not is_stat_anomaly and model and encoder:
                try:
                    if site_name in encoder.classes_:
                        site_id = encoder.transform([site_name])[0]
                        features = [[site_id, month_num, r['Actual'], r['Expected'], r['Comp Delta'], r['Comp %']]]
                        pred = model.predict(features)
                        if pred[0] == -1 and r['Comp %'] < -5.0:
                            is_stat_anomaly = True
                except:
                    is_stat_anomaly = False

            if has_math_error or is_bad_perf or has_no_notes or is_stat_anomaly or has_missing_values or has_quarterly_mismatch:
                if has_math_error: 
                    r['faults'].append("MATH")
                    reasons = []
                    if has_math_error_exp: reasons.append(f"Exp Delta should be {r['Comp Delta']:,.0f}")
                    if has_math_error_fore: reasons.append(f"Fore Delta should be {r['F Comp Delta']:,.0f}")
                    r['math_correction'] = " | ".join(reasons)
                
                if has_quarterly_mismatch: 
                    r['faults'].append("QUARTERS_FORMULA_CHECK")
                    # r['quarter_correction'] is already set above
                
                if is_bad_perf: r['faults'].append("DELTA_ALERT")
                if has_missing_values: r['faults'].append("MISSING_VALUES")
                if has_no_notes: r['faults'].append("MISSING_NOTES")
                if is_stat_anomaly: r['faults'].append("HISTORICAL_COMPARISION")
                
                # Use RAG + LLM for suggestions only on monthly sheets
                # For Expected=0 (MISSING_VALUES), use the specific user-requested one-liner
                if is_monthly_sheet and (has_no_notes or has_missing_values):
                    if r.get('Expected Missing'):
                        r['suggestion'] = "Check the weather station to verify GHI/POA sensor connectivity and data integrity."
                    else:
                        def get_suggestion_with_ctx(record):
                            rag_ctx = get_rag_suggestion(rag_index, record['Site'], record['Comp %'])
                            extra_ctx = ""
                            if record.get("Actual Missing"): extra_ctx += "Actual data is MISSING. "
                            return get_llm_suggestion(record['Site'], record['Comp %'], f"{extra_ctx}{rag_ctx if rag_ctx else ''}", record.get('Notes'))

                        future = executor.submit(get_suggestion_with_ctx, r)
                        suggestion_futures.append((future, r))

                mismatches.append(r)
                save_anomaly_to_db(r['db_id'], "/".join(r['faults']))

        # Wait for all suggestions to finish
        for future, record in suggestion_futures:
            try:
                sug = future.result()
                if sug: record['suggestion'] = sug
            except Exception as e:
                print(f"[ERROR] Parallel get_llm_suggestion failed for {record.get('Site')}: {e}")

    # Save to json for reference

    # Save to json for reference
    os.makedirs('data', exist_ok=True)
    with open('data/flagged_sites.json', 'w') as f:
        json.dump(mismatches, f, indent=4)
        
    return results, mismatches

def analyze_all_months(file_path):
    """
    Processes ALL month sheets in the Excel file.
    Returns a dict keyed by month name with results and mismatches for each.
    """
    config = load_config()
    xl = pd.ExcelFile(file_path)
    available_sheets = xl.sheet_names
    
    all_data = {}
    available_months = []
    
    for month_name, sheet_prefix in config['month_map'].items():
        # Check if sheet exists
        target_sheet = None
        if sheet_prefix in available_sheets:
            target_sheet = sheet_prefix
        else:
            matches = [s for s in available_sheets if s.startswith(sheet_prefix)]
            if matches:
                target_sheet = matches[0]
        
        if not target_sheet:
            continue
        
        try:
            results, mismatches = analyze_file(file_path, month_name)
            if results:
                available_months.append(month_name)
                all_data[month_name] = {
                    "results": results,
                    "mismatches": mismatches
                }
        except Exception as e:
            print(f"[analyze_all_months] Error processing {month_name}: {e}")
            continue
    
    return all_data, available_months

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, required=True)
    parser.add_argument("--month", type=str, required=True)
    args = parser.parse_args()

    results, mismatches = analyze_file(args.file, args.month)
    if not results: return

    # Colors for terminal
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"

    # 1. FULL AUDIT TABLE
    print("\n" + "="*160)
    print(f" FULL RECOMPUTATION AUDIT: {args.month} - {os.path.basename(args.file)}")
    print("="*160)
    
    header = f"{'Site Name':<35} | {'Actual':<10} | {'Expected':<10} | {'Sheet Delta':<12} | {'Rec Delta':<12} | {'Sheet %':<8} | {'Rec %':<8}"
    print(header)
    print("-" * len(header))
    
    for r in results:
        color = ""
        flag_text = ""
        if 'faults' in r:
            if "MATH" in r['faults']: color = RED
            else: color = YELLOW
            
            flag_text = f" [{ '/'.join(r['faults']) }]"
            if 'suggestion' in r:
                flag_text += f" -> SUGGESTION: {r['suggestion']}"

        actual_disp = f"{r['Actual']:>10,.0f}" if not r.get('Actual Missing') else " [MISSING] "
        expected_disp = f"{r['Expected']:>10,.0f}" if not r.get('Expected Missing') else " [MISSING] "
        
        print(f"{color}{r['Site'][:34]:<35} | {actual_disp} | {expected_disp} | {r['Orig Delta']:>12,.0f} | {r['Comp Delta']:>12,.0f} | {r['Orig %']:>7.1f}% | {r['Comp %']:>7.1f}%{flag_text}{RESET}")

    # 2. MISMATCH TABLE
    print("\n" + "!"*160)
    print(" !!! MISMATCHED & FLAGGED RECORDS ONLY !!!")
    print("!"*160)
    
    if not mismatches:
        print(" [OK] No mismatches, performance alerts, or statistical anomalies found.")
    else:
        header_fault = header + " | Fault / Suggestion"
        print(header_fault)
        print("-" * len(header_fault))
        for m in mismatches:
            color = RED if "MATH" in m['faults'] else YELLOW
            info = "/".join(m['faults'])
            if 'suggestion' in m:
                info += f" (Sug: {m['suggestion'][:60]}...)"
            
            actual_disp = f"{m['Actual']:>10,.0f}" if not m.get('Actual Missing') else " [MISSING] "
            expected_disp = f"{m['Expected']:>10,.0f}" if not m.get('Expected Missing') else " [MISSING] "
            
            print(f"{color}{m['Site'][:34]:<35} | {actual_disp} | {expected_disp} | {m['Orig Delta']:>12,.0f} | {m['Comp Delta']:>12,.0f} | {m['Orig %']:>7.1f}% | {m['Comp %']:>7.1f}% | {info}{RESET}")

if __name__ == "__main__":
    main()