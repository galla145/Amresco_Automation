import sqlite3
import os

DB_PATH = "data/solar_production.db"

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table for all production records
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
        notes TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Table for flagged anomalies/mismatches
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS flagged_anomalies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_id INTEGER,
        fault_type TEXT, -- MATH, STAT, DATA
        is_resolved INTEGER DEFAULT 0,
        FOREIGN KEY (record_id) REFERENCES production_records(id)
    )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
