"""
CrewAI-based workout planning logic using Groq LLM.
"""
from crewai import Agent, Task, Crew
from crewai_tools import BaseTool
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
from typing import Type, Optional
import os

from models import WorkoutPlan, Exercise
from database import ExerciseDatabase


# ============================================================================
# 1. LLM CONFIGURATION
# ============================================================================
# Using Groq API with Llama 3.2 1B model
llm = ChatGroq(
    model="llama-3.2-1b-preview",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.7
)


# ============================================================================
# 2. THE TOOL: ExerciseSearchTool
# ============================================================================
class ExerciseSearchToolInput(BaseModel):
    """Input schema for ExerciseSearchTool."""
    target_muscle: str = Field(..., description="Target muscle group (e.g., chest, back, legs, shoulders)")
    category: str = Field(..., description="Exercise category (e.g., strength, cardio, flexibility)")


class ExerciseSearchTool(BaseTool):
    """Tool to search for exercises in MongoDB by target muscle and category."""
    
    name: str = "exercise_search"
    description: str = (
        "Searches the exercise database for a specific exercise by target muscle and category. "
        "Returns the exercise_id and name from MongoDB. "
        "Use this when you need to find a real exercise ID for a specific movement pattern."
    )
    args_schema: Type[BaseModel] = ExerciseSearchToolInput
    
    def _run(self, target_muscle: str, category: str) -> str:
        """
        Execute the exercise search.
        
        Args:
            target_muscle: Target muscle group
            category: Exercise category
            
        Returns:
            Formatted string with exercise_id and name
        """
        db = ExerciseDatabase()
        try:
            result = db.search_exercise(target_muscle=target_muscle, category=category)
            
            if result:
                return f"Exercise ID: {result['exercise_id']}, Name: {result['name']}"
            else:
                return f"No exercise found for muscle='{target_muscle}' and category='{category}'"
        finally:
            db.close()


# ============================================================================
# 3. THE AGENTS
# ============================================================================
strategist_agent = Agent(
    role="Senior Biomechanist",
    goal="Analyze user profile including injuries and fitness goals to create safe and effective training strategies",
    backstory=(
        "You are a world-renowned biomechanics expert with 20+ years of experience in "
        "injury rehabilitation and athletic performance. You understand movement patterns, "
        "contraindications, and how to design programs that work around limitations while "
        "maximizing results. You provide clear strategic guidance based on individual needs."
    ),
    llm=llm,
    verbose=True,
    allow_delegation=False
)

developer_agent = Agent(
    role="Program Designer",
    goal="Design workout intent and structure based on strategic rules without selecting specific exercises",
    backstory=(
        "You are an elite strength and conditioning coach who specializes in program design. "
        "You understand movement patterns (horizontal push/pull, vertical push/pull, hinge, squat, etc.) "
        "and how to structure workouts for optimal results. You create the blueprint of the workout "
        "by defining what types of movements should be included, but you don't pick specific exercises yet."
    ),
    llm=llm,
    verbose=True,
    allow_delegation=False
)

linker_agent = Agent(
    role="Data Specialist",
    goal="Map workout intent to actual exercise IDs from the database using the exercise search tool",
    backstory=(
        "You are a meticulous data specialist who bridges the gap between program design and "
        "implementation. You take the workout blueprint and find the exact exercises from the database "
        "that match each movement pattern. You use the exercise_search tool to find real MongoDB IDs "
        "and ensure every exercise in the plan is actionable and exists in the system."
    ),
    llm=llm,
    verbose=True,
    allow_delegation=False,
    tools=[ExerciseSearchTool()]
)


# ============================================================================
# 4. THE TASKS
# ============================================================================
def create_strategy_task(user_profile: str) -> Task:
    """Create the strategy analysis task."""
    return Task(
        description=(
            f"Analyze this user profile:\n{user_profile}\n\n"
            "Based on this information, create a comprehensive strategy document that includes:\n"
            "1. Key considerations for injuries or limitations\n"
            "2. Appropriate exercise selection guidelines\n"
            "3. Recommended intensity and volume parameters\n"
            "4. Movement patterns to emphasize or avoid\n"
            "5. Overall training approach for their goal\n\n"
            "Provide clear, actionable strategic rules for the program designer."
        ),
        expected_output="A detailed strategy document with safety guidelines and training approach",
        agent=strategist_agent
    )


