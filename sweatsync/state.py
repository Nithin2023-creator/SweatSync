from typing import TypedDict, List, Optional

class SweatSyncState(TypedDict):
    """
    Main state for the SweatSync Agentic Engine.
    Tracks everything from user profile to the final verified plan.
    """
    user_profile: dict        # age, weight, goals, injuries
    equipment_list: List[str] # available gym equipment extracted by Scout
    safety_rules: List[str]   # forbidden movements from Physio
    draft_plan: dict          # 7-day workout schedule
    is_verified: bool         # Auditor safety pass/fail
    revision_count: int       # Iteration tracking for safety loop
    safety_summary: str       # Physio's final narrative result
    violations: List[str]     # Auditor's identified issues (if any)
