import pandas as pd
import os
import sqlite3
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Setup Database Paths
DB_PATH = "data/solar_production.db"
RAG_INDEX_PATH = "data/rag_index_2024.pkl"

def extract_notes_from_db():
    """Fetches all valid notes from the production_records database."""
    print(" [INFO] Connecting to database to extract notes...")
    try:
        conn = sqlite3.connect(DB_PATH)
        query = """
            SELECT site_name, comp_perf, notes 
            FROM production_records 
            WHERE notes IS NOT NULL 
              AND notes NOT IN ('', 'nan', 'None', '-', 'service requests')
              AND length(notes) > 5
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        all_data = []
        for _, row in df.iterrows():
            all_data.append({
                "site": row['site_name'],
                "perf": round(float(row['comp_perf']), 1),
                "note": row['notes']
            })
        print(f" [SUCCESS] Extracted {len(all_data)} valid notes from DB.")
        return all_data
    except Exception as e:
        print(f" [ERROR] Failed to extract from DB: {e}")
        return []

def build_tfidf_rag(data):
    """Creates a local RAG index using TF-IDF."""
    if not data:
        print("No data to index.")
        return

    # Combine Site, Perf, and Note for semantic context
    documents = [f"Site: {d['site']} | Perf: {d['perf']}% | Note: {d['note']}" for d in data]
    
    print(f"Building TF-IDF Index for {len(documents)} snippets...")
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(documents)
    
    # Save the index
    idx_data = {
        "vectorizer": vectorizer,
        "tfidf_matrix": tfidf_matrix,
        "raw_data": data
    }
    
    os.makedirs(os.path.dirname(RAG_INDEX_PATH), exist_ok=True)
    with open(RAG_INDEX_PATH, 'wb') as f:
        pickle.dump(idx_data, f)
    
    print(f"Success! RAG Index updated and saved to {RAG_INDEX_PATH}")

if __name__ == "__main__":
    notes = extract_notes_from_db()
    if notes:
        build_tfidf_rag(notes)
    else:
        print("No valid notes found in database.")
