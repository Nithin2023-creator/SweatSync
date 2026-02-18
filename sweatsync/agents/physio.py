from crewai import Agent, Task, Crew
from sweatsync.state import SweatSyncState
from sweatsync.llm import get_llm

def physio_node(state: SweatSyncState) -> dict:
    """
    Physio Node: Analyzes injuries and defines forbidden movements.
    """
    llm = get_llm()
    
    agent = Agent(
        role="Sports Physiotherapist",
        goal="Ensure workout safety by identifying high-risk movements for the user's injuries.",
        backstory="Top-tier physio specializing in injury prevention and rehabilitation.",
        llm=llm,
        allow_delegation=False,
        verbose=True
    )
    
    task = Task(
        description=(
            "User injuries/conditions: {injuries}\n"
            "Identify 'Forbidden Movements' that could aggravate these injuries. "
            "Also provide a 'Safety Summary' narrative for the user.\n"
            "Output JSON: {{\"forbidden\": [\"movements\"], \"summary\": \"advice\"}}"
        ),
        expected_output="JSON containing forbidden movements and safety summary",
        agent=agent
    )
    
    crew = Crew(agents=[agent], tasks=[task], verbose=True)
    result = crew.kickoff(inputs={"injuries": state["user_profile"].get("injuries", "None")})
    
    import json
    import re
    
    raw_res = str(result)
    try:
        match = re.search(r'\{.*\}', raw_res, re.DOTALL)
        if match:
            data = json.loads(match.group())
            forbidden = data.get("forbidden", [])
            summary = data.get("summary", "No specific safety concerns identified.")
        else:
            forbidden = []
            summary = "No specific safety concerns identified."
    except:
        forbidden = []
        summary = "No specific safety concerns identified."
        
    return {"safety_rules": forbidden, "safety_summary": summary}
