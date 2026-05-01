"""
agent/nodes/policy_compliance.py
Node 4 — Policy Compliance Check (RAG-powered)

Answers: "Does this loan application comply with all regulatory rules
          and internal bank policies?"

Flow:
  1. Build targeted queries from state (loan_type, loan_amount, risk_tier, etc.)
  2. Retrieve relevant policy chunks from Chroma via RAG
  3. Pass retrieved text + application metrics to LLM
  4. LLM reads the actual policy text and flags violations
  5. Return compliance_passed, violations, applicable_rules, policy_notes
"""

import json
import os
from typing import Dict, Any, List

from dotenv import load_dotenv
from huggingface_hub import InferenceClient

from agent.state import AgentState

load_dotenv()

# ── LLM Client ────────────────────────────────────────────────────────────────
HF_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")
MODEL_ID  = os.getenv("HF_MODEL_ID", "Qwen/Qwen2.5-7B-Instruct")

client = InferenceClient(api_key=HF_TOKEN)

# ── Fallback hardcoded rules (used when RAG store is unavailable) ─────────────
# These mirror the RBI/internal rules from the Node 4 spec so the system
# degrades gracefully even without a Chroma store.
FALLBACK_POLICY_TEXT = """
RBI MASTER CIRCULAR — KEY RULES (HARDCODED FALLBACK):

LTV CAPS (Home Loans):
  - Loan up to Rs 30 lakh       → max LTV 90%
  - Loan Rs 30–75 lakh          → max LTV 80%
  - Loan above Rs 75 lakh       → max LTV 75%
  - Vehicle loans                → max LTV 85%

FOIR LIMITS:
  - Salaried borrowers           → max FOIR 55%
  - Self-employed borrowers      → max FOIR 65%

KYC:
  - PAN mandatory for all loans above Rs 50,000

MINIMUM CREDIT SCORES (Internal Policy):
  - Personal loan → min 700
  - Home loan     → min 650
  - Business loan → min 675
  - Vehicle loan  → min 650

LOAN TENURE LIMITS:
  - Home loan     → max 30 years
  - Personal loan → max 7 years
  - Vehicle loan  → max 7 years
  - Business loan → max 15 years

UNSECURED LOAN CAP (Internal Policy):
  - Personal loans without collateral capped at Rs 25 lakh
    without additional verification

PRIORITY SECTOR LENDING (RBI):
  - Home loans up to Rs 35 lakh in metro cities qualify for PSL
  - Agricultural and MSME loans qualify for PSL
"""


# ── Step 1: Build RAG queries from application state ─────────────────────────
def build_rag_queries(state: AgentState) -> List[str]:
    """
    Builds targeted retrieval queries based on the application profile.
    More specific queries = more relevant chunks retrieved.
    """
    loan_type    = state.get("loan_type", "Personal")
    loan_amount  = state.get("loan_amount", 0.0)
    risk_tier    = state.get("risk_tier", "medium")
    collateral   = state.get("collateral_type", "None")
    emp_type     = state.get("employment_type", "Salaried")

    amount_lakhs = loan_amount / 100_000  # convert to lakhs for query clarity

    queries = [
        f"RBI LTV cap {loan_type.lower()} loan {amount_lakhs:.0f} lakhs",
        f"RBI FOIR limit {emp_type.lower()} borrower repayment capacity",
        f"KYC PAN mandatory loan above 50000",
        f"minimum credit score {loan_type.lower()} loan internal policy",
        f"maximum loan tenure {loan_type.lower()} RBI guidelines",
        f"RBI {risk_tier} risk capital requirement Basel III",
    ]

    # Add collateral-specific query
    if collateral.lower() == "none":
        queries.append("unsecured personal loan amount cap internal credit policy")
    else:
        queries.append(f"secured loan {collateral.lower()} collateral RBI norms")

    # Add PSL query for qualifying loan types / amounts
    if loan_type.lower() in ["home", "business"]:
        queries.append("priority sector lending RBI classification home business loan")

    print(f"[Node 4] Built {len(queries)} RAG queries.")
    return queries


