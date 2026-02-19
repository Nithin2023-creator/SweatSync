from pydantic import BaseModel
from typing import List, Optional

class SafetyManifesto(BaseModel):
    hard_stops: List[str]         # forbidden movement tags
    modifications: List[str]      # equipment/posture requirements
    safe_positions: List[str]     # allowed exercise positions
    force_adaptive: bool          # True if paralysis flag present
    redistributed_from: Optional[str]  # e.g. "lower_body"
    safety_narrative: str         # human-readable summary
