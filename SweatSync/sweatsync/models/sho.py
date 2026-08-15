from pydantic import BaseModel
from typing import List

class StructuredHealthObject(BaseModel):
    age: int
    weight_kg: float
    height_cm: float
    sex: str  # "male" | "female" | "other"
    goals: str  # free-text goal description
    training_days_per_week: int  # 2-6
    allowed_days: List[str] = [] # e.g. ["monday", "tuesday", "thursday", "friday"]
    experience_level: str  # "beginner" | "intermediate" | "advanced"
    target_timeline: str  # e.g. "3 months", "12 weeks"
    available_equipment: List[str]
    medical_flags: List[str]  # keys from contraindications.json
    injuries_description: str  # free-text for LLM context
