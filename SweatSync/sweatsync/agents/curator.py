import json
import os
import re
import time
from crewai import Agent, Task, Crew
from sweatsync.state import SweatSyncState
from sweatsync.llm import get_llm
from sweatsync.models.planner import InteractivePlannerObject, WeekPlan, DayPlan, PlannedExercise
from sweatsync.agents.architect import parse_timeline_to_weeks

from sweatsync.exercise_fetcher import (
    fetch_exercises_by_body_part, 
    fetch_exercises_by_equipment, 
    get_cached_exercise_by_name
)

# Semantic mapping from Blueprint Splits to ExerciseDB Body Parts
SPLIT_TO_BODY_PARTS = {
    "Upper Body": ["chest", "back", "upper arms", "shoulders"],
    "Lower Body": ["upper legs", "lower legs", "waist"],
    "Push": ["chest", "shoulders", "upper arms"],
    "Pull": ["back", "upper arms"],
    "Legs": ["upper legs", "lower legs", "waist"],
    "Full Body": ["chest", "back", "upper legs", "shoulders", "upper arms", "waist"],
    "Extra Workout": ["cardio"],
}

def curator_node(state: SweatSyncState) -> dict:
    """
    Agent C: The Curator (Tactical Matcher).
    Selects specific exercises, filters by safety, and applies boredom protection.
    """
    sho = state["user_sho"]
    manifesto = state["safety_manifesto"]
    blueprint = state["strategic_blueprint"]
    total_weeks = parse_timeline_to_weeks(sho.get("target_timeline", "7 weeks"))
    
    # 1. Build Dynamic Exercise Pool via ExerciseDB
    hard_stops = set(manifesto.get("hard_stops", []))
    raw_eq = sho.get("available_equipment", ["body weight"])
    # Map raw frontend equipment to ExerciseDB expected equivalents roughly
    eq_map = {"dumbbells": "dumbbell", "barbells": "barbell", "kettlebells": "kettlebell"}
    available_eq = [eq_map.get(eq.lower(), eq.lower()) for eq in raw_eq]
    if not available_eq: available_eq = ["body weight"]
    
    exercise_pool = []
    seen_ids = set()

    # Determine required body parts from Blueprint split
    training_split = blueprint.get("training_split", {})
    unique_labels = set()
    for macros in training_split.values():
        for macro in macros:
            unique_labels.add(macro)
            
    for label in unique_labels:
        if label in ["Rest", "Recovery"]: continue
        
        body_parts = SPLIT_TO_BODY_PARTS.get(label, ["cardio"])
        for bp in body_parts:
            bp_exercises = fetch_exercises_by_body_part(bp, limit=20)
            
            for ex in bp_exercises:
                # Hard stops check mapping
                if ex.get("bodyPart") in hard_stops or ex.get("target") in hard_stops: 
                    continue
                # Equipment check logic (If "body weight", allow it always)
                ex_eq = ex.get("equipment", "")
                if ex_eq != "body weight" and not any(user_eq in ex_eq for user_eq in available_eq):
                    continue
                    
                if ex["id"] not in seen_ids:
                    exercise_pool.append(ex)
                    seen_ids.add(ex["id"])

    # Fallback if pool is empty/too small due to strict equipment filtering
    if len(exercise_pool) < 20:
        for eq in available_eq:
            eq_exercises = fetch_exercises_by_equipment(eq, limit=20)
            for ex in eq_exercises:
                if ex.get("bodyPart") not in hard_stops and ex["id"] not in seen_ids:
                    exercise_pool.append(ex)
                    seen_ids.add(ex["id"])

    # Send curated summary to LLM (HEAVILY reduced to 25 and compacted to fit VERY tight TPM limits)
    db_summary = [f"{ex['name']} ({ex['target']}, {ex.get('equipment', 'body weight')})" for ex in exercise_pool[:25]]

    provider = state.get("provider", "groq")
    llm = get_llm(provider=provider)
    
    agent = Agent(
        role="Tactical Exercise Matcher",
        goal="Map strategic targets to specific, safe, and engaging exercises.",
        backstory="An expert at exercise selection who ensures variety (Boredom Protection) and strict adherence to safety.",
        llm=llm,
        verbose=True
    )

    # Muscle Coverage Audit (Simplified since we map body parts)
    muscles_in_db = set(ex.get("target") for ex in exercise_pool)
    critical_groups = ["pectorals", "lats", "glutes", "quads", "hamstrings", "delts"]
    missing_groups = [g for g in critical_groups if g not in muscles_in_db]
    
    audit_note = ""
    if missing_groups:
        audit_note = f"WARNING: No safe exercises found in DB for: {', '.join(missing_groups)}. Use alternatives for these muscle groups where possible."

    all_weeks = []
    exercise_history = [] # For variety tracking across sessions

    for week_num in range(1, total_weeks + 1):
        print(f"--- CURATOR GENERATING WEEK {week_num}/{total_weeks} ---")
        
        # Determine phase based on relative position in plan
        accum_end = max(1, int(total_weeks * 0.6))
        intense_end = max(accum_end + 1, int(total_weeks * 0.9))
        if week_num <= accum_end: phase = "Build"
        elif week_num <= intense_end: phase = "Push"
        else: phase = "Recover"

        # Create a tiny version of the blueprint for the prompt to save tokens
        slim_blueprint = {
            "training_split": blueprint.get("training_split", {}),
            "weekly_volumes": blueprint.get("weekly_volumes", [])[:8], # Cap volumes
            "periodization_this_week": [w for w in blueprint.get("periodization", []) if w.get("week_number") == week_num]
        }

        task = Task(
            description=(
                f"Blueprint: {json.dumps(slim_blueprint)}\n"
                f"Manifesto: {json.dumps(manifesto)}\n"
                f"Exercise DB: {json.dumps(db_summary)}\n"
                f"{audit_note}\n\n"
                f"Task: Generate exercises for WEEK {week_num} ({phase} phase).\n"
                "CRITICAL CONSTRAINTS:\n"
                f"1. SAFETY: DO NOT use movements in hard_stops: {manifesto.get('hard_stops', [])}.\n"
                f"2. EQUIPMENT: Use ONLY: {sho.get('available_equipment', [])}.\n"
                "3. VARIETY: Use different exercises from the DB for consecutive sessions hitting same muscles.\n"
                "4. MUSCLE TARGETS: Respect training_split. If Day 1 is 'Upper Body', include chest, back, shoulders.\n"
                "5. REST DAYS: If labeled 'Rest' or 'Recovery', \"exercises\" MUST be [].\n"
                "6. OUTPUT: JSON: {\"days\": {\"day_1\": {\"day_label\": \"...\", \"exercises\": [{\"name\": \"...\", \"sets\": 3, \"reps\": \"12\", \"rpe\": ...}]}}}."
            ),
            expected_output=f"Safe JSON for Week {week_num}",
            agent=agent
        )

        max_retries = 3
        week_success = False
        
        for attempt in range(max_retries):
            try:
                crew = Crew(agents=[agent], tasks=[task], verbose=False) # Reduce noise
                result = crew.kickoff()
                
                raw_res = str(result)
                match = re.search(r'\{.*\}', raw_res, re.DOTALL)
                if match:
                    week_data = json.loads(match.group())
                    
                    # Post-process exercises for this week
                    days_dict = week_data.get("days", {})
                    for day_id in sorted(days_dict.keys()):
                        day = days_dict[day_id]
                        current_day_ids = []
                        
                        const_exercises = day.get("exercises", [])
                        if not isinstance(const_exercises, list):
                            const_exercises = []
                            day["exercises"] = []
                        
                        for ex in const_exercises:
                            # Reconstruct robust exercise entity directly from name
                            ex_name_raw = ex.get("name", "")
                            # Extract base name before parentheses if present
                            ex_name = ex_name_raw.split(" (")[0].strip()
                            
                            # We can pull from our permanent cache instantly (populated by exercise_fetcher)
                            cached = get_cached_exercise_by_name(ex_name)
                            if cached:
                                ex["exercise_id"] = cached["id"]
                                ex["anatomy_url"] = "" # Deprecated, replaced by ExerciseDetailModal
                                ex["heatmap_url"] = "" # Deprecated, replaced by ExerciseDetailModal
                                ex["equipment"] = cached.get("equipment", "body weight")
                                ex["target"] = cached.get("target", "None")
                                current_day_ids.append(cached["id"])
                            else:
                                # Fallback if LLM hallunicates
                                ex["exercise_id"] = "custom"
                                ex["anatomy_url"] = ""
                                ex["heatmap_url"] = ""
                                ex["equipment"] = "Various"
                                ex["target"] = "General"
                                current_day_ids.append("custom")
                        
                        exercise_history.extend(current_day_ids)
                    
                    all_weeks.append({
                        "week_number": week_num,
                        "phase": phase,
                        "days": days_dict
                    })
                    week_success = True
                    break # Break out of retry loop on success
                else:
                    raise ValueError(f"No JSON in Week {week_num}")
                    
            except Exception as e:
                err_str = str(e).lower()
                is_rate_limit = ("rate_limit" in err_str or "rate limit" in err_str or "429" in err_str)
                
                if is_rate_limit and attempt < max_retries - 1:
                    wait_time = 61 # Wait a full minute for TPM to reset
                    print(f"Rate limited on week {week_num}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                elif attempt < max_retries - 1:
                    # Non-rate-limit error (e.g. JSON parse error due to truncation)
                    print(f"Curator Error Week {week_num} (Attempt {attempt+1}): {e}. Retrying in 5s...")
                    time.sleep(5)
                else:
                    # Max retries reached or catastrophic error
                    print(f"Curator FINAL Error Week {week_num}: {e}")
                    all_weeks.append({"week_number": week_num, "phase": phase, "days": {}, "error": str(e)})
                    break # Break retry loop
                    
        if not week_success and len(all_weeks) < week_num:
             all_weeks.append({"week_number": week_num, "phase": phase, "days": {}, "error": "Max retries exceeded"})

        # Forced RPM/TPM cooldown between weeks to prevent Groq API exhaustion
        if week_num < total_weeks:
            print(f"Cooling down for 50s to avoid Groq rate limits between weeks...")
            time.sleep(50)

    planner_obj = InteractivePlannerObject(
        weeks=all_weeks,
        safety_manifesto=manifesto,
        metadata={"total_weeks": total_weeks, "experience": sho["experience_level"]}
    )

    return {"interactive_planner": planner_obj.dict()}
