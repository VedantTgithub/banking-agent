import json
import os
from typing import Dict, Any
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from agent.state import AgentState

load_dotenv()

# ── LLM Client ────────────────────────────────────────────────────────────────
HF_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")
MODEL_ID  = os.getenv("HF_MODEL_ID", "Qwen/Qwen2.5-7B-Instruct")

client = InferenceClient(
    api_key=HF_TOKEN,
)


def call_llm(doc_text: str) -> Dict[str, Any]:
    """
    Calls HuggingFace chat_completion API.
    Returns parsed dict with extracted_name and extracted_income.
    """
    system_prompt = (
        "You are a banking document extraction assistant. "
        "You must respond ONLY with a valid JSON object. "
        "No explanation, no markdown, no code blocks. Just raw JSON."
    )

    user_prompt = f"""Extract the following from the document text below:
1. The applicant full name
2. The annual income as a plain number (digits only, no commas, no symbols, no currency sign)

Return ONLY this JSON format:
{{"extracted_name": "Full Name Here", "extracted_income": 000000}}

If a field is not found, use null.

Document Text:
{doc_text[:3000]}"""

    response = client.chat_completion(
        model=MODEL_ID,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        max_tokens=256,
        temperature=0.1,
    )

    raw = response.choices[0].message.content.strip()
    print(f"[Node 1] Raw LLM response: {raw}")

    # Clean markdown fences if model added them
    if "```" in raw:
        parts = raw.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                raw = part
                break

    # Extract JSON object
    start = raw.find("{")
    end   = raw.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError(f"No JSON found in response: {raw}")

    return json.loads(raw[start:end])


def run(state: AgentState) -> Dict[str, Any]:
    """
    Node 1: Document Verification
    Extracts name + income from uploaded doc text via LLM.
    Cross-checks extracted name against applicant name.
    """
    print("\n--- NODE 1: DOCUMENT VERIFICATION ---")

    raw_text      = state.get("uploaded_doc_text", "").strip()
    expected_name = state.get("applicant_name", "").strip()

    extracted_name   = ""
    extracted_income = 0.0
    missing_docs     = []
    doc_flags        = []

    # ── Step 1: Check document exists ─────────────────────────────────────────
    if not raw_text:
        print("[Node 1] No document text found.")
        missing_docs.append("Income / Salary document is missing")
        return {
            "doc_verified":    False,
            "extracted_name":  "",
            "extracted_income": 0.0,
            "missing_docs":    missing_docs,
            "doc_flags":       doc_flags,
            "current_node":    "document_verification",
        }

    # ── Step 2: LLM Extraction ─────────────────────────────────────────────────
    print(f"[Node 1] Calling LLM: {MODEL_ID}")
    try:
        data = call_llm(raw_text)

        raw_name   = data.get("extracted_name")
        raw_income = data.get("extracted_income")

        extracted_name   = str(raw_name).strip() if raw_name else "Not Found"
        extracted_income = float(raw_income)     if raw_income else 0.0

        print(f"[Node 1] Extracted name:   {extracted_name}")
        print(f"[Node 1] Extracted income: {extracted_income}")

    except Exception as e:
        print(f"[Node 1] LLM call failed: {e}")
        doc_flags.append(f"LLM extraction failed: {str(e)}")
        extracted_name   = "Extraction Failed"
        extracted_income = 0.0

    # ── Step 3: Name cross-check ───────────────────────────────────────────────
    if expected_name and extracted_name not in ["Not Found", "Extraction Failed"]:
        if (expected_name.lower() in extracted_name.lower() or
                extracted_name.lower() in expected_name.lower()):
            print(f"[Node 1] Name match OK: '{expected_name}' ~ '{extracted_name}'")
        else:
            flag = (f"Name mismatch: application says '{expected_name}' "
                    f"but document says '{extracted_name}'")
            doc_flags.append(flag)
            print(f"[Node 1] WARNING: {flag}")

    # ── Step 4: Income check ───────────────────────────────────────────────────
    declared_income = state.get("annual_income", 0.0)

    if extracted_income == 0.0:
        doc_flags.append("Could not extract income from document")
    elif declared_income > 0:
        margin = 0.05 * declared_income
        if abs(extracted_income - declared_income) > margin:
            flag = f"Income mismatch: declared ₹{declared_income:,.2f} but document says ₹{extracted_income:,.2f}"
            doc_flags.append(flag)
            print(f"[Node 1] WARNING: {flag}")
        else:
            print(f"[Node 1] Income match OK: declared ₹{declared_income:,.2f} ~ extracted ₹{extracted_income:,.2f}")

    doc_verified = len(doc_flags) == 0 and len(missing_docs) == 0
    print(f"[Node 1] doc_verified = {doc_verified}")

    return {
        "doc_verified":    doc_verified,
        "extracted_name":  extracted_name,
        "extracted_income": extracted_income,
        "missing_docs":    missing_docs,
        "doc_flags":       doc_flags,
        "current_node":    "document_verification",
    }