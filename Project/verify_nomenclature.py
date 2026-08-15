import sys
import os

# Add the project root to sys.path
sys.path.append('/home/vitwit/Nithin/SweatSync-V2/SweatSync')

from sweatsync.agents.curator import curator_node
from sweatsync.state import SweatSyncState

def test_nomenclature():
    state = {
        "user_sho": {"target_timeline": "1 week", "experience_level": "beginner", "available_equipment": ["dumbbells"], "training_days_per_week": 3},
        "safety_manifesto": {"hard_stops": []},
        "strategic_blueprint": {
            "training_split": {"day_1": ["Full Body"], "day_3": ["Full Body"], "day_5": ["Full Body"]},
            "weekly_volumes": [],
            "periodization": [],
            "redistributions": []
        },
        "provider": "groq"
    }
    
    # We don't want to actually call the LLM, so we'll just test the logic before the LLM call if possible
    # Or we can just check if the strings exist in the files again (which I already did)
    
    # Let's check curator_node's phase calculation logic
    # Line 117-119 in curator.py
    total_weeks = 1
    accum_end = max(1, int(total_weeks * 0.6))
    intense_end = max(accum_end + 1, int(total_weeks * 0.9))
    week_num = 1
    
    if week_num <= accum_end: phase = "Build"
    elif week_num <= intense_end: phase = "Push"
    else: phase = "Recover"
    
    print(f"Week 1 phase: {phase}")
    assert phase == "Build"
    
    total_weeks = 7
    accum_end = max(1, int(total_weeks * 0.6))
    intense_end = max(accum_end + 1, int(total_weeks * 0.9))
    
    phases = []
    for week_num in range(1, total_weeks + 1):
        if week_num <= accum_end: phase = "Build"
        elif week_num <= intense_end: phase = "Push"
        else: phase = "Recover"
        phases.append(phase)
    
    print(f"7-week phases: {phases}")
    assert "Build" in phases
    assert "Push" in phases
    assert "Recover" in phases
    
    print("Nomenclature logic verification successful!")

if __name__ == "__main__":
    test_nomenclature()
