"""
agent/nodes/credit_scoring.py
Node 2 — Credit Scoring

Reads verified income + loan details from state.
Calculates DTI, FOIR, income stability, and a mocked bureau score.
Calls LLM for a plain-English credit summary.
Writes results back to state and sets routing signals.
"""

import json
import os
from typing import Dict, Any

from dotenv import load_dotenv
from huggingface_hub import InferenceClient

from agent.state import AgentState
from tools.risk_calculator import (
    calculate_proposed_emi,
    calculate_dti,
    calculate_foir,
    assess_income_stability,
    mock_bureau_score,
)

load_dotenv()

# ── LLM Client ────────────────────────────────────────────────────────────────
HF_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")
MODEL_ID  = os.getenv("HF_MODEL_ID", "Qwen/Qwen2.5-7B-Instruct")

client = InferenceClient(api_key=HF_TOKEN)


# ── LLM call ──────────────────────────────────────────────────────────────────
def call_llm_credit_summary(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sends all calculated credit metrics to the LLM.
    Returns a dict with:
      - credit_summary  : plain-English paragraph
      - llm_flags       : list of additional red flags the LLM spotted
      - credit_label    : "Low" | "Medium" | "High"
    """
    system_prompt = (
        "You are a senior banking credit analyst. "
        "You must respond ONLY with a valid JSON object — no markdown, no explanation."
    )

    user_prompt = f"""Analyse the following credit metrics for a loan applicant and respond with ONLY this JSON:
{{
  "credit_summary": "<2-3 sentence plain English summary of repayment capacity>",
  "llm_flags": ["<flag 1>", "<flag 2>"],
  "credit_label": "<Low|Medium|High>"
}}

Metrics:
- Bureau Score       : {metrics['bureau_score']}  (scale 300-900; below 550 = very risky)
- DTI Ratio          : {metrics['dti_ratio']} %   (RBI safe limit: below 50 %)
- FOIR               : {metrics['foir']} %         (RBI safe limit: below 55 %; hard reject: above 65 %)
- Income Stability   : {metrics['income_stability']}
- Past Loan Default  : {metrics['past_default']}
- Active Loans       : {metrics['active_loans']}
- Annual Income      : ₹{metrics['annual_income']:,.0f}
- Loan Amount        : ₹{metrics['loan_amount']:,.0f}
- Proposed EMI       : ₹{metrics['proposed_emi']:,.0f} / month
- Existing EMI       : ₹{metrics['existing_emi']:,.0f} / month
- Employment Type    : {metrics['employment_type']}

If llm_flags is empty, return an empty list [].
credit_label must be exactly one of: Low, Medium, High.
"""

    response = client.chat_completion(
        model=MODEL_ID,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        max_tokens=512,
        temperature=0.2,
    )

    raw = response.choices[0].message.content.strip()
    print(f"[Node 2] Raw LLM response: {raw}")

    # Strip markdown fences if present
    if "```" in raw:
        for part in raw.split("```"):
            part = part.strip().lstrip("json").strip()
            if part.startswith("{"):
                raw = part
                break

    start = raw.find("{")
    end   = raw.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError(f"No JSON in LLM response: {raw}")

    return json.loads(raw[start:end])


# ── Main node function ────────────────────────────────────────────────────────
def run(state: AgentState) -> Dict[str, Any]:
    """
    Node 2: Credit Scoring

    1. Resolve income (prefer Node 1 extracted; fall back to declared)
    2. Calculate DTI, FOIR, proposed EMI
    3. Assess income stability
    4. Mock bureau score
    5. Apply hard rules → credit_flags
    6. Call LLM for plain-English summary
    7. Return updated state fields
    """
    print("\n--- NODE 2: CREDIT SCORING ---")

    # ── Resolve income ────────────────────────────────────────────────────────
    extracted_income = state.get("extracted_income", 0.0)
    declared_income  = state.get("annual_income", 0.0)
    # Use extracted income if Node 1 verified it; otherwise fall back to declared
    income = extracted_income if extracted_income > 0 else declared_income
    print(f"[Node 2] Using income: ₹{income:,.0f} "
          f"({'extracted' if extracted_income > 0 else 'declared'})")

    loan_amount      = state.get("loan_amount", 0.0)
    loan_tenure      = state.get("loan_tenure", 1)
    existing_emi     = state.get("existing_emi", 0.0)
    employment_type  = state.get("employment_type", "Salaried")
    years_at_employer= state.get("years_at_employer", 0)
    active_loans     = state.get("active_loans", 0)
    past_default     = state.get("loan_default", "No")   # "Yes" | "No"

    credit_flags: list = []

    # ── Step 1: Income stability ───────────────────────────────────────────────
    income_stability = assess_income_stability(employment_type, years_at_employer)
    print(f"[Node 2] Income stability: {income_stability}")
    if income_stability == "unstable":
        credit_flags.append("Income stability is UNSTABLE — short employment tenure")

    # ── Step 2: Proposed EMI & ratios ─────────────────────────────────────────
    proposed_emi = calculate_proposed_emi(loan_amount, loan_tenure)
    dti_ratio    = calculate_dti(existing_emi, income)
    foir         = calculate_foir(existing_emi, proposed_emi, income)

    print(f"[Node 2] Proposed EMI : ₹{proposed_emi:,.2f}")
    print(f"[Node 2] DTI          : {dti_ratio} %")
    print(f"[Node 2] FOIR         : {foir} %")

    if dti_ratio > 50:
        credit_flags.append(f"DTI ratio is {dti_ratio:.1f} % — exceeds RBI limit of 50 %")
    if foir > 65:
        credit_flags.append(f"FOIR is {foir:.1f} % — HARD REJECT threshold (>65 %) breached")
    elif foir > 55:
        credit_flags.append(f"FOIR is {foir:.1f} % — above comfortable limit of 55 %")

    # ── Step 3: Mock bureau score ─────────────────────────────────────────────
    bureau_score = mock_bureau_score(
        past_default=past_default,
        active_loans=active_loans,
        annual_income=income,
        income_stability=income_stability,
    )
    print(f"[Node 2] Bureau score : {bureau_score}")

    if past_default.lower() == "yes":
        credit_flags.append("Applicant has a PAST LOAN DEFAULT on record")
    if bureau_score < 550:
        credit_flags.append(f"Bureau score {bureau_score} is critically low (<550) — HARD REJECT")
    elif bureau_score < 650:
        credit_flags.append(f"Bureau score {bureau_score} is below acceptable threshold (650)")

    if active_loans > 3:
        credit_flags.append(f"High number of active loans ({active_loans}) — increased credit risk")

    # ── Step 4: LLM credit summary ────────────────────────────────────────────
    llm_summary  = ""
    llm_flags    = []
    credit_label = "High"  # Pessimistic default if LLM call fails

    metrics = {
        "bureau_score"   : bureau_score,
        "dti_ratio"      : dti_ratio,
        "foir"           : foir,
        "income_stability": income_stability,
        "past_default"   : past_default,
        "active_loans"   : active_loans,
        "annual_income"  : income,
        "loan_amount"    : loan_amount,
        "proposed_emi"   : proposed_emi,
        "existing_emi"   : existing_emi,
        "employment_type": employment_type,
    }

    try:
        llm_data     = call_llm_credit_summary(metrics)
        llm_summary  = llm_data.get("credit_summary", "")
        llm_flags    = llm_data.get("llm_flags", [])
        credit_label = llm_data.get("credit_label", "High")
        credit_flags.extend(llm_flags)
        print(f"[Node 2] LLM credit label: {credit_label}")
    except Exception as e:
        err = f"LLM credit analysis failed: {e}"
        print(f"[Node 2] WARNING: {err}")
        credit_flags.append(err)

    # ── Step 5: Routing signals ───────────────────────────────────────────────
    # Hard reject conditions (evaluated by streamlit_app / graph router)
    hard_reject = bureau_score < 550 or foir > 65

    print(f"[Node 2] Hard reject: {hard_reject}")
    print(f"[Node 2] Credit flags: {credit_flags}")

    return {
        "bureau_score"     : bureau_score,
        "dti_ratio"        : dti_ratio,
        "foir"             : foir,
        "income_stability" : income_stability,
        "credit_flags"     : credit_flags,
        # Extra fields passed to UI (not in core state but used for display)
        "proposed_emi"     : proposed_emi,
        "credit_label"     : credit_label,
        "credit_summary"   : llm_summary,
        "hard_reject"      : hard_reject,
        "current_node"     : "credit_scoring",
    }
