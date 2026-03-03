import json
import re
from typing import Optional
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from sweatsync.llm import get_llm
from sweatsync.models.sho import StructuredHealthObject

SYSTEM_PROMPT = """
You are the "Onboarding Interviewer" for SweatSync, an elite, adaptive fitness AI. 
Your objective is to converse with the user to gather their physical metrics, fitness goals, and crucial medical constraints.

# Response Format (MANDATORY)
You MUST ALWAYS respond in a strict JSON format. 
{
  "conversational_message": "...",
  "suggested_options": ["Option 1", "Option 2"],
  "input_type": "text" | "numeric" | "single_select" | "multi_select",
  "expecting_user_input": true,
  "is_final": false,
  "sho_payload": null
}

# Input Type Rules:
- USE "numeric" for age, weight, and height. 
- USE "single_select" for sex, experience level, and single-choice goals.
- USE "multi_select" for training days (Monday-Sunday) and available equipment.
- NEVER ask the user to "reply with a number". Provide the full labels in `suggested_options`.

# Conversation Rules
1. **One Step at a Time:** Ask 1 or 2 logical questions at a time.
2. **The "Dynamic Probe":** If the user mentions ANY pain or injury, ask follow-up questions to determine the exact nature.
3. **Equipment Check:** Verify what equipment they have access to.
4. **Schedule Check:** Ask explicitly which days of the week they can train.

# Required Data Gathering (Internal Tracking)
- Age (int), Weight (kg), Height (cm), Sex (male/female/other)
- Goals (summary), Allowed Days (list), Training Days/Week (int)
- Experience Level (beginner/intermediate/advanced)
- Target Timeline (string), Available Equipment (list)
- Medical Flags (array of keys), Injuries Description (text)

# KNOWN MEDICAL FLAGS
Map injuries to: `disc_bulge`, `knee_injury`, `shoulder_impingement`, `paralysis_lower`, `paralysis_upper`, `cardiac_risk`.

# KNOWN EQUIPMENT KEYS
Map to: `squat_rack`, `barbell`, `dumbbells`, `bench`, `cable_machine`, `machine`, `bodyweight`, `bands`, `kettlebells`.

# Examples:
- Asking age: {"conversational_message": "How old are you?", "suggested_options": [], "input_type": "numeric", "expecting_user_input": true, "is_final": false, "sho_payload": null}
- Asking days: {"conversational_message": "Which days can you train?", "suggested_options": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], "input_type": "multi_select", "expecting_user_input": true, "is_final": false, "sho_payload": null}

# END GOAL: THE SHO PAYLOAD
When finished, set `is_final` to true and include the `sho_payload`:
{
    "age": 32,
    "weight_kg": 85.0,
    "height_cm": 178.0,
    "sex": "male",
    "goals": "...",
    "training_days_per_week": 4,
    "allowed_days": ["monday", "..."],
    "experience_level": "intermediate",
    "target_timeline": "3 months",
    "available_equipment": ["dumbbells", "..."],
    "medical_flags": ["..."],
    "injuries_description": "..."
}
"""

def extract_and_validate_sho(text: str) -> Optional[dict]:
    """Helper to extract the JSON block and validate the sho_payload."""
    try:
        # The entire text should now be a valid JSON string from the LLM
        # We try to find a JSON block if there's any surrounding text
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if not match:
            return None
            
        data = json.loads(match.group())
        if data.get("is_final") and data.get("sho_payload"):
            sho_data = data["sho_payload"]
            # Validate with Pydantic
            sho_obj = StructuredHealthObject(**sho_data)
            return sho_obj.dict()
    except Exception as e:
        print(f"\n[System: Failed to parse/validate JSON. Error: {e}]")
        return None
    return None

def run_onboarding() -> dict:
    """Run the conversational onboarding and return a validated SHO dict."""
    llm = get_llm()
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    
    print("\n" + "="*60)
    print("🤖 STARTING SWEATSYNC AI ONBOARDING")
    print("="*60)

    # Trigger first LLM greeting
    response = llm.invoke(messages)
    messages.append(response)
    print(f"\n🏋️ SweatSync: {response.content}\n")
    
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ['quit', 'exit']:
                print("\nExiting onboarding early.")
                return {}
                
            messages.append(HumanMessage(content=user_input))
            
            # Show typing indicator
            print("🏋️ SweatSync is thinking...", end="\r")
            
            response = llm.invoke(messages)
            messages.append(response)
            
            # Clear typing indicator
            print(" "*30, end="\r")
            
            # Check if LLM output the final JSON payload
            if "===SHO_JSON===" in response.content:
                # Strip the JSON from the user-facing print
                clean_msg = response.content.split("===SHO_JSON===")[0].strip()
                print(f"\n🏋️ SweatSync: {clean_msg}\n")
                
                sho_dict = extract_and_validate_sho(response.content)
                if sho_dict:
                    return sho_dict
                else:
                    # Extraction failed, prompt LLM to fix it
                    err_msg = HumanMessage(content="System Error: The JSON provided was invalid or incomplete. Please output the ===SHO_JSON=== block again with corrections.")
                    messages.append(err_msg)
            else:
                # Normal conversation turn
                print(f"\n🏋️ SweatSync: {response.content}\n")
                
        except KeyboardInterrupt:
            print("\n\nOnboarding interrupted by user.")
            return {}
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            return {}
