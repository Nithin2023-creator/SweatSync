from langgraph.graph import StateGraph, START, END
from sweatsync.state import SweatSyncState
from sweatsync.agents.scout import scout_node
from sweatsync.agents.physio import physio_node
from sweatsync.agents.strategist import strategist_node
from sweatsync.agents.librarian import librarian_node
from sweatsync.agents.auditor import auditor_node

def safety_check(state: SweatSyncState):
    """
    Conditional edge logic: 
    - If Auditor says no, and we haven't looped too much, go back to Librarian.
    - Otherwise, finish.
    """
    if not state.get("is_verified", False):
        if state.get("revision_count", 0) < 3:
            print(f"--- SAFETY VIOLATION DETECTED: {state.get('violations')} ---")
            print(f"--- REVISING (Attempt {state.get('revision_count')}) ---")
            return "librarian"
    return END

def create_sweatsync_graph():
    # Initialize graph with state definition
    workflow = StateGraph(SweatSyncState)

    # Add nodes
    workflow.add_node("scout", scout_node)
    workflow.add_node("physio", physio_node)
    workflow.add_node("strategist", strategist_node)
    workflow.add_node("librarian", librarian_node)
    workflow.add_node("auditor", auditor_node)

    # Add linear flow
    workflow.add_edge(START, "scout")
    workflow.add_edge("scout", "physio")
    workflow.add_edge("physio", "strategist")
    workflow.add_edge("strategist", "librarian")
    workflow.add_edge("librarian", "auditor")

    # Add conditional edge for the Safety Loop
    workflow.add_conditional_edges(
        "auditor",
        safety_check,
        {
            "librarian": "librarian",
            END: END
        }
    )

    return workflow.compile()
