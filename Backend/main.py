from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from datetime import datetime
import pandas as pd

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
# CORS (Frontend Access)
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # In production, restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Health Check
# -----------------------------
@app.get("/")
def health_check():
    return {"status": "AMRESCO backend running"}

# -----------------------------
# Upload XLSX File
# -----------------------------
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    if not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=400,
            detail="Only XLSX files are allowed"
        )

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    try:
        with open(file_path, "wb") as f:
            f.write(await file.read())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"File upload failed: {str(e)}"
        )

    return {
        "message": "File uploaded successfully",
        "filename": file.filename
    }

# -----------------------------
# List Uploaded Files
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
# Analyze Missing Values
# -----------------------------
@app.get("/analyze/{filename}")
def analyze_file(filename: str):

    file_path = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        xls = pd.ExcelFile(file_path)
        sheets = xls.sheet_names
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    total_missing = 0
    total_entries = 0

    empty_count = 0
    na_count = 0
    zero_count = 0

    sheet_summary = []
    sheet_details = {}

    for sheet in sheets:
        df = pd.read_excel(file_path, sheet_name=sheet)

        sheet_total = df.size
        total_entries += sheet_total

        # Detect Empty Cells
        empty_cells = (df == "").sum().sum()
        empty_count += int(empty_cells)

        # Detect N/A values
        na_cells = df.isin(["N/A", "NA", "n/a"]).sum().sum()
        na_count += int(na_cells)

        # Detect Zero values
        zero_cells = (df == 0).sum().sum()
        zero_count += int(zero_cells)

        # Combined missing logic
        missing_mask = (
            (df == "") |
            (df.isin(["N/A", "NA", "n/a"])) |
            (df == 0)
        )

        sheet_missing = missing_mask.sum().sum()
        total_missing += int(sheet_missing)

        sheet_summary.append({
            "sheet_name": sheet,
            "total_entries": int(sheet_total),
            "missing_values": int(sheet_missing)
        })

        # Rows containing missing values
        missing_rows = df[missing_mask.any(axis=1)]

        sheet_details[sheet] = (
            missing_rows
            .fillna("-")
            .astype(str)
            .to_dict(orient="records")
        )

    percent_incomplete = (
        round((total_missing / total_entries) * 100, 1)
        if total_entries > 0 else 0
    )

    return {
        "summary_cards": {
            "total_sheets": len(sheets),
            "total_missing": total_missing,
            "percent_incomplete": percent_incomplete,
            "filled_entries": total_entries - total_missing
        },
        "breakdown": {
            "empty_cells": empty_count,
            "na_values": na_count,
            "zero_values": zero_count
        },
        "sheet_summary": sheet_summary,
        "sheet_details": sheet_details
    }