from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
import logging, traceback
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
import json
from io import BytesIO
import os

from project_ingestion import ingest_project
from analysis import analyze_project
from refactor import refactor_files
from report import generate_report

app = FastAPI(title="Haskell Refactoring and Analysis API", version="1.0.0")

# CORS settings to allow React frontend
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class IngestResponse(BaseModel):
    source_files: List[str]
    project_dir: str

class AnalyzeRequest(BaseModel):
    project_dir: str
    source_files: List[str]

class RefactorRequest(BaseModel):
    project_dir: str
    analysis_results: dict

class ReportRequest(BaseModel):
    analysis_results: dict
    project_name: Optional[str] = "ExampleProject"

# @app.post("/ingest", response_model=IngestResponse)
@app.post("/ingest")
async def ingest(
    uploaded_zip: Optional[UploadFile] = File(None),
    repo_url: Optional[str] = Form(None),
    branch: str = Form("main")
):
    # try:
    #     source_files, project_dir = ingest_project(
    #         uploaded_zip=uploaded_zip,
    #         repo_url=repo_url,
    #         branch=branch
    #     )
    # except Exception as e:
    #     raise HTTPException(status_code=400, detail=str(e))

    zip_buffer = None
    if uploaded_zip:
        contents = await uploaded_zip.read()
        zip_buffer = BytesIO(contents)
    
    try:
        source_files, project_dir = ingest_project(
            uploaded_zip=zip_buffer,
            repo_url=repo_url,
            branch=branch
         )
        if source_files:
            analysis_results = analyze_project(project_dir, source_files)
            # return analysis_results
            pre_refactor_overall = analysis_results["pre_refactor"]["overall"]
            refactored_results = refactor_files(analysis_results, project_dir)

            analysis_results["post_refactor"] = refactored_results
            final_report = generate_report(analysis_results, project_name="ProjectName")
            # Save to a JSON file
            with open("project_result/project_result.json", "w", encoding="utf-8") as f:
                # json.dump(final_report, f, indent=2)
                f.write(final_report)
            # print(type(final_report))
            return final_report
            
            
    except Exception as e:
        logging.error("Ingestion failed:\n%s", traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))
    return {"source_files": source_files, "project_dir": project_dir}
    




@app.get("/result_json")
def get_project_result():
    file_path = "project_result/project_result.json"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/json")
    return {"error": "File not found"}

@app.get("/file_detail")
def get_project_result():
    file_path = "project_result/project_result.json"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/json")
    return {"error": "File not found"}


@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    try:
        return analyze_project(request.project_dir, request.source_files)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/refactor")
async def refactor(request: RefactorRequest):
    try:
        return refactor_files(request.analysis_results, request.project_dir)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/report")
async def report(request: ReportRequest):
    try:
        report_json = generate_report(request.analysis_results, project_name=request.project_name)
        return JSONResponse(content=json.loads(report_json))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok"}
