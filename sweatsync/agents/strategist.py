from crewai import Agent, Task, Crew
from sweatsync.state import SweatSyncState
from sweatsync.llm import get_llm

def strategist_node(state: SweatSyncState) -> dict:
    """
    Strategist Node: Designs the 7-day workout split skeleton.
    """
    llm = get_llm()
    
    agent = Agent(
        role="Fitness Strategist",
        goal="Design a 7-day workout split tailored to user goals and safety constraints.",
        backstory="Expert coach known for creating optimal training volume and recovery cycles.",
        llm=llm,
        allow_delegation=False,
        verbose=True
    )
    
    task = Task(
        description=(
            "Goals: {goals}\n"
            "Safety Rules: {rules}\n"
            "Design a 7-day split (e.g., Push/Pull/Legs or Full Body).\n"
            "Output JSON: {{\"day_1\": \"focus\", ..., \"day_7\": \"focus\"}}"
        ),
        expected_output="JSON 7-day split focus",
        agent=agent
    )
    
    crew = Crew(agents=[agent], tasks=[task], verbose=True)
    result = crew.kickoff(inputs={
        "goals": state["user_profile"].get("goals", "General fitness"),
        "rules": state["safety_rules"]
    })
    
    import json
    import re
    
    raw_res = str(result)
    try:
        match = re.search(r'\{.*\}', raw_res, re.DOTALL)
        if match:
            plan = json.loads(match.group())
        else:
            plan = {"error": "failed to generate split"}
    except:
        plan = {"error": "failed to generate split"}
        
    return {"draft_plan": plan}
