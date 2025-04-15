from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import os
import json
import glob
from fastapi import HTTPException


app = FastAPI()

REPORT_FOLDER = "test_reports"

@app.get("/")
def read_root():
    return {"message": "Welcome to the AI Interview Report API!"}

@app.get("/report")
def get_report(meeting_id: str = Query(..., description="Meeting ID without timestamp")):
    # Get all files matching the pattern
    files = glob.glob(os.path.join(REPORT_FOLDER, f"{meeting_id}_*_report.json"))
    if not files:
        return JSONResponse(status_code=404, content={"error": "Report not found."})

    # Get the latest report by sorting with timestamp
    latest_file = sorted(files)[-1]
    with open(latest_file, "r") as f:
        data = json.load(f)
    
    return data

@app.get("/all_reports")
def list_all_reports():
    files = glob.glob(os.path.join(REPORT_FOLDER, "*_report.json"))
    reports = []
    for file in files:
        with open(file, "r") as f:
            report = json.load(f)
            reports.append({
                "filename": os.path.basename(file),
                "summary": report.get("candidate_report", {}).get("summary", {}),
                "verdict": report.get("candidate_report", {}).get("verdict")
            })
    return reports

@app.get("/report/latest")
def get_latest_report():
    report_files = glob.glob(os.path.join(REPORT_FOLDER, "*_report.json"))
    if not report_files:
        raise HTTPException(status_code=404, detail="No reports found.")

    latest_file = max(report_files, key=os.path.getctime)

    with open(latest_file, "r") as f:
        report_data = json.load(f)

    return JSONResponse(content=report_data["candidate_report"])

