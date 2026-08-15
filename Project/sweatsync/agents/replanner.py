"""
Replanner Agent: Handles structural plan changes like skipping weeks,
adding/removing days, and volume compensation.
"""
import json
import re
from sweatsync.llm import get_llm
from langchain_core.messages import SystemMessage, HumanMessage


def classify_intent(prompt: str, llm=None, provider="groq") -> str:
    """
    Classify user intent into: simple_edit | question | replan
    Uses fast keyword heuristics to avoid an extra LLM round-trip.
    """
    p = prompt.lower().strip()

    # --- Replan signals (structural changes) ---
    replan_patterns = [
        r'\bskip\b', r'\bcancel\b', r'\bremove week\b', r'\bdelete week\b',
        r'\badd.*week\b', r'\bextend\b', r'\breschedule\b', r'\brestructure\b',
        r'\brearrange\b', r'\bshift.*week\b', r'\bmove.*week\b',
        r'\bswap.*week\b', r'\bmerge.*week\b', r'\bsplit.*week\b',
        r'\bweek\s*\d+', r'\bremove.*day\b', r'\badd.*day\b',
        r'\bi\s*can\'?t.*train\b', r'\bi\s*won\'?t.*available\b',
        r'\brecover\b', r'\bdeload\b',
    ]
    for pat in replan_patterns:
        if re.search(pat, p):
            return "replan"

    # --- Question signals ---
    question_patterns = [
        r'^(what|why|how|when|which|where|who|is|are|do|does|can|could|should|will|would)\b',
        r'\?\s*$',
        r'\bexplain\b', r'\btell me\b', r'\bdescribe\b',
        r'\bwhat.*muscle\b', r'\bwhy.*exercise\b', r'\bhow.*work\b',
    ]
    for pat in question_patterns:
        if re.search(pat, p):
            return "question"

    # Default: treat as simple edit (swap, change reps, adjust, etc.)
    return "simple_edit"


def build_replan_prompt(
    user_message: str,
    plan: dict,
    sho: dict,
    safety_manifesto: dict,
    context: dict
) -> tuple:
    """
    Build system + user prompts for the replanner agent.
    Returns (system_prompt, user_prompt) tuple.
    """

    # Strip URLs from plan to save tokens
    def strip_urls(obj):
        if isinstance(obj, dict):
            obj.pop("anatomy_url", None)
            obj.pop("heatmap_url", None)
            for v in obj.values():
                strip_urls(v)
        elif isinstance(obj, list):
            for x in obj:
                strip_urls(x)

    clean_plan = json.loads(json.dumps(plan))
    strip_urls(clean_plan)

    # Build compact plan summary
    weeks_summary = []
    for w in clean_plan.get("weeks", []):
        days = w.get("days", {})
        day_info = []
        total_exercises = 0
        for dk, dv in days.items():
            exs = dv.get("exercises", [])
            total_exercises += len(exs)
            label = dv.get("day_label", dk)
            day_info.append(f"{dk}: {label} ({len(exs)} ex)")
        weeks_summary.append(
            f"Week {w.get('week_number', '?')} ({w.get('phase', '?')}): "
            f"{total_exercises} total exercises | {', '.join(day_info)}"
        )

    system_prompt = f"""You are SweatSync Replanner — an expert fitness coach who restructures workout plans.

USER PROFILE:
- Goals: {sho.get('goals', 'General fitness')}
- Training days/week: {sho.get('training_days_per_week', 3)}
- Experience: {sho.get('experience_level', 'beginner')}
- Equipment: {json.dumps(sho.get('available_equipment', []))}
- Medical flags: {json.dumps(sho.get('medical_flags', []))}

SAFETY MANIFESTO:
{json.dumps(safety_manifesto)}

CURRENT PLAN OVERVIEW:
{chr(10).join(weeks_summary)}

RULES:
1. When user skips a week, mark it as a rest week (empty exercises) and REDISTRIBUTE its volume across remaining active weeks.
2. Compensation must respect: RPE ceilings, user's available training days, and safety constraints.
3. If the user skips multiple weeks, consider extending the plan timeline rather than overloading.
4. ALWAYS maintain the same JSON structure for each week.
5. Keep exercise_id references from the original plan (do NOT invent new IDs).
6. Return "reps" as strings (e.g., "12" or "8-12").
7. Do NOT include anatomy_url or heatmap_url (server restores them).
8. Be direct and specific in your reply — tell the user exactly what changed.

Return valid json:
{{
  "reply": "Direct explanation of what changed and how you compensated",
  "action": "replan",
  "preview": {{
    "skipped_weeks": [list of 1-indexed week numbers skipped],
    "affected_weeks": [list of 1-indexed week numbers that received extra volume],
    "compensation": "Brief description of compensation strategy"
  }},
  "updated_weeks": {{
     "0": {{ ... modified week 1 object ... }},
     "3": {{ ... modified week 4 object ... }}
  }}
}}

ONLY include weeks in 'updated_weeks' that have actually changed. 
The keys MUST be the 0-based string indices of the weeks in the original 'weeks' list."""

    user_prompt = f"""User says: {user_message}

Context: Viewing {context.get('level', 'weeks')} level, Week {(context.get('week_index', 0) or 0) + 1}

FULL CURRENT PLAN (modify this):
{json.dumps(clean_plan)}"""

    return system_prompt, user_prompt


def execute_replan(
    user_message: str,
    plan: dict,
    sho: dict,
    safety_manifesto: dict,
    context: dict,
    provider: str = "groq"
) -> dict:
    """
    Execute the replanning agent synchronously.
    Returns the response dict with reply, action, preview, and updated_plan.
    """
    llm = get_llm(provider=provider)
    system_prompt, user_prompt = build_replan_prompt(
        user_message, plan, sho, safety_manifesto, context
    )

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])

        match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if match:
            data = json.loads(match.group())
            return data
        else:
            return {
                "reply": "I couldn't process that replan request. Please try again.",
                "action": "error",
                "updated_plan": plan
            }
    except Exception as e:
        print(f"Replanner error: {e}")
        return {
            "reply": f"Replanning failed: {str(e)}",
            "action": "error",
            "updated_plan": plan
        }
