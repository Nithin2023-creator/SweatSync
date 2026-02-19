import json
import os
import re
from crewai import Agent, Task, Crew
from sweatsync.state import SweatSyncState
from sweatsync.llm import get_llm
from sweatsync.models.planner import InteractivePlannerObject, WeekPlan, DayPlan, PlannedExercise

def curator_node(state: SweatSyncState) -> dict:
    """
    Agent C: The Curator (Tactical Matcher).
    Selects specific exercises, filters by safety, and applies boredom protection.
    """
    sho = state["user_sho"]
    manifesto = state["safety_manifesto"]
    blueprint = state["strategic_blueprint"]
    
    # 1. Load Exercise DB
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    with open(os.path.join(data_dir, "exercise_db.json"), "r") as f:
        exercise_db = json.load(f)["exercises"]

    llm = get_llm()
    
    agent = Agent(
        role="Tactical Exercise Matcher",
        goal="Map strategic targets to specific, safe, and engaging exercises.",
        backstory="An expert at exercise selection who ensures variety (Boredom Protection) and strict adherence to safety.",
        llm=llm,
        verbose=True
    )

    # Fail-Safe: Filter Exercise DB in Python BEFORE LLM sees it
    hard_stops = set(manifesto.get("hard_stops", []))
    available_eq = set(sho.get("available_equipment", []))
    force_adaptive = manifesto.get("force_adaptive", False)
    
    filtered_db = []
    for ex in exercise_db:
        # 1. Equipment check
        if not any(eq in available_eq for eq in ex["equipment"]):
            continue
            
        # 2. Hard stop check (matching tags)
        if any(tag in hard_stops for tag in ex["tags"]):
            continue
            
        # 3. Adaptive check (if force_adaptive is true, only allow seated/supine)
        if force_adaptive:
            if ex["position"] not in ["seated", "supine"]:
                continue
        
        filtered_db.append(ex)

    # Pass relevant DB to LLM (simplified list to save tokens)
    db_summary = [{"id": ex["id"], "name": ex["name"], "muscle": ex["muscle_group"], "tags": ex["tags"], "pos": ex["position"]} for ex in filtered_db]

    # Muscle Coverage Audit
    muscles_in_db = set(ex["muscle"] for ex in db_summary)
    critical_groups = ["quadriceps", "hamstrings", "glutes", "chest", "back", "shoulders"]
    missing_groups = [g for g in critical_groups if g not in muscles_in_db]
    
    audit_note = ""
    if missing_groups:
        audit_note = f"WARNING: No safe exercises found in DB for: {', '.join(missing_groups)}. Use alternatives for these muscle groups where possible."

    all_weeks = []
    exercise_history = [] # For variety tracking across sessions

    for week_num in range(1, 8):
        print(f"--- CURATOR GENERATING WEEK {week_num} ---")
        
        # Determine phase based on week number
        if week_num <= 3: phase = "accumulation"
        elif week_num <= 6: phase = "intensification"
        else: phase = "deload"

        task = Task(
            description=(
                f"Strategic Blueprint: {json.dumps(blueprint)}\n"
                f"Safety Manifesto: {json.dumps(manifesto)}\n"
                f"Exercise DB: {json.dumps(db_summary)}\n"
                f"{audit_note}\n\n"
                f"Task: Generate exercises for WEEK {week_num} ({phase} phase).\n"
                "CRITICAL CONSTRAINTS:\n"
                f"1. SAFETY: DO NOT use any exercise that involves movements listed in hard_stops: {manifesto.get('hard_stops', [])}.\n"
                f"2. EQUIPMENT: Use ONLY available equipment: {sho.get('available_equipment', [])}.\n"
                "3. VARIETY (HARD): You MUST pull different exercise IDs from the DB for consecutive sessions hitting same muscles. DO NOT repeat the same workout every day.\n"
                "4. MUSCLE TARGETS: Look at the Strategic Blueprint's training_split. If Day 1 is 'Upper Body', ensure you include chest, back, and shoulders. If 'Lower Body', include glutes, hamstrings, or quads (where safe).\n"
                "5. OUTPUT: Return valid JSON matching this schema: {\"days\": {\"day_1\": {\"day_label\": \"...\", \"exercises\": [{\"exercise_id\": \"...\", \"sets\": 3, \"reps\": \"...\", \"rpe\": ...}]}}}"
            ),
            expected_output=f"Safe JSON for Week {week_num}",
            agent=agent
        )

        crew = Crew(agents=[agent], tasks=[task], verbose=False) # Reduce noise
        result = crew.kickoff()
        
        raw_res = str(result)
        try:
            match = re.search(r'\{.*\}', raw_res, re.DOTALL)
            if match:
                week_data = json.loads(match.group())
                
                # Post-process exercises for this week
                days_dict = week_data.get("days", {})
                for day_id in sorted(days_dict.keys()):
                    day = days_dict[day_id]
                    current_day_ids = []
                    
                    for ex in day.get("exercises", []):
                        eid = ex.get("exercise_id")
                        
                        # Variety Post-Processor: If repeated from previous session, try to swap
                        if eid in exercise_history[-5:]: # Check last 5 exercises
                            db_match = next((x for x in filtered_db if x["id"] == eid), None)
                            if db_match:
                                muscle = db_match["muscle_group"]
                                # Find alternative for same muscle that isn't in history
                                alt = next((x for x in filtered_db if x["muscle_group"] == muscle and x["id"] not in exercise_history[-10:]), None)
                                if alt:
                                    ex["exercise_id"] = alt["id"]
                                    eid = alt["id"]
                        
                        db_ex = next((x for x in exercise_db if x["id"] == eid), None)
                        if db_ex:
                            ex["anatomy_url"] = db_ex["anatomy_url"]
                            ex["heatmap_url"] = db_ex["heatmap_url"]
                            ex["name"] = db_ex["name"]
                            ex["equipment"] = ", ".join(db_ex["equipment"])
                            current_day_ids.append(eid)
                    
                    exercise_history.extend(current_day_ids)
                
                all_weeks.append({
                    "week_number": week_num,
                    "phase": phase,
                    "days": days_dict
                })
            else:
                raise ValueError(f"No JSON in Week {week_num}")
        except Exception as e:
            print(f"Curator Error Week {week_num}: {e}")
            all_weeks.append({"week_number": week_num, "phase": phase, "days": {}, "error": str(e)})

    planner_obj = InteractivePlannerObject(
        weeks=all_weeks,
        safety_manifesto=manifesto,
        metadata={"total_weeks": 7, "experience": sho["experience_level"]}
    )

    return {"interactive_planner": planner_obj.dict()}
