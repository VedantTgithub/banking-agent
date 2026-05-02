from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import datetime
import os
import sys

# Add the parent directory to sys.path to import agent modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from tools.ocr_tool import extract_text_from_uploaded_file
from agent.graph import loan_agent_app
from agent.state import AgentState

app = FastAPI(title="Loan Underwriting API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def read_root():
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/underwrite")
async def underwrite(
    applicant_name: str = Form(...),
    pan_number: str = Form(...),
    dob: str = Form(...),
    loan_amount: float = Form(...),
    loan_type: str = Form(...),
    loan_tenure: int = Form(...),
    loan_purpose: str = Form(...),
    annual_income: float = Form(...),
    employment_type: str = Form(...),
    employer_name: str = Form(...),
    years_at_employer: int = Form(...),
    existing_emi: float = Form(...),
    active_loans: int = Form(...),
    loan_default: str = Form(...),
    collateral_type: str = Form(...),
    collateral_value: float = Form(...),
    collateral_description: str = Form(...),
    document: UploadFile = File(...)
):
    # 1. OCR Extraction
    try:
        # Wrap the file in a way pypdf can read it
        doc_text = extract_text_from_uploaded_file(document.file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process PDF: {str(e)}")

    if not doc_text:
        raise HTTPException(status_code=400, detail="Could not extract text from the PDF.")

    # 2. Initial State
    state: AgentState = {
        "application_id"    : f"APP-{datetime.datetime.now().strftime('%Y%m%d%H%M')}",
        "thread_id"         : "thread-api",
        "applicant_name"    : applicant_name.strip(),
        "pan_number"        : pan_number.strip(),
        "dob"               : dob,
        "loan_amount"       : float(loan_amount),
        "loan_type"         : loan_type,
        "loan_tenure"       : int(loan_tenure),
        "loan_purpose"      : loan_purpose.strip(),
        "annual_income"     : float(annual_income),
        "employment_type"   : employment_type,
        "employer_name"     : employer_name.strip(),
        "years_at_employer" : int(years_at_employer),
        "existing_emi"      : float(existing_emi),
        "active_loans"      : int(active_loans),
        "loan_default"      : loan_default,
        "collateral_type"   : collateral_type,
        "collateral_value"  : float(collateral_value),
        "collateral_description": collateral_description.strip(),
        "uploaded_doc_text" : doc_text,
        "doc_verified"      : False,
        "missing_docs"      : [],
        "doc_flags"         : [],
        "extracted_income"  : 0.0,
        "extracted_name"    : "",
        "bureau_score"      : 0,
        "dti_ratio"         : 0.0,
        "foir"              : 0.0,
        "income_stability"  : "",
        "credit_flags"      : [],
        "risk_tier"         : "",
        "ltv_ratio"         : 0.0,
        "collateral_score"  : 0.0,
        "sector_risk"       : "",
        "risk_flags"        : [],
        "compliance_passed" : False,
        "violations"        : [],
        "applicable_rules"  : [],
        "policy_notes"      : "",
        "decision"          : "",
        "confidence"        : 0.0,
        "decision_report"   : "",
        "recommended_terms" : {},
        "current_node"      : "start",
        "errors"    : [],
        "messages"  : [],
    }

    # 3. Graph Execution
    try:
        # Use invoke instead of stream for a single API response
        # Or we could use stream and yield events, but simple invoke is better for standard REST
        final_state = loan_agent_app.invoke(state, config={"configurable": {"thread_id": state["application_id"]}})
        return final_state
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
