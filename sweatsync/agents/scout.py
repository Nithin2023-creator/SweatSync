from crewai import Agent, Task, Crew
from sweatsync.state import SweatSyncState
from sweatsync.llm import get_llm

def scout_node(state: SweatSyncState) -> dict:
    """
    Scout Node: Analyzes user goals and extracts available equipment.
    """
    llm = get_llm()
    
    agent = Agent(
        role="Equipment Scout",
        goal="Identify available gym equipment and user fitness level.",
        backstory="Expert at parsing messy user input to extract concrete gym equipment lists.",
        llm=llm,
        allow_delegation=False,
        verbose=True
    )
    
    task = Task(
        description=(
            "Based on this user profile: {profile}\n"
            "Identify all available equipment mentioned. "
            "If none mentioned, assume 'bodyweight only'. "
            "Output valid JSON like: {{\"equipment\": [\"list\", \"of\", \"items\"]}}"
        ),
        expected_output="JSON list of equipment",
        agent=agent
    )
    
    # Run crew (single agent for now as specified in graph design)
    crew = Crew(agents=[agent], tasks=[task], verbose=True)
    result = crew.kickoff(inputs={"profile": state["user_profile"]})
    
    # Simple JSON extraction logic (robust for 1b model)
    import json
    import re
    
    raw_res = str(result)
    try:
        match = re.search(r'\{.*\}', raw_res, re.DOTALL)
        if match:
            data = json.loads(match.group())
            equipment = data.get("equipment", [])
        else:
            equipment = ["bodyweight"]
    except:
        equipment = ["bodyweight"]
        
    return {"equipment_list": equipment}
