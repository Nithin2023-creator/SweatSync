from langgraph.graph import StateGraph, END
from sweatsync.state import SweatSyncState
from sweatsync.agents.guardian import guardian_node
from sweatsync.agents.architect import architect_node
from sweatsync.agents.curator import curator_node

def check_conflicts(state: SweatSyncState) -> str:
    """
    Conditional edge: check if Architect's output conflicts with Guardian's stops.
    Also verifies frequency budget (e.g. 4 days/month target).
    """
    blueprint = state.get("strategic_blueprint", {})
    sho = state.get("user_sho", {})
    manifesto = state.get("safety_manifesto", {})
    
    # 1. Frequency Budget Check
    days_per_week = sho.get("training_days_per_week", 3)
    # Correcting for Month/Week terminology from user feedback (4 days/month = 1 day/week)
    # The SHO in main.py currently has 4 days_per_week, but if it were month, we'd scale it.
    actual_days = [d for d, m in blueprint.get("training_split", {}).items() if m != ["Rest"] and m != ["Recovery"]]
    
    if len(actual_days) != days_per_week:
        # Potentially set a conflict flag to trigger revision
        return "revise"

    # 2. Safety manifesto check
    hard_stops = set(manifesto.get("hard_stops", []))
    for day, muscles in blueprint.get("training_split", {}).items():
        if any(stop in " ".join(muscles).lower() for stop in hard_stops):
            return "revise"

    if state.get("revision_count", 0) >= state.get("max_revisions", 2):
        return "proceed"
        
    return "proceed"

def create_sweatsync_graph():
    """Build the 3-agent SweatSync graph."""
    graph = StateGraph(SweatSyncState)

    # Add nodes
    graph.add_node("guardian", guardian_node)
    graph.add_node("architect", architect_node)
    graph.add_node("curator", curator_node)

    # Define workflow
    graph.set_entry_point("guardian")
    graph.add_edge("guardian", "architect")
    
    # Conditional edge from architect to check conflicts (simplified loop for now)
    graph.add_conditional_edges(
        "architect",
        check_conflicts,
        {
            "revise": "architect", # In a real scenario, feedback would be added to state
            "proceed": "curator"
        }
    )
    
    graph.add_edge("curator", END)

    return graph.compile()
