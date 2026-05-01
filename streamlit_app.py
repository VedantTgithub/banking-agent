import sys
import os
import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from tools.ocr_tool import extract_text_from_uploaded_file
from agent.graph import loan_agent_app
from agent.state import AgentState

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Loan Underwriting Agent",
    page_icon="🏦",
    layout="centered"
)

st.title("🏦 Loan Underwriting Agent")
st.caption("🚀 Powered by LangGraph | Smart Short-Circuiting & Early Termination Enabled")

st.divider()

# ── Input form ─────────────────────────────────────────────────────────────────
st.header("📋 Applicant & Loan Details")

with st.container(border=True):
    st.subheader("👤 Section 1 — Personal Details")
    col1, col2 = st.columns(2)
    with col1:
        applicant_name = st.text_input("Full Name (as per documents)", placeholder="e.g. Vedant Sharma")
        pan_number     = st.text_input("PAN Number", placeholder="e.g. ABCDE1234F")
    with col2:
        dob = st.date_input(
            "Date of Birth",
            min_value=datetime.date.today().replace(year=datetime.date.today().year - 100),
            max_value=datetime.date.today(),
            value=datetime.date.today().replace(year=datetime.date.today().year - 30),
        )

with st.container(border=True):
    st.subheader("💰 Section 2 — Loan Details")
    col1, col2 = st.columns(2)
    with col1:
        loan_amount  = st.number_input("Loan Amount (₹)", min_value=0.0, step=10000.0)
        loan_type    = st.selectbox("Loan Type", ["Home", "Personal", "Business", "Vehicle"])
    with col2:
        loan_tenure  = st.slider("Loan Tenure (Years)", min_value=1, max_value=30, value=10)
        loan_purpose = st.text_input("Purpose of Loan", placeholder="e.g. Buying a house")

with st.container(border=True):
    st.subheader("💼 Section 3 — Employment & Income")
    col1, col2 = st.columns(2)
    with col1:
        employment_type    = st.selectbox("Employment Type", ["Salaried", "Self-Employed", "Business Owner"])
        employer_name      = st.text_input("Employer / Company Name", placeholder="e.g. Tech Corp")
    with col2:
        annual_income      = st.number_input("Declared Annual Income (₹)", min_value=0.0, step=10000.0)
        years_at_employer  = st.number_input("Years at Current Employer", min_value=0, step=1)

with st.container(border=True):
    st.subheader("💳 Section 4 — Financial Obligations")
    col1, col2 = st.columns(2)
    with col1:
        existing_emi  = st.number_input("Existing Monthly EMI (₹)", min_value=0.0, step=1000.0)
        active_loans  = st.number_input("Number of Active Loans", min_value=0, step=1)
    with col2:
        loan_default  = st.radio("Any Loan Default in Past?", ["Yes", "No"], index=1, horizontal=True)

with st.container(border=True):
    st.subheader("🏠 Section 5 — Collateral")
    col1, col2 = st.columns(2)
    with col1:
        collateral_type        = st.selectbox("Collateral Type", ["Property", "Gold", "FD", "Vehicle", "None"])
        collateral_value       = st.number_input("Collateral Value (₹)", min_value=0.0, step=10000.0)
    with col2:
        collateral_description = st.text_area("Collateral Description", placeholder="e.g. 2BHK flat in Mumbai", height=68)

st.subheader("📂 Section 6 — Documents Upload")
uploaded_file = st.file_uploader(
    "Upload Salary Slip / Income Document (PDF only)",
    type=["pdf"]
)

run_button = st.button("🚀 Run AI Underwriting Analysis", use_container_width=True, type="primary")

st.divider()

