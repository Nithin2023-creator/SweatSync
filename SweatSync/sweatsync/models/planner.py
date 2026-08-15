from pydantic import BaseModel, BeforeValidator
from typing import List, Dict, Any, Annotated
from sweatsync.models.manifesto import SafetyManifesto

# Use Annotated and BeforeValidator to coerce any input to string
FlexibleString = Annotated[str, BeforeValidator(lambda v: str(v) if v is not None else "")]

class PlannedExercise(BaseModel):
    exercise_id: str
    name: str
    sets: int
    reps: FlexibleString
    rpe: float
    equipment: str
    anatomy_url: str = ""
    heatmap_url: str = ""

class DayPlan(BaseModel):
    day_label: str       # e.g. "Push Day"
    exercises: List[PlannedExercise] = []

class WeekPlan(BaseModel):
    week_number: int
    phase: str
    days: Dict[str, DayPlan]  # "day_1" → DayPlan

class InteractivePlannerObject(BaseModel):
    weeks: List[WeekPlan]
    safety_manifesto: SafetyManifesto
    metadata: Dict[str, Any]
