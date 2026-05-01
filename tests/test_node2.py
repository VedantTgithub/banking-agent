"""
tests/test_node2.py
Unit tests for Node 2 — Credit Scoring.

Run from the loan_underwriting_agent directory:
    python -m tests.test_node2
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.risk_calculator import (
    calculate_proposed_emi,
    calculate_dti,
    calculate_foir,
    assess_income_stability,
    mock_bureau_score,
)

# ─────────────────────────────────────────────────────────────────────────────
# Helper: build a minimal AgentState for Node 2
# ─────────────────────────────────────────────────────────────────────────────
def make_state(**overrides) -> dict:
    base = {
        "application_id"   : "TEST-002",
        "thread_id"        : "thread-test",
        "applicant_name"   : "Test User",
        "pan_number"       : "TESTX9999X",
        "dob"              : "1990-01-01",
        "loan_amount"      : 500_000.0,
        "loan_type"        : "Personal",
        "loan_tenure"      : 5,
        "loan_purpose"     : "Test",
        "annual_income"    : 1_200_000.0,
        "employment_type"  : "Salaried",
        "employer_name"    : "Test Corp",
        "years_at_employer": 3,
        "existing_emi"     : 5_000.0,
        "active_loans"     : 0,
        "loan_default"     : "No",
        "collateral_type"  : "None",
        "collateral_value" : 0.0,
        "collateral_description": "",
        "uploaded_doc_text": "",
        # Node 1 outputs
        "doc_verified"     : True,
        "missing_docs"     : [],
        "doc_flags"        : [],
        "extracted_income" : 1_200_000.0,
        "extracted_name"   : "Test User",
        # Node 2 placeholder
        "bureau_score"     : 0,
        "dti_ratio"        : 0.0,
        "foir"             : 0.0,
        "income_stability" : "",
        "credit_flags"     : [],
        # Nodes 3-5 placeholders
        "risk_tier": "", "ltv_ratio": 0.0, "collateral_score": 0.0,
        "sector_risk": "", "risk_flags": [],
        "compliance_passed": False, "violations": [], "applicable_rules": [],
        "policy_notes": "",
        "decision": "", "confidence": 0.0, "decision_report": "",
        "recommended_terms": {},
        "current_node"     : "start",
        "errors"           : [],
        "messages"         : [],
    }
    base.update(overrides)
    return base


# ─────────────────────────────────────────────────────────────────────────────
# Pure-math tests (no LLM calls)
# ─────────────────────────────────────────────────────────────────────────────

def test_case_1_clean_applicant():
    """Clean applicant - should pass all thresholds."""
    print("\n-- Test 1: Clean Applicant --")
    annual_income  = 1_200_000.0
    loan_amount    = 500_000.0
    loan_tenure    = 5
    existing_emi   = 5_000.0
    active_loans   = 0
    past_default   = "No"
    employment     = "Salaried"
    years          = 3

    proposed_emi     = calculate_proposed_emi(loan_amount, loan_tenure)
    dti              = calculate_dti(existing_emi, annual_income)
    foir             = calculate_foir(existing_emi, proposed_emi, annual_income)
    stability        = assess_income_stability(employment, years)
    bureau           = mock_bureau_score(past_default, active_loans, annual_income, stability)

    print(f"  Proposed EMI     : Rs {proposed_emi:,.2f}")
    print(f"  DTI              : {dti} %")
    print(f"  FOIR             : {foir} %")
    print(f"  Income Stability : {stability}")
    print(f"  Bureau Score     : {bureau}")

    assert bureau > 650,   f"Expected bureau > 650, got {bureau}"
    assert foir   < 50,    f"Expected FOIR < 50 %, got {foir}"
    assert dti    < 50,    f"Expected DTI < 50 %, got {dti}"
    assert stability == "stable"
    print("  [PASS] Test 1 PASSED")


def test_case_2_high_foir():
    """High FOIR - should flag hard reject."""
    print("\n-- Test 2: High FOIR --")
    annual_income = 300_000.0
    loan_amount   = 2_000_000.0
    loan_tenure   = 5
    existing_emi  = 15_000.0

    proposed_emi = calculate_proposed_emi(loan_amount, loan_tenure)
    foir         = calculate_foir(existing_emi, proposed_emi, annual_income)

    print(f"  Proposed EMI : Rs {proposed_emi:,.2f}")
    print(f"  FOIR         : {foir} %")

    assert foir > 65, f"Expected FOIR > 65 %, got {foir}"
    print("  [PASS] Test 2 PASSED - hard reject FOIR flagged")


def test_case_3_past_default():
    """Past default - bureau score should drop below 550, hard reject."""
    print("\n-- Test 3: Past Default --")
    past_default  = "Yes"
    annual_income = 1_500_000.0
    active_loans  = 0
    stability     = assess_income_stability("Salaried", 4)
    bureau        = mock_bureau_score(past_default, active_loans, annual_income, stability)

    print(f"  Income Stability : {stability}")
    print(f"  Bureau Score     : {bureau}")

    assert bureau < 550, f"Expected bureau < 550, got {bureau}"
    print("  [PASS] Test 3 PASSED - hard reject bureau score flagged")


def test_case_4_self_employed_unstable():
    """Self-employed with < 3 years - income stability should be unstable."""
    print("\n-- Test 4: Self-Employed Unstable --")
    stability = assess_income_stability("Self-Employed", 1)
    print(f"  Income Stability : {stability}")
    assert stability == "unstable", f"Expected 'unstable', got '{stability}'"
    print("  [PASS] Test 4 PASSED - unstable income flagged")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n[*] Running Node 2 unit tests (pure math - no LLM calls)")
    test_case_1_clean_applicant()
    test_case_2_high_foir()
    test_case_3_past_default()
    test_case_4_self_employed_unstable()
    print("\n[OK] All 4 Node 2 tests PASSED!")
