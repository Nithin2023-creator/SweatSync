import json
import os
from crewai import Agent, Task, Crew
from sweatsync.state import SweatSyncState
from sweatsync.llm import get_llm
from sweatsync.models.manifesto import SafetyManifesto

def guardian_node(state: SweatSyncState) -> dict:
    """
    Agent A: The Guardian (Clinical Gatekeeper).
    Identifies medical Red Flags and generates a Safety Manifesto.
    """
    sho = state["user_sho"]
    
    # 1. Load Contraindications Library
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    with open(os.path.join(data_dir, "contraindications.json"), "r") as f:
        library = json.load(f)["conditions"]

    # 2. Hard-code rule merging logic
    hard_stops = set()
    modifications = set()
    safe_positions = set(["any", "seated", "standing", "supine", "prone"]) # start with all
    force_adaptive = False
    redistributed_from = None

    for flag in sho.get("medical_flags", []):
        if flag in library:
            cond = library[flag]
            hard_stops.update(cond.get("hard_stop", []))
            modifications.update(cond.get("modifications", []))
            
            # Intersection of safe positions
            flag_positions = set(cond.get("safe_positions", []))
            if "any" not in flag_positions:
                safe_positions = safe_positions.intersection(flag_positions)
            
            if cond.get("force_adaptive"):
                force_adaptive = True
                # Heuristic: if lower_body restricted, redistribute from lower
                if "all_lower_body" in cond.get("hard_stop", []):
                    redistributed_from = "lower_body"
                elif "all_upper_body" in cond.get("hard_stop", []):
                    redistributed_from = "upper_body"

    # 3. Use Agent for nuanced narrative and catching missed flags in free-text
    llm = get_llm()
    
    agent = Agent(
        role="Clinical Gatekeeper",
        goal="Ensure absolute safety by identifying all medical risks and movement contraindications.",
        backstory="A world-class sports physio and clinical safety officer with absolute veto power.",
        llm=llm,
        verbose=True
    )

    task = Task(
        description=(
            f"Analyze this patient SHO: {json.dumps(sho)}\n"
            f"Injuries listed: {sho.get('injuries_description')}\n"
            f"Base Hard Stops: {list(hard_stops)}\n"
            f"Base Modifications: {list(modifications)}\n"
            "Identify if any additional movements should be stopped based on the free-text description. "
            "Write a concise Safety Manifesto narrative for the user."
        ),
        expected_output="JSON with 'additional_hard_stops', 'additional_modifications', and 'narrative'",
        agent=agent
    )

    crew = Crew(agents=[agent], tasks=[task], verbose=True)
    result = crew.kickoff()
    
    # Simple JSON extraction (robust for 1b/8b)
    import re
    raw_res = str(result)
    try:
        match = re.search(r'\{.*\}', raw_res, re.DOTALL)
        if match:
            data = json.loads(match.group())
            hard_stops.update(data.get("additional_hard_stops", []))
            modifications.update(data.get("additional_modifications", []))
            narrative = data.get("narrative", "Follow standard safety precautions.")
        else:
            narrative = "Follow standard safety precautions."
    except:
        narrative = "Follow standard safety precautions."

    manifesto = SafetyManifesto(
        hard_stops=list(hard_stops),
        modifications=list(modifications),
        safe_positions=list(safe_positions),
        force_adaptive=force_adaptive,
        redistributed_from=redistributed_from,
        safety_narrative=narrative
    )

    return {"safety_manifesto": manifesto.dict()}
