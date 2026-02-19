import json
import os
from crewai import Agent, Task, Crew
from sweatsync.state import SweatSyncState
from sweatsync.llm import get_llm
from sweatsync.models.blueprint import StrategicBlueprint, WeeklyVolume, PeriodizationWeek

def architect_node(state: SweatSyncState) -> dict:
    """
    Agent B: The Architect (Mathematical Strategist).
    Calculates volume, frequency, intensity, and periodization.
    Performs Metabolic Redistribution.
    """
    sho = state["user_sho"]
    manifesto = state["safety_manifesto"]
    
    llm = get_llm()
    
    agent = Agent(
        role="Mathematical Fitness Strategist",
        goal="Calculate optimal hypertrophy volume and periodization while adhering to strict safety constraints.",
        backstory="A data-driven coach who uses mathematical models to optimize training stimulus and recovery.",
        llm=llm,
        verbose=True
    )

    # Context for LLM
    redistribution_note = ""
    if manifesto.get("force_adaptive") and manifesto.get("redistributed_from"):
        redistribution_note = f"METABOLIC REDISTRIBUTION REQUIRED: {manifesto['redistributed_from']} is non-functional. Reallocate that volume to viable muscle groups."

    # 1. Pre-compute training split based on frequency
    days_per_week = sho.get("training_days_per_week", 3)
    
    # Simple split logic
    if days_per_week <= 3:
        # Full Body split
        split_template = {
            "day_1": ["Full Body"],
            "day_2": ["Rest"],
            "day_3": ["Full Body"],
            "day_4": ["Rest"],
            "day_5": ["Full Body"],
            "day_6": ["Rest"],
            "day_7": ["Recovery"]
        }
    elif days_per_week == 4:
        # Upper/Lower split
        split_template = {
            "day_1": ["Upper Body"],
            "day_2": ["Lower Body"],
            "day_3": ["Rest"],
            "day_4": ["Upper Body"],
            "day_5": ["Lower Body"],
            "day_6": ["Rest"],
            "day_7": ["Recovery"]
        }
    else:
        # PPL (Push/Pull/Legs)
        split_template = {
            "day_1": ["Push"],
            "day_2": ["Pull"],
            "day_3": ["Legs"],
            "day_4": ["Push"],
            "day_5": ["Pull"],
            "day_6": ["Legs"],
            "day_7": ["Recovery"]
        }
    
    # Adjust training days to match exactly days_per_week if needed
    training_days = [d for d, m in split_template.items() if m != ["Rest"] and m != ["Recovery"]]
    if len(training_days) > days_per_week:
        for i in range(days_per_week, len(training_days)):
            split_template[training_days[i]] = ["Rest"]
    elif len(training_days) < days_per_week:
        rest_days = [d for d, m in split_template.items() if m == ["Rest"]]
        for i in range(min(days_per_week - len(training_days), len(rest_days))):
            split_template[rest_days[i]] = ["Extra Workout"]

    task = Task(
        description=(
            f"User Profile: {json.dumps(sho)}\n"
            f"Safety Constraints: {json.dumps(manifesto)}\n"
            f"PRE-COMPUTED SPLIT (HARD CONSTRAINT): {json.dumps(split_template)}\n"
            f"{redistribution_note}\n\n"
            "Task: Create a 7-week Strategic Blueprint.\n"
            f"1. RED ALERT: You MUST use the pre-computed training split provided above. DO NOT add or remove training days. The user trains EXACTLY {days_per_week} days/week.\n"
            "2. Calculate weekly sets per muscle group (Hypertrophy Math). Ensure reasonable progressive overload (max 10-15% volume increase between weeks).\n"
            "3. Define 7-week periodization: Weeks 1-3 Accumulation (RPE 7-8), Weeks 4-6 Intensification (RPE 8-9), Week 7 Deload (RPE 5-6).\n"
            "4. Output valid JSON mapping to the StrategicBlueprint model."
        ),
        expected_output="JSON matching StrategicBlueprint model structure",
        agent=agent
    )

    crew = Crew(agents=[agent], tasks=[task], verbose=True)
    result = crew.kickoff()
    
    import re
    raw_res = str(result)
    try:
        match = re.search(r'\{.*\}', raw_res, re.DOTALL)
        if match:
            blueprint_data = json.loads(match.group())
            # Enforce pre-computed split in case LLM hallucinations
            blueprint_data["training_split"] = split_template
            blueprint = StrategicBlueprint(**blueprint_data)
        else:
            raise ValueError("No JSON found in Architect output")
    except Exception as e:
        # Fallback split
        blueprint = StrategicBlueprint(
            training_split=split_template,
            weekly_volumes=[WeeklyVolume(muscle_group="General", sets_per_week=10, rep_range="8-12", rpe_target=8, frequency=days_per_week)],
            periodization=[PeriodizationWeek(week_number=i, phase="accumulation", volume_modifier=1.0, rpe_ceiling=8) for i in range(1, 8)],
            redistributions=["Fallback due to parsing error"]
        )

    return {"strategic_blueprint": blueprint.dict()}
