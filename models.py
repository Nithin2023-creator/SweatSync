"""
Pydantic models for workout planning system.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class Exercise(BaseModel):
    """Represents a single exercise in the workout plan."""
    exercise_id: str = Field(..., description="MongoDB ObjectId of the exercise")
    name: str = Field(..., description="Exercise name")
    sets: int = Field(..., description="Number of sets")
    reps: int = Field(..., description="Number of repetitions per set")
    rest_seconds: int = Field(..., description="Rest time in seconds between sets")
    notes: Optional[str] = Field(None, description="Additional notes or modifications")


class WorkoutPlan(BaseModel):
    """Complete workout plan with exercises and metadata."""
    strategy_summary: str = Field(..., description="Strategic approach based on user profile")
    exercises: List[Exercise] = Field(..., description="List of exercises in the workout")
    total_duration_minutes: int = Field(..., description="Estimated total workout duration")
    difficulty_level: str = Field(..., description="Difficulty level: Beginner, Intermediate, or Advanced")
    special_considerations: Optional[str] = Field(None, description="Any special considerations or warnings")