# ── Run pipeline ───────────────────────────────────────────────────────────────
if run_button:
    if not applicant_name.strip():
        st.warning("Please enter the applicant name.")
        st.stop()
    if uploaded_file is None:
        st.warning("Please upload a document.")
        st.stop()

    # 1. OCR Extraction
    with st.spinner("📄 Extracting data from document..."):
        doc_text = extract_text_from_uploaded_file(uploaded_file)
    
    if not doc_text:
        st.error("Could not extract text from the PDF.")
        st.stop()

    # 2. Initial State
    state: AgentState = {
        "application_id"    : f"APP-{datetime.datetime.now().strftime('%Y%m%d%H%M')}",
        "thread_id"         : "thread-demo",
        "applicant_name"    : applicant_name.strip(),
        "pan_number"        : pan_number.strip(),
        "dob"               : str(dob),
        "loan_amount"       : float(loan_amount),
        "loan_type"         : loan_type,
        "loan_tenure"       : int(loan_tenure),
        "loan_purpose"      : loan_purpose.strip(),
        "annual_income"     : float(annual_income),
        "employment_type"   : employment_type,
        "employer_name"     : employer_name.strip(),
        "years_at_employer" : int(years_at_employer),
        "existing_emi"      : float(existing_emi),
        "active_loans"      : int(active_loans),
        "loan_default"      : loan_default,
        "collateral_type"   : collateral_type,
        "collateral_value"  : float(collateral_value),
        "collateral_description": collateral_description.strip(),
        "uploaded_doc_text" : doc_text,
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
        "errors"            : [],
        "messages"          : [],
    }

    # 3. Graph Execution
    with st.status("🧠 AI Agent is evaluating your application...", expanded=True) as status_box:
        for event in loan_agent_app.stream(state, config={"configurable": {"thread_id": "demo"}}):
            for node_name, output in event.items():
                st.write(f"✅ **{node_name.replace('_', ' ').title()}** complete.")
                state.update(output)
        status_box.update(label="🎯 Evaluation Complete!", state="complete", expanded=False)

    # 4. Display Results
    st.header("📊 Analysis Results")
    
    # Identify which nodes were actually run
    nodes_run = []
    if state.get("extracted_name"): nodes_run.append("doc")
    if state.get("bureau_score", 0) > 0: nodes_run.append("credit")
    if state.get("risk_tier"): nodes_run.append("risk")
    if state.get("applicable_rules"): nodes_run.append("policy")
    if state.get("decision"): nodes_run.append("decision")

    tabs = st.tabs(["📄 Doc Check", "💳 Credit", "⚖️ Risk", "📜 Policy", "🏁 Final Verdict"])
    
    with tabs[0]:
        if "doc" in nodes_run:
            if state["doc_verified"]: st.success("Document Verified")
            else: st.error("Verification Issues Found")
            c1, c2 = st.columns(2)
            c1.metric("Name on Doc", state["extracted_name"])
            c2.metric("Income on Doc", f"₹{state['extracted_income']:,.0f}")
            if state["doc_flags"]:
                for f in state["doc_flags"]: st.warning(f"🚩 {f}")
        else:
            st.info("Node skipped.")

    with tabs[1]:
        if "credit" in nodes_run:
            c1, c2, c3 = st.columns(3)
            c1.metric("Bureau Score", state["bureau_score"])
            c2.metric("DTI Ratio", f"{state['dti_ratio']:.1f}%")
            c3.metric("FOIR", f"{state['foir']:.1f}%")
            if state["credit_flags"]:
                for f in state["credit_flags"]: st.warning(f"🚩 {f}")
        else:
            st.info("Node skipped.")

    with tabs[2]:
        if "risk" in nodes_run:
            st.subheader(f"Risk Tier: {state['risk_tier'].upper()}")
            c1, c2, c3 = st.columns(3)
            c1.metric("LTV Ratio", f"{state['ltv_ratio']:.1f}%")
            c2.metric("Collateral Score", f"{state['collateral_score']:.2f}")
            c3.metric("Sector Risk", state["sector_risk"].title())
            if state["risk_flags"]:
                for f in state["risk_flags"]: st.warning(f"🚩 {f}")
        else:
            st.info("Node skipped.")

    with tabs[3]:
        if "policy" in nodes_run:
            if state["compliance_passed"]: st.success("Policy Check Passed")
            else: st.error("Policy Violations Found")
            if state["violations"]:
                for v in state["violations"]: st.error(f"🚫 {v}")
            with st.expander("Rules Checked"):
                for r in state["applicable_rules"]: st.write(f"- {r}")
        else:
            st.info("Node skipped.")

    with tabs[4]:
        if "decision" in nodes_run:
            decision = state["decision"]
            if decision == "APPROVED": st.success(f"## {decision}")
            elif decision == "ESCALATED": st.warning(f"## {decision}")
            else: st.error(f"## {decision}")
            
            st.markdown("### Underwriter Report")
            st.write(state["decision_report"])
            
            if state.get("recommended_terms"):
                with st.expander("📝 Recommended Terms", expanded=True):
                    st.json(state["recommended_terms"])
        else:
            st.warning("Decision not reached.")

    # Summary Table
    st.divider()
    st.subheader("🏁 Quick Summary")
    summary = {
        "Check": ["Verdict", "Doc Match", "Bureau Score", "Risk Tier", "Compliance"],
        "Result": [
            state.get("decision", "Short-Circuited"),
            "✅ Match" if state.get("doc_verified") else "❌ Mismatch/Issue",
            str(state.get("bureau_score", "N/A")),
            state.get("risk_tier", "N/A").upper(),
            "✅ Pass" if state.get("compliance_passed") else "❌ Fail"
        ]
    }
    st.table(summary)