# ── Step 2: Retrieve policy chunks ───────────────────────────────────────────
def retrieve_policy_chunks(queries: List[str]) -> str:
    """
    Tries to use the Chroma retriever. Falls back to hardcoded policy text
    if the Chroma store is not available (e.g. ingest.py hasn't been run).

    Returns a single string of all relevant policy chunks concatenated.
    """
    try:
        from rag.retriever import get_retriever
        retriever = get_retriever(k=4)

        seen_chunks  = set()
        all_chunks   = []

        for query in queries:
            try:
                docs = retriever.invoke(query)
                for doc in docs:
                    # Deduplicate by content hash
                    chunk_id = hash(doc.page_content[:200])
                    if chunk_id not in seen_chunks:
                        seen_chunks.add(chunk_id)
                        source = doc.metadata.get("source", "unknown")
                        all_chunks.append(
                            f"[Source: {source}]\n{doc.page_content.strip()}"
                        )
            except Exception as qe:
                print(f"[Node 4] Query failed '{query}': {qe}")

        if all_chunks:
            combined = "\n\n---\n\n".join(all_chunks)
            print(f"[Node 4] Retrieved {len(all_chunks)} unique policy chunks via RAG.")
            return combined

        print("[Node 4] RAG returned no chunks — using hardcoded fallback.")
        return FALLBACK_POLICY_TEXT

    except FileNotFoundError as e:
        print(f"[Node 4] Chroma store not found ({e}). Using hardcoded fallback.")
        return FALLBACK_POLICY_TEXT
    except Exception as e:
        print(f"[Node 4] RAG retrieval error ({e}). Using hardcoded fallback.")
        return FALLBACK_POLICY_TEXT


# ── Step 3: LLM compliance check ─────────────────────────────────────────────
def call_llm_compliance_check(
    policy_text : str,
    app_metrics : Dict[str, Any],
) -> Dict[str, Any]:
    """
    Passes the retrieved policy text + application metrics to the LLM.
    The LLM reads the actual policy and checks each rule.

    Returns dict with:
      - compliance_passed  : bool
      - violations         : list[str]
      - applicable_rules   : list[str]
      - policy_notes       : str
    """
    system_prompt = (
        "You are a senior banking compliance officer. "
        "You must respond ONLY with a valid JSON object — no markdown, no explanation. "
        "Read the retrieved policy text carefully and apply it strictly to the application."
    )

    user_prompt = f"""You are checking a loan application for regulatory and policy compliance.

=== RETRIEVED POLICY TEXT ===
{policy_text[:4000]}

=== LOAN APPLICATION METRICS ===
- Applicant Name       : {app_metrics['applicant_name']}
- PAN Number           : {app_metrics['pan_number']}
- Loan Type            : {app_metrics['loan_type']}
- Loan Amount          : Rs {app_metrics['loan_amount']:,.0f}
- Loan Tenure          : {app_metrics['loan_tenure']} years
- Employment Type      : {app_metrics['employment_type']}
- Annual Income        : Rs {app_metrics['annual_income']:,.0f}
- Collateral Type      : {app_metrics['collateral_type']}
- Collateral Value     : Rs {app_metrics['collateral_value']:,.0f}
- Bureau Score         : {app_metrics['bureau_score']}
- DTI Ratio            : {app_metrics['dti_ratio']:.1f}%
- FOIR                 : {app_metrics['foir']:.1f}%
- LTV Ratio            : {app_metrics['ltv_ratio']:.1f}%
- Risk Tier            : {app_metrics['risk_tier']}
- Past Default         : {app_metrics['past_default']}

=== YOUR TASK ===
Check ALL of the following against the retrieved policy text:
1. KYC compliance (PAN provided and valid format ABCDE1234F)
2. LTV cap (check against RBI rules for this loan type and amount bracket)
3. FOIR limit (check against employment type)
4. Minimum credit score (check against loan type)
5. Loan tenure limit (check against loan type)
6. Unsecured loan cap (if no collateral and personal loan)
7. Priority sector lending eligibility (note if applicable)

Respond with ONLY this JSON (no markdown, no preamble):
{{
  "compliance_passed": true or false,
  "violations": [
    "Violation description citing the policy rule e.g. LTV 87% exceeds RBI cap of 80% for loans between Rs 30-75 lakh (RBI Master Circular Section 3.2)"
  ],
  "applicable_rules": [
    "Rule name and section e.g. RBI Master Circular 2024 — Section 3.2 LTV Norms"
  ],
  "policy_notes": "Any important notes e.g. loan qualifies for priority sector lending, or conditional approval possible with additional documentation"
}}

If there are no violations, set compliance_passed to true and violations to [].
Each violation must cite the specific policy section from the retrieved text if available.
"""

    response = client.chat_completion(
        model=MODEL_ID,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        max_tokens=1024,
        temperature=0.1,   # Low temp for deterministic compliance decisions
    )

    raw = response.choices[0].message.content.strip()
    print(f"[Node 4] Raw LLM response:\n{raw}")

    # Strip markdown fences if model added them
    if "```" in raw:
        for part in raw.split("```"):
            part = part.strip().lstrip("json").strip()
            if part.startswith("{"):
                raw = part
                break

    start = raw.find("{")
    end   = raw.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError(f"No JSON found in LLM compliance response: {raw}")

    return json.loads(raw[start:end])


