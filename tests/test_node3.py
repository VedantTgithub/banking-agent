"""
tests/test_node3.py
Unit tests for Node 3 -- Risk Assessment.

Run from the loan_underwriting_agent directory:
    python -m tests.test_node3
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.risk_calculator import (
    calculate_ltv,
    get_rbi_ltv_cap,
    score_collateral,
    assess_sector_risk,
    calculate_risk_tier,
)


# ─────────────────────────────────────────────────────────────────────────────
# Test 1 -- Clean home loan with good collateral (should be low risk)
# ─────────────────────────────────────────────────────────────────────────────
def test_case_1_clean_home_loan():
    print("\n-- Test 1: Clean Home Loan (Low Risk) --")
    loan_amount      = 4_000_000.0   # 40L
    collateral_value = 6_000_000.0   # 60L
    loan_type        = "Home"
    bureau_score     = 750
    foir             = 38.0
    income_stability = "stable"
    collateral_type  = "Property"

    ltv_ratio        = calculate_ltv(loan_amount, collateral_value)
    ltv_cap          = get_rbi_ltv_cap(loan_type, loan_amount)
    collateral_score = score_collateral(collateral_type)
    sector_risk      = assess_sector_risk("Salaried", 5)
    risk_tier        = calculate_risk_tier(
        bureau_score, foir, ltv_ratio, ltv_cap,
        collateral_score, loan_amount, sector_risk, income_stability, "No"
    )

    print(f"  LTV ratio        : {ltv_ratio} %  (cap: {ltv_cap} %)")
    print(f"  Collateral score : {collateral_score}")
    print(f"  Sector risk      : {sector_risk}")
    print(f"  Risk tier        : {risk_tier}")

    assert abs(ltv_ratio - 66.67) < 0.1, f"Expected LTV ~66.67%, got {ltv_ratio}"
    assert ltv_ratio <= ltv_cap,          f"LTV {ltv_ratio} should be within RBI cap {ltv_cap}"
    assert risk_tier == "low",            f"Expected risk_tier='low', got '{risk_tier}'"
    print("  [PASS] Test 1 PASSED")


# ─────────────────────────────────────────────────────────────────────────────
# Test 2 -- LTV breach (70L loan, 80L property -> 87.5% > 80% RBI cap)
# ─────────────────────────────────────────────────────────────────────────────
def test_case_2_ltv_breach():
    print("\n-- Test 2: LTV Breach -> High Risk --")
    loan_amount      = 7_000_000.0   # 70L
    collateral_value = 8_000_000.0   # 80L
    loan_type        = "Home"

    ltv_ratio = calculate_ltv(loan_amount, collateral_value)
    ltv_cap   = get_rbi_ltv_cap(loan_type, loan_amount)
    risk_tier = calculate_risk_tier(
        bureau_score=720, foir=42.0,
        ltv_ratio=ltv_ratio, ltv_cap=ltv_cap,
        collateral_score=score_collateral("Property"),
        loan_amount=loan_amount,
        sector_risk="low", income_stability="stable", past_default="No"
    )

    print(f"  LTV ratio : {ltv_ratio} %  (cap: {ltv_cap} %)")
    print(f"  Risk tier : {risk_tier}")

    assert ltv_ratio > ltv_cap, f"LTV {ltv_ratio} should exceed cap {ltv_cap}"
    assert risk_tier == "high", f"Expected risk_tier='high', got '{risk_tier}'"
    print("  [PASS] Test 2 PASSED - LTV breach flagged as high risk")


# ─────────────────────────────────────────────────────────────────────────────
# Test 3 -- Unsecured personal loan high amount (20L, no collateral)
# ─────────────────────────────────────────────────────────────────────────────
def test_case_3_unsecured_large_loan():
    print("\n-- Test 3: Unsecured Personal Loan (High Amount) --")
    loan_amount      = 2_000_000.0   # 20L
    collateral_type  = "None"
    bureau_score     = 620

    collateral_score = score_collateral(collateral_type)
    ltv_ratio        = calculate_ltv(loan_amount, 0.0)
    ltv_cap          = get_rbi_ltv_cap("Personal", loan_amount)
    risk_tier        = calculate_risk_tier(
        bureau_score=bureau_score, foir=45.0,
        ltv_ratio=ltv_ratio, ltv_cap=ltv_cap,
        collateral_score=collateral_score,
        loan_amount=loan_amount,
        sector_risk="low", income_stability="stable", past_default="No"
    )

    print(f"  Collateral score : {collateral_score}")
    print(f"  Bureau score     : {bureau_score}")
    print(f"  Risk tier        : {risk_tier}")

    assert collateral_score == 0.0,  f"Expected 0.0, got {collateral_score}"
    assert risk_tier in ("high", "medium"), f"Expected high/medium risk, got '{risk_tier}'"
    print("  [PASS] Test 3 PASSED - unsecured large loan flagged")


# ─────────────────────────────────────────────────────────────────────────────
# Test 4 -- Past default -> very_high immediately
# ─────────────────────────────────────────────────────────────────────────────
def test_case_4_past_default():
    print("\n-- Test 4: Past Default -> Very High Risk --")
    risk_tier = calculate_risk_tier(
        bureau_score=540, foir=35.0,
        ltv_ratio=50.0, ltv_cap=90.0,
        collateral_score=0.0,
        loan_amount=1_000_000.0,
        sector_risk="low", income_stability="stable", past_default="Yes"
    )

    print(f"  Risk tier : {risk_tier}")
    assert risk_tier == "very_high", f"Expected 'very_high', got '{risk_tier}'"
    print("  [PASS] Test 4 PASSED - past default escalates to very_high")


# ─────────────────────────────────────────────────────────────────────────────
# Test 5 -- Business owner, short tenure, vehicle collateral
# ─────────────────────────────────────────────────────────────────────────────
def test_case_5_business_unstable_sector():
    print("\n-- Test 5: Business Owner, Unstable Sector --")
    employment_type  = "Business Owner"
    years_employed   = 1
    collateral_type  = "Vehicle"
    collateral_value = 500_000.0
    loan_amount      = 1_000_000.0

    sector_risk      = assess_sector_risk(employment_type, years_employed)
    collateral_score = score_collateral(collateral_type)
    ltv_ratio        = calculate_ltv(loan_amount, collateral_value)
    ltv_cap          = get_rbi_ltv_cap("Vehicle", loan_amount)
    risk_tier        = calculate_risk_tier(
        bureau_score=700, foir=40.0,
        ltv_ratio=ltv_ratio, ltv_cap=ltv_cap,
        collateral_score=collateral_score,
        loan_amount=loan_amount,
        sector_risk=sector_risk,
        income_stability="unstable",
        past_default="No"
    )

    print(f"  Sector risk      : {sector_risk}")
    print(f"  Collateral score : {collateral_score}")
    print(f"  LTV ratio        : {ltv_ratio} %  (cap: {ltv_cap} %)")
    print(f"  Risk tier        : {risk_tier}")

    assert sector_risk == "high",      f"Expected sector_risk='high', got '{sector_risk}'"
    assert collateral_score == 0.50,   f"Expected collateral_score=0.5, got {collateral_score}"
    assert risk_tier in ("medium", "high"), f"Expected medium/high, got '{risk_tier}'"
    print("  [PASS] Test 5 PASSED - high sector risk flagged")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n[*] Running Node 3 unit tests (pure math - no LLM calls)")
    test_case_1_clean_home_loan()
    test_case_2_ltv_breach()
    test_case_3_unsecured_large_loan()
    test_case_4_past_default()
    test_case_5_business_unstable_sector()
    print("\n[OK] All 5 Node 3 tests PASSED!")
