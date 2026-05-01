"""
agent/nodes/decision_generation.py
Node 5 — Final Decision Generation

This node runs last. It aggregates all flags, scores, and compliance results
from previous nodes and generates a final loan verdict (APPROVED, REJECTED, or ESCALATED).
"""

import json
import os
from typing import Dict, Any
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from agent.state import AgentState

load_dotenv()

HF_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")
MODEL_ID  = os.getenv("HF_MODEL_ID", "Qwen/Qwen2.5-7B-Instruct")

client = InferenceClient(api_key=HF_TOKEN)

def call_llm_decision_report(state: AgentState, status: str) -> Dict[str, Any]:
    """
    Calls LLM to write a professional final decision report/letter.
    """
    system_prompt = (
        "You are a senior banking underwriting manager. "
        "Your task is to write a final loan decision report. "
        "Respond ONLY with a valid JSON object."
    )

    # Collect all flags
    all_flags = (
        state.get("doc_flags", []) + 
        state.get("credit_flags", []) + 
        state.get("risk_flags", []) + 
        state.get("violations", [])
    )

    user_prompt = f"""Write a final underwriting report for the following application.
    
Status: {status}
Applicant: {state.get('applicant_name')}
Loan: {state.get('loan_type')} loan for Rs {state.get('loan_amount'):,.0f}

Key Metrics:
- Bureau Score: {state.get('bureau_score')}
- Risk Tier: {state.get('risk_tier')}
- Compliance: {'Passed' if state.get('compliance_passed') else 'FAILED'}
- Red Flags identified: {all_flags}

Return ONLY this JSON format:
{{
  "decision_report": "<3-4 sentence professional summary and justification>",
  "confidence": 0.00,
  "recommended_terms": {{
      "rate_adjustment": "+0.5%",
      "notes": "..."
  }}
}}
"""

    response = client.chat_completion(
        model=MODEL_ID,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        max_tokens=512,
        temperature=0.3,
    )

    raw = response.choices[0].message.content.strip()
    
    # Strip markdown
    if "```" in raw:
        for part in raw.split("```"):
            part = part.strip().lstrip("json").strip()
            if part.startswith("{"):
                raw = part
                break

    start = raw.find("{")
    end   = raw.rfind("}") + 1
    return json.loads(raw[start:end])

def run(state: AgentState) -> Dict[str, Any]:
    print("\n--- NODE 5: DECISION GENERATION ---")
    
    # 1. Determine Status based on flags
    doc_issue = not state.get("doc_verified")
    hard_reject = state.get("hard_reject", False)
    risk_tier = state.get("risk_tier", "high")
    compliance_passed = state.get("compliance_passed", True)
    violations = state.get("violations", [])

    status = "APPROVED"
    
    if hard_reject or risk_tier == "very_high" or not compliance_passed or len(violations) > 0:
        status = "REJECTED"
    elif risk_tier == "high" or doc_issue:
        status = "ESCALATED"
    elif risk_tier == "medium":
        status = "APPROVED" # but maybe with conditions
    
    print(f"[Node 5] Final status determined: {status}")

    # 2. Call LLM for formal report
    try:
        report_data = call_llm_decision_report(state, status)
        return {
            "decision": status,
            "decision_report": report_data.get("decision_report", ""),
            "confidence": report_data.get("confidence", 0.9),
            "recommended_terms": report_data.get("recommended_terms", {}),
            "current_node": "decision_generation"
        }
    except Exception as e:
        print(f"[Node 5] LLM report failed: {e}")
        return {
            "decision": status,
            "decision_report": f"Manual {status} decision based on internal flags.",
            "confidence": 1.0,
            "current_node": "decision_generation"
        }
