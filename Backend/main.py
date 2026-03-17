# main.py

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from datetime import datetime

# Supabase
from supabase import create_client, Client

# Import analysis functions
from scripts.ai_notes import  analyze_file as analyze_ainotes
from missing_detection import analyze_missing_values
from anomaly_detection import analyze_file as analyze_anomalies
from formula_detection import analyze_formula_errors

# -----------------------------
# Supabase Configuration
# -----------------------------
SUPABASE_URL = "https://qvdzlwzjodciqsvizbgf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF2ZHpsd3pqb2RjaXFzdml6YmdmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMxMTYyNzAsImV4cCI6MjA4ODY5MjI3MH0.2mqj_-ZL0A2PiuR-sOkvL2a347iFibkRqMZi-ABAqRo"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------
# Paths
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# -----------------------------
# App Initialization
# -----------------------------
app = FastAPI(
    title="AMRESCO Automation Backend",
    version="1.0.0"
)

# -----------------------------
# CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# -----------------------------
# Health Check
# -----------------------------
@app.get("/")
def health_check():
    return {"status": "AMRESCO backend running"}

# -----------------------------
# Upload File
# -----------------------------
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    if not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only XLSX files allowed")

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    try:
        with open(file_path, "wb") as f:
            f.write(await file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "message": "File uploaded successfully",
        "filename": file.filename
    }

# -----------------------------
# List Files
# -----------------------------
@app.get("/files")
def get_uploaded_files():

    files = []
    for filename in os.listdir(UPLOAD_DIR):
        path = os.path.join(UPLOAD_DIR, filename)
        if os.path.isfile(path):
            files.append({
                "name": filename,
                "size_kb": round(os.path.getsize(path) / 1024, 2),
                "uploaded_at": datetime.fromtimestamp(
                    os.path.getctime(path)
                ).strftime("%Y-%m-%d %H:%M:%S")
            })

    return files

# -----------------------------
# Analyze File
# -----------------------------
@app.get("/analyze/{filename}")
def analyze_excel_file(filename: str):

    file_path = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        # -----------------------------
        # Missing values analysis
        # -----------------------------
        missing_result = analyze_missing_values(file_path)
        missing_issues = missing_result.get("issues", [])

        # -----------------------------
        # Anomaly detection
        # -----------------------------
        anomaly_result = analyze_anomalies(file_path)

        # -----------------------------
        # Formula analysis
        # -----------------------------
        formula_result = analyze_formula_errors(file_path)
        formula_issues = formula_result.get("issues", [])
        formula_error_count = formula_result.get("formula_errors", len(formula_issues))
        
         # -----------------------------
        # ✅ AI NOTES (NEW)
        # -----------------------------
        # You can pass month dynamically later
        ainotes_results, ainotes_mismatches = analyze_ainotes(file_path, "August")

        # 🔥 CLEAN Gemini errors (IMPORTANT)
        for r in ainotes_mismatches or []:
            if "suggestion" in r and str(r["suggestion"]).startswith("Error:"):
                r["suggestion"] = "Investigate performance drop using historical trends and site inspection."


        # -----------------------------
        # Summary calculations
        # -----------------------------
        total_cells = missing_result.get("total_cells", 0)
        missing_values = len(missing_issues)
        missing_percentage = missing_result.get("percentage", 0)
        abnormal_values_count = len([
            a for a in anomaly_result
            if a.get("issue_type") == "abnormal value"
        ])
        underperform_sites_count = len(set([
            a.get("site")
            for a in anomaly_result
            if a.get("issue_type") == "underperforming site"
        ]))

        # -----------------------------
        # Save to Supabase
        # -----------------------------
        supabase.table("analysis_results").insert({
            "filename": filename,
            "total_cells": total_cells,
            "missing_values": missing_values,
            "missing_percentage": missing_percentage,
            "abnormal_values": abnormal_values_count,
            "underperforming_sites": underperform_sites_count,
            "formula_errors": formula_error_count
        }).execute()

        # -----------------------------
        # API Response
        # -----------------------------
        return {
            "message": "Analysis completed",
            "summary": {
                "total_cells": total_cells,
                "missing_values": missing_values,
                "percentage": missing_percentage,
                "abnormal_values": abnormal_values_count,
                "underperforming_sites": underperform_sites_count,
                "formula_errors": formula_error_count
            },
            "missing": missing_issues,
            "anomalies": anomaly_result,
            "formulas": formula_issues
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))