"""
tools/risk_calculator.py
Pure-math financial helpers — no LLM calls, no I/O side-effects.
Used by Node 2 (credit_scoring.py).
"""


# ── 1. Proposed EMI (simplified flat-rate) ────────────────────────────────────
def calculate_proposed_emi(loan_amount: float, loan_tenure_years: int) -> float:
    """
    Simplified EMI = loan_amount / (tenure_years * 12).
    In production replace with proper amortisation formula.
    Returns 0 if either input is zero.
    """
    months = loan_tenure_years * 12
    if months == 0 or loan_amount == 0:
        return 0.0
    return round(loan_amount / months, 2)


# ── 2. DTI — Debt-to-Income Ratio ─────────────────────────────────────────────
def calculate_dti(existing_emi: float, annual_income: float) -> float:
    """
    DTI = (existing_emi * 12) / annual_income * 100
    RBI guideline: keep below 50 %.
    Returns 0 if annual_income is zero.
    """
    if annual_income == 0:
        return 0.0
    dti = (existing_emi * 12) / annual_income * 100
    return round(dti, 2)


# ── 3. FOIR — Fixed Obligation to Income Ratio ────────────────────────────────
def calculate_foir(
    existing_emi: float,
    proposed_emi: float,
    annual_income: float,
) -> float:
    """
    FOIR = (existing_emi + proposed_emi) / monthly_income * 100
    RBI guideline: flag above 55 %, hard-reject above 65 %.
    Returns 0 if annual_income is zero.
    """
    if annual_income == 0:
        return 0.0
    monthly_income = annual_income / 12
    foir = (existing_emi + proposed_emi) / monthly_income * 100
    return round(foir, 2)


# ── 4. Income Stability ───────────────────────────────────────────────────────
def assess_income_stability(employment_type: str, years_at_employer: int) -> str:
    """
    Returns "stable" | "moderate" | "unstable" based on employment type and tenure.
    """
    emp = employment_type.lower().replace("-", " ").replace("_", " ")

    if "salaried" in emp:
        if years_at_employer >= 2:
            return "stable"
        elif years_at_employer >= 1:
            return "moderate"
        else:
            return "unstable"

    elif "self employed" in emp or "business" in emp:
        if years_at_employer >= 3:
            return "moderate"
        else:
            return "unstable"

    # Fallback
    return "unstable"


# ── 5. Mocked Bureau Score ────────────────────────────────────────────────────
def mock_bureau_score(
    past_default: str,
    active_loans: int,
    annual_income: float,
    income_stability: str,
) -> int:
    """
    Generates a realistic CIBIL-style score (300–900) based on risk signals.
    In production this is replaced by a live CIBIL / Experian API call.

    Scoring logic:
      Base score                        : 750
      Past default = Yes                : -200
      Each active loan beyond 1         : -20 per extra loan
      Income > 10 LPA (stable)         : +50
      Unstable income                   : -50
      Moderate income stability         : -20
    Final score is clamped to [300, 900].
    """
    score = 750

    # Past default is the biggest negative signal.
    # Apply it first and skip income bonus — a defaulter must score below 550.
    has_default = past_default.strip().lower() == "yes"
    if has_default:
        score -= 210          # 750 - 210 = 540, safely below 550

    # Penalise for each loan beyond the first
    if active_loans > 1:
        score -= (active_loans - 1) * 20

    # Income / stability bonus only applies to clean applicants
    if not has_default:
        if annual_income >= 1_000_000 and income_stability == "stable":
            score += 50
        elif income_stability == "unstable":
            score -= 50
        elif income_stability == "moderate":
            score -= 20

    return max(300, min(900, score))


# ══════════════════════════════════════════════════════════════════════════════
# NODE 3 HELPERS — Risk Assessment
# ══════════════════════════════════════════════════════════════════════════════

