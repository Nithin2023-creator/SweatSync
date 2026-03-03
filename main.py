import json
import sys
from sweatsync.graph import create_sweatsync_graph
from sweatsync.agents.interviewer import run_onboarding

def main():
    # 1. Gather Structured Health Object (SHO)
    if "--demo" in sys.argv:
        print("--- RUNNING IN DEMO MODE (HARDCODED SHO) ---")
        sample_sho = {
            "age": 32,
            "weight_kg": 85.0,
            "height_cm": 178.0,
            "sex": "male",
            "goals": "Build muscle and increase strength. Focus on longevity.",
            "training_days_per_week": 4,
            "allowed_days": ["monday", "tuesday", "thursday", "friday"],
            "experience_level": "intermediate",
            "target_timeline": "3 months",
            "available_equipment": ["squat_rack", "barbell", "dumbbells", "bench"],
            "medical_flags": ["disc_bulge", "knee_injury"],
            "injuries_description": "Lower back pain (disc bulge L4-L5), sensitive right knee when squatting deep."
        }
    else:
        sample_sho = run_onboarding()
        if not sample_sho:
            print("Onboarding aborted. Exiting.")
            sys.exit(0)
        
        print(f"\n✅ SHO successfully generated:")
        print(json.dumps(sample_sho, indent=2))
        print("\n")
    # 2. Initialize state
    initial_state = {
        "user_sho": sample_sho,
        "safety_manifesto": {},
        "strategic_blueprint": {},
        "interactive_planner": {},
        "revision_count": 0,
        "conflict_detected": False,
        "max_revisions": 2
    }

    # 3. Create and Run Graph
    print("--- STARTING SWEATSYNC AGENTIC ENGINE (3-AGENT PIPELINE) ---")
    app = create_sweatsync_graph()
    
    # Run the graph
    final_output = app.invoke(initial_state)

    # 4. Extract Final Planner
    planner = final_output.get("interactive_planner", {})

    # 5. Output to Terminal and File
    print("\n--- FINAL 7-WEEK WORKOUT PLANNER GENERATED ---")
    # Pretty print summary (top level)
    print(f"Experience Level: {planner.get('metadata', {}).get('experience', 'N/A')}")
    print(f"Safety Status: {planner.get('safety_manifesto', {}).get('safety_narrative', 'N/A')[:200]}...")
    
    with open("sweatsync_result.json", "w") as f:
        json.dump(planner, f, indent=2)
    print("\nComplete 7-week plan saved to sweatsync_result.json")

if __name__ == "__main__":
    main()