def create_design_task() -> Task:
    """Create the workout design task."""
    return Task(
        description=(
            "Based on the strategic rules provided, design the INTENT of a workout program.\n\n"
            "For each exercise slot, specify:\n"
            "- Movement pattern type (e.g., 'Horizontal Push', 'Vertical Pull', 'Squat Pattern')\n"
            "- Target muscle group (e.g., 'chest', 'back', 'legs')\n"
            "- Exercise category (e.g., 'strength', 'cardio')\n"
            "- Recommended sets and reps\n"
            "- Rest periods\n"
            "- Any special notes or modifications\n\n"
            "Create 5-7 exercise slots. DO NOT select specific exercise names or IDs yet - "
            "just define what TYPE of exercise should go in each slot."
        ),
        expected_output="A workout blueprint with exercise slots defined by movement patterns and parameters",
        agent=developer_agent
    )


def create_linking_task() -> Task:
    """Create the exercise linking task with Pydantic output."""
    return Task(
        description=(
            "Take the workout blueprint and use the exercise_search tool to find real exercises "
            "from the database for each slot.\n\n"
            "For each exercise slot:\n"
            "1. Use the exercise_search tool with the target_muscle and category specified\n"
            "2. Extract the exercise_id and name from the search results\n"
            "3. Combine this with the sets, reps, rest, and notes from the blueprint\n\n"
            "Then create a complete WorkoutPlan with:\n"
            "- strategy_summary: Brief summary of the strategic approach\n"
            "- exercises: List of Exercise objects with real IDs and complete parameters\n"
            "- total_duration_minutes: Estimated total workout time\n"
            "- difficulty_level: Beginner, Intermediate, or Advanced\n"
            "- special_considerations: Any important notes or warnings\n\n"
            "CRITICAL: Output must conform to the WorkoutPlan Pydantic model structure."
        ),
        expected_output="A complete WorkoutPlan object with all exercises linked to database IDs",
        agent=linker_agent,
        output_pydantic=WorkoutPlan
    )


# ============================================================================
# 5. THE EXECUTION CLASS
# ============================================================================
class WorkoutGenerator:
    """Main class for generating workout plans using CrewAI."""
    
    def __init__(self):
        """Initialize the workout generator."""
        self.exercise_tool = ExerciseSearchTool()
    
    def generate_plan(self, user_profile: str) -> WorkoutPlan:
        """
        Generate a complete workout plan based on user profile.
        
        Args:
            user_profile: Text description of user's goals, injuries, experience level, etc.
            
        Returns:
            WorkoutPlan object with exercises linked to database IDs
        """
        # Create tasks
        strategy_task = create_strategy_task(user_profile)
        design_task = create_design_task()
        linking_task = create_linking_task()
        
        # Create crew with sequential process
        crew = Crew(
            agents=[strategist_agent, developer_agent, linker_agent],
            tasks=[strategy_task, design_task, linking_task],
            verbose=True
        )
        
        # Execute the crew
        result = crew.kickoff()
        
        # The result should be a WorkoutPlan thanks to output_pydantic
        if isinstance(result, WorkoutPlan):
            return result
        else:
            # Fallback: try to parse result as WorkoutPlan
            return WorkoutPlan.model_validate_json(str(result))


# ============================================================================
# EXAMPLE USAGE
# ============================================================================
if __name__ == "__main__":
    # Example user profile
    user_profile = """
    Name: John Doe
    Age: 35
    Experience: Intermediate (2 years training)
    Goal: Build muscle and improve strength
    Injuries: Previous lower back strain (recovered), should avoid heavy deadlifts
    Preferences: Prefers compound movements, trains 4x per week
    """
    
    # Generate workout plan
    generator = WorkoutGenerator()
    plan = generator.generate_plan(user_profile)
    
    # Print results
    print("\n" + "="*80)
    print("GENERATED WORKOUT PLAN")
    print("="*80)
    print(f"\nStrategy: {plan.strategy_summary}")
    print(f"Difficulty: {plan.difficulty_level}")
    print(f"Duration: {plan.total_duration_minutes} minutes")
    print(f"\nExercises:")
    for i, exercise in enumerate(plan.exercises, 1):
        print(f"\n{i}. {exercise.name}")
        print(f"   ID: {exercise.exercise_id}")
        print(f"   Sets: {exercise.sets} | Reps: {exercise.reps} | Rest: {exercise.rest_seconds}s")
        if exercise.notes:
            print(f"   Notes: {exercise.notes}")
    
    if plan.special_considerations:
        print(f"\nSpecial Considerations: {plan.special_considerations}")
