from crewai import Agent, Task, Crew
from sweatsync.state import SweatSyncState
from sweatsync.llm import get_llm

def auditor_node(state: SweatSyncState) -> dict:
    """
    Auditor Node: Verifies the plan against safety and equipment rules.
    """
    llm = get_llm()
    
    agent = Agent(
        role="Safety Auditor",
        goal="Verify that the workout plan is 100% safe and uses only available equipment.",
        backstory="Cynical safety inspector who hates safety violations and incorrect equipment usage.",
        llm=llm,
        allow_delegation=False,
        verbose=True
    )
    
    task = Task(
        description=(
            "Check this plan: {plan}\n"
            "Safety Rules: {rules}\n"
            "Available Equipment: {equipment}\n"
            "If it violates any rule or uses unavailable equipment, set verified to false and list violations. "
            "Output JSON: {{\"verified\": true/false, \"violations\": [\"list\"]}}"
        ),
        expected_output="JSON audit result",
        agent=agent
    )
    
    crew = Crew(agents=[agent], tasks=[task], verbose=True)
    result = crew.kickoff(inputs={
        "plan": state["draft_plan"],
        "rules": state["safety_rules"],
        "equipment": state["equipment_list"]
    })
    
    import json
    import re
    
    raw_res = str(result)
    try:
        match = re.search(r'\{.*\}', raw_res, re.DOTALL)
        if match:
            audit = json.loads(match.group())
            verified = audit.get("verified", False)
            violations = audit.get("violations", [])
        else:
            verified = False
            violations = ["Audit parsing failed"]
    except:
        verified = False
        violations = ["Audit error"]
        
    return {"is_verified": verified, "violations": violations}
