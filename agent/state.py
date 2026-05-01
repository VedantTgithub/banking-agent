from typing import TypedDict, Optional, List, Dict, Any

class AgentState(TypedDict):

    # ── Application identifiers ──────────────────────────────
    application_id: str
    thread_id: str

    # ── Raw input from applicant ─────────────────────────────
    applicant_name: str
    pan_number: str
    dob: str
    loan_amount: float
    loan_type: str                # "Home" | "Personal" | "Business" | "Vehicle"
    loan_tenure: int
    loan_purpose: str
    annual_income: float
    employment_type: str          # "Salaried" | "Self-Employed" | "Business Owner"
    employer_name: str
    years_at_employer: int
    existing_emi: float
    active_loans: int
    loan_default: str             # "Yes" | "No"
    collateral_type: str          # "Property" | "Gold" | "FD" | "Vehicle" | "None"
    collateral_value: float
    collateral_description: str
    uploaded_doc_text: str        # raw text extracted from uploaded PDF

    # ── Node 1 outputs: Document Verification ───────────────
    doc_verified: bool
    missing_docs: List[str]
    doc_flags: List[str]
    extracted_income: float
    extracted_name: str

    # ── Node 2 outputs: Credit Scoring ──────────────────────
    bureau_score: int
    dti_ratio: float
    foir: float
    income_stability: str         # "stable" | "unstable" | "moderate"
    credit_flags: List[str]

    # ── Node 3 outputs: Risk Assessment ─────────────────────
    risk_tier: str                # "low" | "medium" | "high" | "very_high"
    ltv_ratio: float
    collateral_score: float
    sector_risk: str              # "low" | "medium" | "high"
    risk_flags: List[str]

    # ── Node 4 outputs: Policy Compliance ───────────────────
    compliance_passed: bool
    violations: List[str]
    applicable_rules: List[str]
    policy_notes: str

    # ── Node 5 outputs: Decision Generation ─────────────────
    decision: str                 # "APPROVED" | "REJECTED" | "ESCALATED"
    confidence: float             # 0.0 to 1.0
    decision_report: str
    recommended_terms: Dict[str, Any]

    # ── Shared across all nodes ──────────────────────────────
    current_node: str
    errors: List[str]
    messages: List[Dict[str, str]]  # LangChain message history