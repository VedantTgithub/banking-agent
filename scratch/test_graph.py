
import os
import sys
import datetime

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.graph import loan_agent_app
from agent.state import AgentState

state: AgentState = {
    "application_id"    : f"TEST-{datetime.datetime.now().strftime('%Y%m%d%H%M')}",
    "thread_id"         : "test-thread",
    "applicant_name"    : "Test User",
    "pan_number"        : "ABCDE1234F",
    "dob"               : "1990-01-01",
    "loan_amount"       : 500000.0,
    "loan_type"         : "Personal",
    "loan_tenure"       : 5,
    "loan_purpose"      : "Test",
    "annual_income"     : 1200000.0,
    "employment_type"   : "Salaried",
    "employer_name"     : "Test Corp",
    "years_at_employer" : 2,
    "existing_emi"      : 0.0,
    "active_loans"      : 0,
    "loan_default"      : "No",
    "collateral_type"   : "None",
    "collateral_value"  : 0.0,
    "collateral_description": "N/A",
    "uploaded_doc_text" : "Sample salary slip text. Income: 100000 per month.",
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

try:
    print("Invoking graph...")
    result = loan_agent_app.invoke(state, config={"configurable": {"thread_id": "test-id"}})
    print("Success!")
    print(f"Decision: {result.get('decision')}")
except Exception as e:
    import traceback
    print("Error during graph execution:")
    traceback.print_exc()
