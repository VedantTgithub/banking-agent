"""
agent/graph.py
LangGraph Orchestrator

Defines the state machine, nodes, and conditional routing logic
for the automated loan underwriting agent.
"""

from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END

from agent.state import AgentState
from agent.nodes import (
    document_verification,
    credit_scoring,
    risk_assessment,
    policy_compliance,
    decision_generation,
)
from memory.checkpointer import get_checkpointer


# ── ROUTERS ──────────────────────────────────────────────────────────────────

def route_after_doc_verification(state: AgentState) -> Literal["credit_scoring", "decision_generation"]:
    """
    Short-circuits if document verification fails.
    """
    if not state.get("doc_verified"):
        print("[Router] Doc verification failed. Short-circuiting to Decision Generation.")
        return "decision_generation"
    return "credit_scoring"

def route_after_credit_scoring(state: AgentState) -> Literal["risk_assessment", "decision_generation"]:
    """
    Short-circuits if a hard reject is triggered in credit scoring.
    """
    if state.get("hard_reject"):
        print("[Router] Hard reject in Credit Scoring. Short-circuiting to Decision Generation.")
        return "decision_generation"
    return "risk_assessment"

def route_after_risk_assessment(state: AgentState) -> Literal["policy_compliance", "decision_generation"]:
    """
    Short-circuits if risk tier is very high.
    """
    if state.get("risk_tier") == "very_high":
        print("[Router] Very High Risk tier detected. Short-circuiting to Decision Generation.")
        return "decision_generation"
    return "policy_compliance"

def route_after_policy_compliance(state: AgentState) -> Literal["decision_generation"]:
    """
    Always goes to decision generation after compliance check.
    If compliance failed, the Decision Node will handle the rejection report.
    """
    if not state.get("compliance_passed"):
         print("[Router] Compliance failed. Proceeding to Decision Generation for final report.")
    return "decision_generation"


# ── GRAPH BUILDING ────────────────────────────────────────────────────────────

def create_graph():
    # 1. Initialize StateGraph
    workflow = StateGraph(AgentState)

    # 2. Add Nodes
    workflow.add_node("document_verification", document_verification.run)
    workflow.add_node("credit_scoring", credit_scoring.run)
    workflow.add_node("risk_assessment", risk_assessment.run)
    workflow.add_node("policy_compliance", policy_compliance.run)
    workflow.add_node("decision_generation", decision_generation.run)

    # 3. Set Entry Point
    workflow.set_entry_point("document_verification")

    # 4. Define Edges with Short-Circuiting logic
    workflow.add_conditional_edges(
        "document_verification",
        route_after_doc_verification,
        {
            "credit_scoring": "credit_scoring",
            "decision_generation": "decision_generation"
        }
    )

    workflow.add_conditional_edges(
        "credit_scoring",
        route_after_credit_scoring,
        {
            "risk_assessment": "risk_assessment",
            "decision_generation": "decision_generation"
        }
    )

    workflow.add_conditional_edges(
        "risk_assessment",
        route_after_risk_assessment,
        {
            "policy_compliance": "policy_compliance",
            "decision_generation": "decision_generation"
        }
    )

    workflow.add_edge("policy_compliance", "decision_generation")
    workflow.add_edge("decision_generation", END)

    # 5. Compile with SQLite persistence
    return workflow.compile(checkpointer=get_checkpointer())

# Export a singleton instance
loan_agent_app = create_graph()
