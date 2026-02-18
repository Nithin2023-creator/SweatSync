import json
from sweatsync.graph import create_sweatsync_graph

def main():
    # 1. Define sample user profile
    user_profile = {
        "age": 32,
        "weight": "85kg",
        "goals": "Build muscle and increase strength. 4 days per week.",
        "injuries": "Lower back pain (disc bulge), sensitive right knee.",
        "equipment": "I have a squat rack, barbell, and some dumbbells at home."
    }

    # 2. Initialize state
    initial_state = {
        "user_profile": user_profile,
        "equipment_list": [],
        "safety_rules": [],
        "draft_plan": {},
        "is_verified": False,
        "revision_count": 0,
        "safety_summary": "",
        "violations": []
    }

    # 3. Create and Run Graph
    print("--- STARTING SWEATSYNC AGENTIC ENGINE ---")
    app = create_sweatsync_graph()
    
    # Run the graph
    final_output = app.invoke(initial_state)

    # 4. Generate Clean JSON Artifact
    result_artifact = {
        "verified_7_day_schedule": final_output["draft_plan"],
        "safety_summary": final_output["safety_summary"],
        "equipment_identified": final_output["equipment_list"],
        "safety_status": "VERIFIED" if final_output["is_verified"] else "UNVERIFIED (MAX REVISIONS REACHED)",
        "violations_found": final_output["violations"]
    }

    # 5. Output to Terminal and File
    print("\n--- FINAL OUTPUT GENERATED ---")
    print(json.dumps(result_artifact, indent=2))
    
    with open("sweatsync_result.json", "w") as f:
        json.dump(result_artifact, f, indent=2)
    print("\nResult saved to sweatsync_result.json")

if __name__ == "__main__":
    main()
