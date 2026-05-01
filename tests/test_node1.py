import sys
import os
from dotenv import load_dotenv

# Ensure we can import from the project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables (like HUGGINGFACEHUB_API_TOKEN) from .env
load_dotenv()

from agent.state import AgentState
from agent.nodes.document_verification import run

def test_node_1():
    print("Starting Test for Node 1: Document Verification")
    
    # 1. Create a dummy state with simulated PDF text
    dummy_text = """
    EMPLOYEE SALARY SLIP
    Month: March 2026
    
    Employee Name: Vedant
    Annual CTC: 1200000
    Bank: HDFC Bank
    """
    
    state: AgentState = {
        "application_id": "TEST-001",
        "thread_id": "thread-1",
        "applicant_name": "Vedant",
        "annual_income": 1200000.0,
        "loan_amount": 500000.0,
        "loan_type": "personal",
        "employment_type": "salaried",
        "existing_emi": 0.0,
        "collateral_description": "",
        "uploaded_doc_text": dummy_text,
        
        # We don't need the rest for Node 1, but we satisfy the TypedDict
        "doc_verified": False,
        "missing_docs": [],
        "doc_flags": [],
        "extracted_income": 0.0,
        "extracted_name": "",
        "bureau_score": 0,
        "dti_ratio": 0.0,
        "foir": 0.0,
        "income_stability": "",
        "credit_flags": [],
        "risk_tier": "",
        "ltv_ratio": 0.0,
        "collateral_score": 0.0,
        "sector_risk": "",
        "risk_flags": [],
        "compliance_passed": False,
        "violations": [],
        "applicable_rules": [],
        "policy_notes": "",
        "decision": "",
        "confidence": 0.0,
        "decision_report": "",
        "recommended_terms": {},
        "current_node": "start",
        "errors": [],
        "messages": []
    }
    
    print(f"\nSimulated PDF Text Provided to Node:\n{dummy_text}")
    print("Invoking Node 1 (Sending prompt to Hugging Face LLM...)\n")
    
    # 2. Run the node
    result = run(state)
    
    # 3. Print the results
    print("\n--- Extraction Results ---")
    for key, value in result.items():
        print(f"  {key}: {value}")
        
    print("\nTest Complete!")

if __name__ == "__main__":
    test_node_1()
