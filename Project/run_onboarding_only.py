import json
import sys
from sweatsync.agents.interviewer import run_onboarding

def main():
    """
    Run only the onboarding part of the SweatSync engine.
    This script is for testing the conversational data gathering and SHO generation.
    """
    print("--- STARTING SWEATSYNC ONBOARDING TEST ---")
    
    # Run the conversational onboarding
    sho = run_onboarding()
    
    if not sho:
        print("\n❌ Onboarding was aborted or failed to generate a valid SHO.")
        sys.exit(0)
    
    # Print the resulting Structured Health Object (SHO)
    print("\n" + "="*60)
    print("✅ ONBOARDING COMPLETE: STRUCTURED HEALTH OBJECT (SHO) GENERATED")
    print("="*60)
    print(json.dumps(sho, indent=2))
    print("\nTest passed! The SHO is ready for the next stage of the pipeline.")

if __name__ == "__main__":
    main()
