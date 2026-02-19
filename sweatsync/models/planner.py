from pydantic import BaseModel
from typing import List, Dict, Any
from sweatsync.models.manifesto import SafetyManifesto

class PlannedExercise(BaseModel):
    exercise_id: str
    name: str
    sets: int
    reps: str
    rpe: float
    equipment: str
    anatomy_url: str
    heatmap_url: str

class DayPlan(BaseModel):
    day_label: str       # e.g. "Push Day"
    exercises: List[PlannedExercise]

class WeekPlan(BaseModel):
    week_number: int
    phase: str
    days: Dict[str, DayPlan]  # "day_1" → DayPlan

class InteractivePlannerObject(BaseModel):
    weeks: List[WeekPlan]
    safety_manifesto: SafetyManifesto
    metadata: Dict[str, Any]
