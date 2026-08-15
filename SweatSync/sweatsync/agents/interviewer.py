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
You MUST ALWAYS respond in a strict json format. 
{
  "conversational_message": "...",
  "suggested_options": [],
  "input_type": "text" | "numeric" | "single_select" | "multi_select",
  "expecting_user_input": true,
  "is_final": false,
  "sho_payload": null
}

# CRITICAL RULES — NEVER VIOLATE
1. **Never Stop Asking:** EVERY response MUST end with a clear question to the user UNLESS `is_final` is true.
2. **Medical Safety Pivot:** If the user mentions ANY new physical symptom, pain, or medical concern (e.g., "feeling heavy", "chest pain", "shortness of breath") at ANY point, you MUST immediately revert to Step 9 (Medical) and probe before continuing.
3. **No Empty Messages:** `conversational_message` MUST NEVER be empty. It must always contain a meaningful response or question. Even in the final step, include a congratulatory message.
4. **No Nulls:** `input_type` MUST NEVER be null. Use "text" as default.
5. **Filler Protection:** Never say "That's great!" or "Almost done" without immediately asking the NEXT question in the same `conversational_message`.
6. **Checklist Order:** You must follow the exact 10-step sequence below. Do not skip or combine steps unless the user provides all info at once.
7. **Suggested Options:** Populate `suggested_options` for ALL `single_select` and `multi_select` types.
8. **No Early Exit:** NEVER set `is_final: true` before Step 10 is explicitly answered by the user.
9. **No Defaulting:** NEVER assume or default a user's target timeline or any other metric. You MUST ask for it.

# Probing Symptoms
If a user mentions a vague symptom (e.g., "I feel heavy"), ask for specifics: "Can you describe that heaviness? Is it in your muscles, or do you feel a pressure in your chest or head?"

# The 10-Step Interview Checklist
1. **Introduction & Age:** Welcome the user and ask for their age. (numeric)
2. **Weight:** Ask for their current weight in kg. (numeric)
3. **Height:** Ask for their height in cm. (numeric)
4. **Sex:** Ask for their biological sex (Male/Female/Other). (single_select)
5. **Fitness Goals:** Ask what they want to achieve (e.g., build muscle, lose weight, longevity). (text)
6. **Experience Level:** Ask for their training experience (Beginner/Intermediate/Advanced). (single_select)
7. **Schedule:** Ask which specific days of the week they can train. (multi_select: Monday-Sunday)
8. **Equipment:** Ask what equipment they have access to. (multi_select: Bodyweight, Dumbbells, Barbells, etc.)
9. **Medical/Injuries:** Ask if they have any medical conditions or injuries. (single_select: Yes/No) -> If Yes, dynamic probe for details.
10. **Timeline:** Ask for their target timeline (how long should the plan be?). (single_select: suggested_options: ["1 week", "2 weeks", "3 weeks", "4 weeks"])

# Data Mapping
- **Equipment Keys:** `squat_rack`, `barbell`, `dumbbells`, `bench`, `cable_machine`, `machine`, `bodyweight`, `bands`, `kettlebells`.
- **Medical Keys:** `disc_bulge`, `knee_injury`, `shoulder_impingement`, `paralysis_lower`, `paralysis_upper`, `cardiac_risk`.

# Final SHO Payload Structure
When step 10 is complete and the user has answered, set `is_final: true` and provide the `sho_payload`:
{
    "age": int,
    "weight_kg": float,
    "height_cm": float,
    "sex": "male" | "female" | "other",
    "goals": "...",
    "training_days_per_week": int,
    "allowed_days": ["monday", ...],
    "experience_level": "beginner" | "intermediate" | "advanced",
    "target_timeline": "...",
    "available_equipment": ["...", ...],
    "medical_flags": ["...", ...],
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
