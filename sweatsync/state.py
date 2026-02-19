from typing import TypedDict, List, Dict, Any

class SweatSyncState(TypedDict):
    """Shared state for the 3-agent SweatSync pipeline."""
    user_sho: Dict[str, Any]           # Structured Health Object (Input)
    safety_manifesto: Dict[str, Any]   # Agent A output
    strategic_blueprint: Dict[str, Any] # Agent B output
    interactive_planner: Dict[str, Any] # Agent C output (Final)
    revision_count: int
    conflict_detected: bool
    max_revisions: int
