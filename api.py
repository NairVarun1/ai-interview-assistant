from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import os
import json

app = FastAPI()
REPORTS_DIR = "test_reports"  # Folder where JSON reports are saved

@app.get("/")
def read_root():
    return {"message": "API is working. Try /test_reports/test_report.json"}

@app.get("/report/test_report")
def get_report(filename: str):
    file_path = os.path.join(REPORTS_DIR, f"{filename}.json")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report not found")

    with open(file_path, "r") as file:
        data = json.load(file)

    return JSONResponse(content=data)
