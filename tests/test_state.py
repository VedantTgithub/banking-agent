import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.state import AgentState
from memory.checkpointer import get_checkpointer

def test_state_structure():
    # Create a dummy state that matches AgentState
    dummy_state: AgentState = {
        "application_id": "LOAN_001",
        "thread_id": "thread_001",
        "applicant_name": "Rahul Sharma",
        "pan_number": "ABCDE1234F",
        "dob": "1990-01-01",
        "loan_amount": 5000000.0,       # 50 lakhs
        "loan_type": "Home",
        "loan_tenure": 20,
        "loan_purpose": "Buying a new flat",
        "annual_income": 1200000.0,     # 12 LPA
        "employment_type": "Salaried",
        "employer_name": "Tech Corp",
        "years_at_employer": 5,
        "existing_emi": 10000.0,
        "active_loans": 1,
        "loan_default": "No",
        "collateral_type": "Property",
        "collateral_value": 6000000.0,
        "collateral_description": "2BHK flat in Mumbai",
        "uploaded_doc_text": "Sample extracted text from salary slip",

        # Node 1 outputs (empty for now)
        "doc_verified": False,
        "missing_docs": [],
        "doc_flags": [],
        "extracted_income": 0.0,
        "extracted_name": "",

        # Node 2 outputs (empty for now)
        "bureau_score": 0,
        "dti_ratio": 0.0,
        "foir": 0.0,
        "income_stability": "",
        "credit_flags": [],

        # Node 3 outputs (empty for now)
        "risk_tier": "",
        "ltv_ratio": 0.0,
        "collateral_score": 0.0,
        "sector_risk": "",
        "risk_flags": [],

        # Node 4 outputs (empty for now)
        "compliance_passed": False,
        "violations": [],
        "applicable_rules": [],
        "policy_notes": "",

        # Node 5 outputs (empty for now)
        "decision": "",
        "confidence": 0.0,
        "decision_report": "",
        "recommended_terms": {},

        # Shared
        "current_node": "start",
        "errors": [],
        "messages": []
    }

    print("✅ AgentState created successfully")
    print(f"   Application ID : {dummy_state['application_id']}")
    print(f"   Applicant      : {dummy_state['applicant_name']}")
    print(f"   Loan Amount    : ₹{dummy_state['loan_amount']:,.0f}")
    print(f"   Loan Type      : {dummy_state['loan_type']}")
    print(f"   Annual Income  : ₹{dummy_state['annual_income']:,.0f}")
    print(f"   Employment     : {dummy_state['employment_type']}")
    return dummy_state


def test_checkpointer():
    checkpointer = get_checkpointer()
    print("✅ Checkpointer created successfully")
    print(f"   Type : {type(checkpointer).__name__}")
    return checkpointer


if __name__ == "__main__":
    print("\n── Testing AgentState ──────────────────────────")
    state = test_state_structure()

    print("\n── Testing Checkpointer ────────────────────────")
    cp = test_checkpointer()

    print("\n🎉 Step 1 complete — state and memory are ready!")