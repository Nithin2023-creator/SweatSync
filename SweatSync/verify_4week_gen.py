import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the project root to sys.path
sys.path.append('/home/vitwit/Nithin/SweatSync-V2/SweatSync')

load_dotenv('/home/vitwit/Nithin/SweatSync-V2/SweatSync/.env')

from sweatsync.state import SweatSyncState
from sweatsync.agents.architect import architect_node
from sweatsync.agents.curator import curator_node

async def verify_generation():
    state: SweatSyncState = {
        "user_sho": {
            "target_timeline": "4 weeks",
            "experience_level": "intermediate",
            "available_equipment": ["dumbbells", "barbells"],
            "training_days_per_week": 4
        },
        "safety_manifesto": {
            "hard_stops": [],
            "force_adaptive": False
        },
        "provider": "groq"
    }
    
    print("--- Starting Architect ---")
    arch_res = architect_node(state)
    state.update(arch_res)
    
    print("--- Starting Curator ---")
    # Curator is synchronous in current implementation but uses asyncio.to_thread internally for fetchers
    cur_res = curator_node(state)
    state.update(cur_res)
    
    planner = state.get("interactive_planner")
    if not planner:
        print("FAILED: No interactive_planner found")
        return
    
    weeks = planner.get("weeks", [])
    print(f"Total Weeks Generated: {len(weeks)}")
    
    for i, week in enumerate(weeks):
        days = week.get("days", {})
        day_count = len([d for d in days.values() if d.get("exercises")])
        print(f"Week {i+1} ({week.get('phase')}): {day_count} training days")
        if week.get("error"):
            print(f"  ERROR: {week.get('error')}")

if __name__ == "__main__":
    asyncio.run(verify_generation())
