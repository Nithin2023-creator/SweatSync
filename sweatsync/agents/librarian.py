from crewai import Agent, Task, Crew
from sweatsync.state import SweatSyncState
from sweatsync.llm import get_llm

def librarian_node(state: SweatSyncState) -> dict:
    """
    Librarian Node: Selects exercises based on equipment and safety rules.
    """
    llm = get_llm()
    
    agent = Agent(
        role="Exercise Librarian",
        goal="Select safe exercises that ONLY use available equipment.",
        backstory="Master of exercise databases who strictly follows equipment and safety constraints.",
        llm=llm,
        allow_delegation=False,
        verbose=True
    )
    
    task = Task(
        description=(
            "Split: {plan}\n"
            "Equipment: {equipment}\n"
            "Forbidden: {forbidden}\n"
            "Fill the split with specific exercises. STRICTLY FILTER by available equipment. "
            "AVOID forbidden movements. Output JSON: {{\"day_1\": [{{ \"ex\": \"name\", \"sets\": \"X\", \"reps\": \"Y\", \"eq\": \"item\" }}], ...}}"
        ),
        expected_output="JSON 7-day detailed plan",
        agent=agent
    )
    
    crew = Crew(agents=[agent], tasks=[task], verbose=True)
    result = crew.kickoff(inputs={
        "plan": state["draft_plan"],
        "equipment": state["equipment_list"],
        "forbidden": state["safety_rules"]
    })
    
    import json
    import re
    
    raw_res = str(result)
    try:
        match = re.search(r'\{.*\}', raw_res, re.DOTALL)
        if match:
            detailed_plan = json.loads(match.group())
        else:
            detailed_plan = state["draft_plan"] # fallback
    except:
        detailed_plan = state["draft_plan"]
        
    return {"draft_plan": detailed_plan, "revision_count": state.get("revision_count", 0) + 1}