# ── 6. RBI LTV Cap ────────────────────────────────────────────────────────────
def get_rbi_ltv_cap(loan_type: str, loan_amount: float) -> float:
    """
    Returns the RBI-mandated maximum LTV % for the given loan type and amount.
    Returns 100.0 for loan types with no regulatory LTV cap (personal, business).
    """
    lt = loan_type.lower()

    if "home" in lt:
        if loan_amount <= 3_000_000:       # up to 30L
            return 90.0
        elif loan_amount <= 7_500_000:     # 30L – 75L
            return 80.0
        else:                              # above 75L
            return 75.0

    elif "vehicle" in lt:
        return 85.0

    # Personal / Business — no mandatory LTV cap
    return 100.0


# ── 7. LTV Ratio ──────────────────────────────────────────────────────────────
def calculate_ltv(loan_amount: float, collateral_value: float) -> float:
    """
    LTV = loan_amount / collateral_value * 100
    Returns 0.0 when collateral_value is 0 (unsecured loan).
    """
    if collateral_value == 0:
        return 0.0
    return round(loan_amount / collateral_value * 100, 2)


# ── 8. Collateral Score ───────────────────────────────────────────────────────
def score_collateral(collateral_type: str) -> float:
    """
    Ranks collateral quality on a 0–1 scale.
    FD = best (liquid, guaranteed); None = worst (unsecured).
    """
    mapping = {
        "fd"       : 1.0,
        "gold"     : 0.85,
        "property" : 0.75,
        "vehicle"  : 0.50,
        "none"     : 0.0,
    }
    return mapping.get(collateral_type.lower(), 0.0)


# ── 9. Sector / Employment Risk ───────────────────────────────────────────────
def assess_sector_risk(employment_type: str, years_at_employer: int) -> str:
    """
    Returns "low" | "medium" | "high" based on employment type and stability.
    """
    emp = employment_type.lower().replace("-", " ").replace("_", " ")

    if "salaried" in emp:
        # Assume stable corporate employer; long tenure = lower risk
        if years_at_employer >= 3:
            return "low"
        else:
            return "medium"

    elif "self employed" in emp:
        if years_at_employer >= 3:
            return "medium"
        else:
            return "high"

    elif "business" in emp:
        # Business owners carry volatile income risk
        if years_at_employer >= 5:
            return "medium"
        else:
            return "high"

    return "high"   # Unknown employment type → conservative


# ── 10. Overall Risk Tier ─────────────────────────────────────────────────────
def calculate_risk_tier(
    bureau_score    : int,
    foir            : float,
    ltv_ratio       : float,
    ltv_cap         : float,
    collateral_score: float,
    loan_amount     : float,
    sector_risk     : str,
    income_stability: str,
    past_default    : str,
) -> str:
    """
    Combines all risk signals into a single risk tier.
    Returns "low" | "medium" | "high" | "very_high".

    Escalation rules (applied in order; tier can only increase):
      past_default = Yes          → very_high (immediate)
      bureau_score < 600          → high
      bureau_score < 650          → medium
      foir > 60 %                 → high
      foir > 50 %                 → medium
      ltv > RBI cap               → high
      collateral_score < 0.5
        AND loan > 10 L           → medium
      sector_risk = high          → medium
      income_stability = unstable → medium
    """
    TIER_ORDER = ["low", "medium", "high", "very_high"]

    def escalate(current: str, new: str) -> str:
        return new if TIER_ORDER.index(new) > TIER_ORDER.index(current) else current

    tier = "low"

    # Immediate escalation — past default overrides everything
    if past_default.strip().lower() == "yes":
        return "very_high"

    # Bureau score signals
    if bureau_score < 600:
        tier = escalate(tier, "high")
    elif bureau_score < 650:
        tier = escalate(tier, "medium")

    # FOIR signals
    if foir > 60:
        tier = escalate(tier, "high")
    elif foir > 50:
        tier = escalate(tier, "medium")

    # LTV breach
    if ltv_ratio > 0 and ltv_ratio > ltv_cap:
        tier = escalate(tier, "high")

    # Weak collateral on large unsecured loan (> 10L)
    if collateral_score < 0.5 and loan_amount > 1_000_000:
        tier = escalate(tier, "medium")

    # Sector risk
    if sector_risk == "high":
        tier = escalate(tier, "medium")

    # Income instability
    if income_stability == "unstable":
        tier = escalate(tier, "medium")

    return tier
