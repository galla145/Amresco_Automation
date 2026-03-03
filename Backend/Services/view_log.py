import sqlite3
import pandas as pd
import os

DB_PATH = "data/solar_production.db"

def show_anomaly_log():
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    
    # This query joins the production records with the flags to show you a clean "Log"
    query = """
    SELECT 
        p.month as Month,
        p.site_name as Site,
        p.actual as Actual,
        p.expected as Expected,
        p.comp_perf as 'Perf %',
        f.fault_type as 'Fault Type',
        p.file_source as 'Source File',
        p.timestamp as 'Detection Time'
    FROM production_records p
    INNER JOIN flagged_anomalies f ON p.id = f.record_id
    ORDER BY p.timestamp DESC
    """
    
    try:
        df = pd.read_sql_query(query, conn)
        
        print("\n" + "="*140)
        print(" " * 50 + "SOLAR ANOMALY DATABASE LOG")
        print("="*140)
        
        if df.empty:
            print("\n   [INFO] No anomalies found in the database yet.")
        else:
            # Format numbers for readability
            df['Actual'] = df['Actual'].map('{:,.0f}'.format)
            df['Expected'] = df['Expected'].map('{:,.0f}'.format)
            df['Perf %'] = df['Perf %'].map('{:.1f}%'.format)
            
            print(df.to_string(index=False))
            
        print("="*140)
        print(f"Total anomalies in history: {len(df)}")
        
    except Exception as e:
        print(f"[ERROR] Could not read log: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    show_anomaly_log()