# ── Main node function ────────────────────────────────────────────────────────
def run(state: AgentState) -> Dict[str, Any]:
    """
    Node 4: Policy Compliance Check

    1. Build targeted RAG queries from state
    2. Retrieve relevant policy chunks from Chroma (fallback to hardcoded)
    3. Send retrieved policy + application metrics to LLM
    4. LLM checks all compliance rules against actual policy text
    5. Return compliance result to state
    """
    print("\n--- NODE 4: POLICY COMPLIANCE CHECK ---")

    # ── Read all inputs from state ────────────────────────────────────────────
    app_metrics = {
        "applicant_name"  : state.get("applicant_name", ""),
        "pan_number"      : state.get("pan_number", ""),
        "loan_type"       : state.get("loan_type", "Personal"),
        "loan_amount"     : state.get("loan_amount", 0.0),
        "loan_tenure"     : state.get("loan_tenure", 0),
        "employment_type" : state.get("employment_type", "Salaried"),
        "annual_income"   : state.get("annual_income", 0.0),
        "collateral_type" : state.get("collateral_type", "None"),
        "collateral_value": state.get("collateral_value", 0.0),
        "bureau_score"    : state.get("bureau_score", 0),
        "dti_ratio"       : state.get("dti_ratio", 0.0),
        "foir"            : state.get("foir", 0.0),
        "ltv_ratio"       : state.get("ltv_ratio", 0.0),
        "risk_tier"       : state.get("risk_tier", "medium"),
        "past_default"    : state.get("loan_default", "No"),
    }

    print(f"[Node 4] Loan type: {app_metrics['loan_type']} | "
          f"Amount: Rs {app_metrics['loan_amount']:,.0f} | "
          f"Risk tier: {app_metrics['risk_tier']}")

    # ── Step 1: Build RAG queries ─────────────────────────────────────────────
    queries = build_rag_queries(state)

    # ── Step 2: Retrieve policy chunks ────────────────────────────────────────
    policy_text = retrieve_policy_chunks(queries)

    # ── Step 3: LLM compliance check ─────────────────────────────────────────
    compliance_passed = False
    violations        = []
    applicable_rules  = []
    policy_notes      = ""

    try:
        result = call_llm_compliance_check(policy_text, app_metrics)

        compliance_passed = bool(result.get("compliance_passed", False))
        violations        = result.get("violations", [])
        applicable_rules  = result.get("applicable_rules", [])
        policy_notes      = result.get("policy_notes", "")

        print(f"[Node 4] Compliance passed: {compliance_passed}")
        print(f"[Node 4] Violations found : {len(violations)}")
        if violations:
            for v in violations:
                print(f"[Node 4]   ✗ {v}")

    except Exception as e:
        err = f"Compliance LLM check failed: {e}"
        print(f"[Node 4] ERROR: {err}")
        violations.append(err)
        compliance_passed = False

    return {
        "compliance_passed" : compliance_passed,
        "violations"        : violations,
        "applicable_rules"  : applicable_rules,
        "policy_notes"      : policy_notes,
        "current_node"      : "policy_compliance",
    }