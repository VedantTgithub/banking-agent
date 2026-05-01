"""
agent/nodes/risk_assessment.py
Node 3 — Risk Assessment

Reads credit outputs from Node 2 plus loan/collateral details from state.
Calculates LTV, collateral quality, sector risk, and overall risk tier.
Calls LLM for a plain-English risk summary.
Writes results back to state.
"""

import json
import os
from typing import Dict, Any

from dotenv import load_dotenv
from huggingface_hub import InferenceClient

from agent.state import AgentState
from tools.risk_calculator import (
    get_rbi_ltv_cap,
    calculate_ltv,
    score_collateral,
    assess_sector_risk,
    calculate_risk_tier,
)

load_dotenv()

# ── LLM Client ────────────────────────────────────────────────────────────────
HF_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")
MODEL_ID  = os.getenv("HF_MODEL_ID", "Qwen/Qwen2.5-7B-Instruct")

client = InferenceClient(api_key=HF_TOKEN)


# ── LLM Risk Summary ──────────────────────────────────────────────────────────
def call_llm_risk_summary(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sends all calculated risk metrics to the LLM.
    Returns a dict with:
      - risk_summary : plain-English paragraph (2-3 sentences)
      - llm_flags    : list of additional risk factors the LLM spotted
      - confirmed_tier: LLM-confirmed or adjusted risk tier
    """
    system_prompt = (
        "You are a senior banking risk officer. "
        "You must respond ONLY with a valid JSON object — no markdown, no explanation."
    )

    user_prompt = f"""Analyse the following loan risk metrics and respond with ONLY this JSON:
{{
  "risk_summary": "<2-3 sentence plain English assessment of the loan's risk to the bank>",
  "llm_flags": ["<extra risk factor 1>", "<extra risk factor 2>"],
  "confirmed_tier": "<low|medium|high|very_high>"
}}

Loan Risk Metrics:
- Risk Tier (calculated) : {metrics['risk_tier']}
- LTV Ratio              : {metrics['ltv_ratio']} %  (RBI cap: {metrics['ltv_cap']} %)
- Collateral Type        : {metrics['collateral_type']}
- Collateral Score       : {metrics['collateral_score']} / 1.0
- Sector Risk            : {metrics['sector_risk']}
- Bureau Score           : {metrics['bureau_score']}
- FOIR                   : {metrics['foir']} %
- Income Stability       : {metrics['income_stability']}
- Past Default           : {metrics['past_default']}
- Loan Type              : {metrics['loan_type']}
- Loan Amount            : Rs {metrics['loan_amount']:,.0f}
- Employment Type        : {metrics['employment_type']}
- Years at Employer      : {metrics['years_at_employer']}

If llm_flags is empty return [].
confirmed_tier must be exactly one of: low, medium, high, very_high.
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
    print(f"[Node 3] Raw LLM response: {raw}")

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
    Node 3: Risk Assessment

    1. Read credit outputs from Node 2 + form inputs
    2. Calculate LTV and check against RBI cap
    3. Score collateral quality
    4. Assess sector / employment risk
    5. Compute overall risk tier
    6. Call LLM for plain-English risk summary
    7. Return updated state fields
    """
    print("\n--- NODE 3: RISK ASSESSMENT ---")

    # ── Read inputs ───────────────────────────────────────────────────────────
    bureau_score     = state.get("bureau_score", 0)
    foir             = state.get("foir", 0.0)
    income_stability = state.get("income_stability", "unstable")

    loan_amount      = state.get("loan_amount", 0.0)
    loan_type        = state.get("loan_type", "Personal")
    collateral_type  = state.get("collateral_type", "None")
    collateral_value = state.get("collateral_value", 0.0)
    employment_type  = state.get("employment_type", "Salaried")
    years_at_employer= state.get("years_at_employer", 0)
    past_default     = state.get("loan_default", "No")

    risk_flags: list = []

    # ── Step 1: LTV ───────────────────────────────────────────────────────────
    ltv_ratio = calculate_ltv(loan_amount, collateral_value)
    ltv_cap   = get_rbi_ltv_cap(loan_type, loan_amount)

    print(f"[Node 3] LTV ratio : {ltv_ratio} %  (RBI cap: {ltv_cap} %)")

    if ltv_ratio > 0 and ltv_ratio > ltv_cap:
        flag = (f"LTV {ltv_ratio:.1f}% exceeds RBI cap of {ltv_cap:.0f}% "
                f"for {loan_type} loan of Rs {loan_amount:,.0f}")
        risk_flags.append(flag)
        print(f"[Node 3] WARNING: {flag}")

    # ── Step 2: Collateral score ──────────────────────────────────────────────
    collateral_score = score_collateral(collateral_type)
    print(f"[Node 3] Collateral score : {collateral_score} ({collateral_type})")

    if collateral_score == 0.0 and loan_amount > 1_000_000:
        risk_flags.append(
            f"Unsecured loan of Rs {loan_amount:,.0f} — no collateral provided"
        )
    elif collateral_score < 0.5:
        risk_flags.append(
            f"Weak collateral ({collateral_type}) — score {collateral_score}/1.0"
        )

    # ── Step 3: Sector risk ───────────────────────────────────────────────────
    sector_risk = assess_sector_risk(employment_type, years_at_employer)
    print(f"[Node 3] Sector risk : {sector_risk}")

    if sector_risk == "high":
        risk_flags.append(
            f"High sector risk: {employment_type} with only {years_at_employer} years tenure"
        )

    # ── Step 4: Overall risk tier ─────────────────────────────────────────────
    risk_tier = calculate_risk_tier(
        bureau_score=bureau_score,
        foir=foir,
        ltv_ratio=ltv_ratio,
        ltv_cap=ltv_cap,
        collateral_score=collateral_score,
        loan_amount=loan_amount,
        sector_risk=sector_risk,
        income_stability=income_stability,
        past_default=past_default,
    )
    print(f"[Node 3] Risk tier : {risk_tier}")

    if past_default.lower() == "yes":
        risk_flags.insert(0, "Past loan default — immediate escalation to very_high risk tier")

    # ── Step 5: LLM risk summary ──────────────────────────────────────────────
    risk_summary   = ""
    llm_flags      = []
    confirmed_tier = risk_tier   # fallback

    metrics = {
        "risk_tier"       : risk_tier,
        "ltv_ratio"       : ltv_ratio,
        "ltv_cap"         : ltv_cap,
        "collateral_type" : collateral_type,
        "collateral_score": collateral_score,
        "sector_risk"     : sector_risk,
        "bureau_score"    : bureau_score,
        "foir"            : foir,
        "income_stability": income_stability,
        "past_default"    : past_default,
        "loan_type"       : loan_type,
        "loan_amount"     : loan_amount,
        "employment_type" : employment_type,
        "years_at_employer": years_at_employer,
    }

    try:
        llm_data       = call_llm_risk_summary(metrics)
        risk_summary   = llm_data.get("risk_summary", "")
        llm_flags      = llm_data.get("llm_flags", [])
        confirmed_tier = llm_data.get("confirmed_tier", risk_tier)
        risk_flags.extend(llm_flags)
        print(f"[Node 3] LLM confirmed tier: {confirmed_tier}")
    except Exception as e:
        err = f"LLM risk summary failed: {e}"
        print(f"[Node 3] WARNING: {err}")
        risk_flags.append(err)

    return {
        "risk_tier"       : confirmed_tier,
        "ltv_ratio"       : ltv_ratio,
        "collateral_score": collateral_score,
        "sector_risk"     : sector_risk,
        "risk_flags"      : risk_flags,
        # Extra display fields (not core state, used by Streamlit)
        "ltv_cap"         : ltv_cap,
        "risk_summary"    : risk_summary,
        "current_node"    : "risk_assessment",
    }
