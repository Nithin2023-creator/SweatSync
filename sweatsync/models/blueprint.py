from pydantic import BaseModel
from typing import List, Dict, Optional

class WeeklyVolume(BaseModel):
    muscle_group: str
    sets_per_week: int
    rep_range: str         # e.g. "8-12"
    rpe_target: float      # 7.0-9.0
    frequency: int         # sessions per week hitting this group

class PeriodizationWeek(BaseModel):
    week_number: int       # 1-7
    phase: str             # "accumulation" | "intensification" | "deload"
    volume_modifier: float # 1.0, 1.1, 0.6, etc.
    rpe_ceiling: float     # max RPE for this week

class StrategicBlueprint(BaseModel):
    training_split: Dict[str, List[str]]  # day → muscle groups
    weekly_volumes: List[WeeklyVolume]
    periodization: List[PeriodizationWeek]
    redistributions: List[str]  # notes on volume reallocation
    conflict_found: bool = False
    conflict_notes: Optional[str] = None
