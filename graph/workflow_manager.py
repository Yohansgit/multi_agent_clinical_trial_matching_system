from typing import Dict, Any
from langgraph.graph import StateGraph, END

from agents.reasoning_engine import hybrid_search_and_reason
from agents.critic_agent import critic_verify
from utils.disk_cache import load, save

class WorkflowState(Dict[str, Any]):
    pass

# -----------------------------
# Nodes
# -----------------------------

def retrieve_node(state: WorkflowState):
    state["candidate_trials"] = hybrid_search_and_reason(
        patient=state["patient"],
        embed_cache=state["embed_cache"],
        top_k=state["max_trials"]
    )
    return state

def fast_filter_node(state: WorkflowState):
    filtered = []

    for t in state["candidate_trials"]:
        if not t["eligible"]:
            filtered.append({**t, "final_eligible": False})
        else:
            filtered.append({**t, "final_eligible": None})

    state["fast_path"] = filtered
    return state

def route(state: WorkflowState):
    if any(t["final_eligible"] is None for t in state["fast_path"]):
        return "critic"
    return "persist"

def critic_node(state: WorkflowState):
    verified = []

    for t in state["fast_path"]:
        if t["final_eligible"] is False:
            verified.append(t)
            continue

        audit = critic_verify(t["Criteria"], t["patient_summary"])

        verified.append({
            **t,
            "final_eligible": t["eligible"] and audit["eligible"],
            "final_reason": audit["reasons"]
        })

    state["verified"] = verified
    return state

def persist_node(state: WorkflowState):
    pid = state["patient"]["patient_id"]

    cached = load("workflow_patient", pid)
    if cached:
        state["final"] = cached
        return state

    result = {
        "patient_id": pid,
        "trials": state.get("verified", state["fast_path"])
    }

    save("workflow_patient", pid, result)
    save("embedding_cache", "global", state["embed_cache"])

    state["final"] = result
    return state

# -----------------------------
# Build Graph
# -----------------------------
def build_workflow():
    g = StateGraph(WorkflowState)

    g.add_node("retrieve", retrieve_node)
    g.add_node("fast", fast_filter_node)
    g.add_node("critic", critic_node)
    g.add_node("persist", persist_node)

    g.set_entry_point("retrieve")
    g.add_edge("retrieve", "fast")

    g.add_conditional_edges(
        "fast",
        route,
        {"critic": "critic", "persist": "persist"}
    )

    g.add_edge("critic", "persist")
    g.add_edge("persist", END)

    return g.compile()

workflow = build_workflow()
