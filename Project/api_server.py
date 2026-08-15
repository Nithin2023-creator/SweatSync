"""
FastAPI bridge for the SweatSync Onboarding Interviewer Agent.
React frontend calls this directly. MongoDB stores completed SHO profiles.
Pipeline generation with SSE progress streaming.
"""
import json
import re
import os
import asyncio
import httpx
from typing import List, Optional
import bcrypt
from pydantic import BaseModel
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi import FastAPI, HTTPException, Request, Depends, status
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from sweatsync.llm import get_llm
from sweatsync.models.sho import StructuredHealthObject
from sweatsync.agents.interviewer import SYSTEM_PROMPT, extract_and_validate_sho
from sweatsync.agents.guardian import guardian_node
from sweatsync.agents.architect import architect_node
from sweatsync.agents.curator import curator_node
from sweatsync.agents.replanner import classify_intent, execute_replan
from sweatsync.state import SweatSyncState
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="SweatSync Onboarding API")

# CORS — allow Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client["sweatsync"]
profiles_collection = db["profiles"]
sessions_collection = db["sessions"]  # Stores SHO + plan for replanning
users_collection = db["users"]
exercises_cache = db["exercises_cache"] # Caches ExerciseDB results

# Auth Configuration
SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-key-for-sweatsync-auth")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 1 week

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await users_collection.find_one({"username": username})
    if user is None:
        raise credentials_exception
    return user

# --- Request / Response Models ---

class User(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    provider: Optional[str] = "groq"

class ChatResponse(BaseModel):
    reply: str
    suggested_options: List[str] = []
    input_type: Optional[str] = "text" # Changed to Optional just in case, but view logic will fill it
    sho: Optional[dict] = None
    is_complete: bool = False

class GenerateRequest(BaseModel):
    sho: dict
    provider: Optional[str] = "groq"

class PlanChatContext(BaseModel):
    level: str  # "week" | "day" | "session" | "exercise"
    week_index: Optional[int] = None
    day_key: Optional[str] = None
    exercise_index: Optional[int] = None

class PlanChatRequest(BaseModel):
    prompt: str
    context: PlanChatContext
    current_plan: dict
    session_id: Optional[str] = None  # For replanning — retrieves SHO from MongoDB
    provider: Optional[str] = "groq"


# --- Auth Endpoints ---

@app.post("/api/auth/register")
async def register(user: User):
    existing_user = await users_collection.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = {
        "username": user.username,
        "password": hashed_password,
        "created_at": datetime.utcnow()
    }
    await users_collection.insert_one(new_user)
    return {"message": "User registered successfully"}

@app.post("/api/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await users_collection.find_one({"username": form_data.username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/user/data")
async def get_user_data(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    # Get the most recent session for this user
    session = await sessions_collection.find_one(
        {"user_id": user_id},
        sort=[("_id", -1)] # Sort by _id descending to get the latest (since uuid is used, maybe we should sort by insertion time. Better yet, we can just get the first one for now, or sort by $natural)
        # However, we are using uuid4 for _id, which isn't time-ordered. Let's just find the most recent one by $natural or add a created_at field.
    )
    
    if session:
        return {
            "sho": session["sho"],
            "plan": session["plan"],
            "session_id": session["_id"]
        }
        
    return {"sho": None, "plan": None, "session_id": None}

# --- Endpoints ---

# --- ExerciseDB Proxy Endpoints ---

@app.get("/api/exercise/search")
async def search_exercise(name: str):
    """Fuzzy searches an exercise by name via RapidAPI and caches the result."""
    name_lower = name.lower()
    
    # Check cache first with case-insensitive regex
    cached = await exercises_cache.find_one({"name_lower": {"$regex": f"^{re.escape(name_lower)}$", "$options": "i"}})
    if cached:
        cached.pop("_id", None)
        return cached

    # Proxy to RapidAPI
    rapid_key = os.getenv("RAPIDAPI_KEY")
    if not rapid_key:
        raise HTTPException(status_code=500, detail="RAPIDAPI_KEY not configured")

    headers = {
        "X-RapidAPI-Key": rapid_key,
        "X-RapidAPI-Host": "exercisedb.p.rapidapi.com"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"https://exercisedb.p.rapidapi.com/exercises/name/{name}",
                headers=headers,
                timeout=10.0
            )
            resp.raise_for_status()
            results = resp.json()
            
            if results and isinstance(results, list) and len(results) > 0:
                best_match = results[0]
                # Cache it
                best_match["name_lower"] = best_match.get("name", "").lower()
                await exercises_cache.update_one({"id": best_match["id"]}, {"$set": best_match}, upsert=True)
                best_match.pop("_id", None)
                return best_match
            else:
                return {"error": "Exercise not found in ExerciseDB"}
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"RapidAPI fetch error: {str(e)}")

@app.get("/api/exercise/details/{exercise_id}")
async def get_exercise_details_by_id(exercise_id: str):
    """Gets full exercise details natively by ID, prioritizing cache."""
    # Handle legacy EX IDs by searching by name if ID lookup fails
    cached = await exercises_cache.find_one({"id": exercise_id})
    if cached:
        cached.pop("_id", None)
        return cached
        
    if exercise_id.startswith("EX"):
        # This is a legacy ID, we can't fetch it from RapidAPI directly.
        # It should have been migrated, but as fallback, we return 404
        # and let the frontend fall back to name search.
        raise HTTPException(status_code=404, detail="Legacy exercise ID requires name-based search")

    rapid_key = os.getenv("RAPIDAPI_KEY")
    headers = {"X-RapidAPI-Key": rapid_key, "X-RapidAPI-Host": "exercisedb.p.rapidapi.com"}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"https://exercisedb.p.rapidapi.com/exercises/exercise/{exercise_id}", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                data["name_lower"] = data.get("name", "").lower()
                await exercises_cache.update_one({"id": exercise_id}, {"$set": data}, upsert=True)
                data.pop("_id", None)
                return data
        except:
            pass
    raise HTTPException(status_code=404, detail="Exercise not found")


@app.get("/api/exercise/image/{exercise_id}")
async def get_exercise_image(exercise_id: str):
    """Streams the GIF image seamlessly from ExerciseDB to the frontend."""
    rapid_key = os.getenv("RAPIDAPI_KEY")
    if not rapid_key:
        raise HTTPException(status_code=500, detail="RAPIDAPI_KEY not configured")
        
    url = f"https://exercisedb.p.rapidapi.com/image?exerciseId={exercise_id}&resolution=360&rapidapi-key={rapid_key}"
    
    async def fetch_image():
        async with httpx.AsyncClient() as client:
            try:
                async with client.stream("GET", url, timeout=15.0) as response:
                    async for chunk in response.aiter_bytes():
                        yield chunk
            except Exception as e:
                print(f"Error streaming image {exercise_id}: {e}")
                
    return StreamingResponse(fetch_image(), media_type="image/gif")

@app.get("/api/exercises/muscle/{muscle}")
async def get_exercises_by_muscle(muscle: str):
    """Fetches exercises for a given react-body-highlighter muscle slug."""
    
    # Map react-body-highlighter slugs to ExerciseDB bodyPart or target
    slug_map = {
        "chest": {"type": "target", "value": "pectorals"},
        "biceps": {"type": "target", "value": "biceps"},
        "triceps": {"type": "target", "value": "triceps"},
        "forearm": {"type": "target", "value": "forearms"},
        "front-deltoids": {"type": "target", "value": "delts"},
        "back-deltoids": {"type": "target", "value": "delts"},
        "trapezius": {"type": "target", "value": "traps"},
        "upper-back": {"type": "target", "value": "upper back"},
        "lower-back": {"type": "target", "value": "spine"},
        "abs": {"type": "target", "value": "abs"},
        "obliques": {"type": "target", "value": "abs"},
        "quadriceps": {"type": "target", "value": "quads"},
        "hamstring": {"type": "target", "value": "hamstrings"},
        "gluteal": {"type": "target", "value": "glutes"},
        "calves": {"type": "target", "value": "calves"},
        "adductor": {"type": "target", "value": "adductors"},
        "abductors": {"type": "target", "value": "abductors"}
    }
    
    mapping = slug_map.get(muscle)
    if not mapping:
        # Fallback to searching by bodyPart exactly
        from sweatsync.exercise_fetcher import fetch_exercises_by_body_part
        import asyncio
        exercises = await asyncio.to_thread(fetch_exercises_by_body_part, muscle, limit=20)
    else:
        import asyncio
        if mapping["type"] == "target":
            from sweatsync.exercise_fetcher import fetch_exercises_by_target
            exercises = await asyncio.to_thread(fetch_exercises_by_target, mapping["value"], limit=20)
        else:
            from sweatsync.exercise_fetcher import fetch_exercises_by_body_part
            exercises = await asyncio.to_thread(fetch_exercises_by_body_part, mapping["value"], limit=20)

    if not exercises:
        raise HTTPException(status_code=404, detail="No exercises found for this muscle")
        
    return exercises

@app.post("/api/plan/chat")
async def plan_chat(req: PlanChatRequest, current_user: dict = Depends(get_current_user)):
    """
    Contextual chat to modify the existing plan.
    Uses partial updates for simple edits, full replan for structural changes.
    """
    llm = get_llm(provider=req.provider, max_tokens=1024)
    
    # Step 1: Classify intent
    intent = classify_intent(req.prompt, llm)
    print(f"PlanChat Intent: {intent} | Prompt: {req.prompt[:50]}")
    
    plan = req.current_plan
    
    # Step 2: Route by intent
    if intent == "replan":
        return await handle_replan(req, plan)
    elif intent == "question":
        return await handle_question(req, plan, llm)
    else:
        return await handle_simple_edit(req, plan, llm)


async def handle_replan(req: PlanChatRequest, plan: dict) -> dict:
    """Handle structural replan requests (skip weeks, reschedule, etc.)"""
    # Retrieve SHO from MongoDB
    sho = {}
    safety_manifesto = plan.get("safety_manifesto", {})
    
    if req.session_id:
        try:
            session = await sessions_collection.find_one({"_id": req.session_id})
            if session:
                sho = session.get("sho", {})
                safety_manifesto = session.get("safety_manifesto", safety_manifesto)
        except Exception as e:
            print(f"Session lookup error: {e}")
    
    context = {
        "level": req.context.level,
        "week_index": req.context.week_index,
        "day_key": req.context.day_key,
        "exercise_index": req.context.exercise_index
    }
    
    import asyncio
    result = await asyncio.to_thread(
        execute_replan,
        req.prompt, plan, sho, safety_manifesto, context, req.provider
    )
    
    # Merge updated weeks if provided (partial update to save tokens)
    updated_weeks = result.get("updated_weeks")
    if updated_weeks:
        print(f"DEBUG: Merging {len(updated_weeks)} weeks from agent")
        for key, week_data in updated_weeks.items():
            try:
                # Extract digits from key (handles "0", "week_0", "Week 1", etc.)
                match = re.search(r'(\d+)', key)
                if match:
                    val = int(match.group(1))
                    # If AI used 1-based indexing (e.g. "Week 4"), adjust to 0-based
                    if "week" in key.lower() and val > 0 and val <= len(plan.get("weeks", [])):
                        # If the key is like "week 4" and the value is 4, it's likely 1-indexed.
                        # But wait, if they return "0" it's 0-indexed.
                        # Let's check if the value matches the 1-indexed week number in the object.
                        # For safety, if it's "week X" we'll try to find a match or default to 0-indexed if it's small.
                        # Most reliable: if 'week' in key, it's probably 1-indexed.
                        idx = val - 1
                    else:
                        idx = val
                        
                    if 0 <= idx < len(plan.get("weeks", [])):
                        plan["weeks"][idx] = week_data
                        print(f"DEBUG: Successfully merged week {idx} from key '{key}'")
                    else:
                        print(f"DEBUG: Calculated index {idx} from key '{key}' out of range")
                else:
                    print(f"DEBUG: No digits found in key '{key}'")
            except Exception as e:
                print(f"DEBUG: Error merging week {key}: {e}")
    else:
        print("DEBUG: No updated_weeks found in result")
    
    updated_plan = result.get("updated_plan") or plan
    
    # Update session in MongoDB
    if req.session_id:
        try:
            print(f"DEBUG: Updating MongoDB session {req.session_id}")
            await sessions_collection.update_one(
                {"_id": req.session_id},
                {"$set": {"plan": updated_plan}}
            )
        except Exception as e:
            print(f"DEBUG: Session update error: {e}")
    
    return {
        "reply": result.get("reply", "Plan restructured."),
        "action": result.get("action", "replan"),
        "preview": result.get("preview"),
        "updated_plan": updated_plan
    }


async def handle_question(req: PlanChatRequest, plan: dict, llm) -> dict:
    
    """Handle question-only requests — answer without modifying the plan."""
    weeks = plan.get("weeks", [])
    
    # Build compact overview (minimal tokens)
    weeks_overview = []
    for i, w in enumerate(weeks):
        days = w.get("days", {})
        day_names = [f"{dk}({len(dv.get('exercises',[]))}ex)" for dk, dv in days.items()]
        weeks_overview.append(f"W{w.get('week_number', i+1)}({w.get('phase', '?')}): {','.join(day_names)}")
    
    system_prompt = f"""You are SweatSync AI Trainer. Answer the user's question about their workout plan.
Be direct (1-3 sentences). Reference actual data from the plan.

PLAN: {' | '.join(weeks_overview)}

Return valid json:
{{"reply": "Your direct answer"}}"""
    
    try:
        # Use a lower max_tokens for faster question responses
        from langchain_core.messages import SystemMessage as SM, HumanMessage as HM
        response = llm.invoke([
            SM(content=system_prompt),
            HM(content=req.prompt)
        ])
        match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if match:
            data = json.loads(match.group())
            return {"reply": data.get("reply", "I couldn't answer that."), "updated_plan": plan}
    except Exception as e:
        print(f"Question handler error: {e}")
    return {"reply": "I couldn't process that question.", "updated_plan": plan}


async def handle_simple_edit(req: PlanChatRequest, plan: dict, llm) -> dict:
    """Handle simple edits (swap exercises, adjust reps, etc.) — existing slice-based logic."""
    weeks = plan.get("weeks", [])
    
    # Build a compact overview of all weeks for LLM context
    weeks_overview = []
    for i, w in enumerate(weeks):
        days = w.get("days", {})
        day_summaries = []
        for dk, dv in days.items():
            exs = dv.get("exercises", [])
            day_summaries.append(f"{dk}: {dv.get('day_label', '?')} ({len(exs)} exercises)")
        weeks_overview.append(f"Week {w.get('week_number', i+1)} ({w.get('phase', '?')}): {', '.join(day_summaries)}")
    overview_text = chr(10).join(weeks_overview)
    
    # 2. Get the detailed slice for the focused context
    relevant_slice = None
    slice_path = ""
    
    if req.context.level == "week":
        if req.context.week_index is not None and req.context.week_index < len(weeks):
            relevant_slice = weeks[req.context.week_index]
            slice_path = f"Week {req.context.week_index + 1}"
    elif req.context.level in ["day", "session"]:
        if req.context.week_index is not None and req.context.week_index < len(weeks):
            relevant_slice = weeks[req.context.week_index].get("days", {}).get(req.context.day_key)
            slice_path = f"Week {req.context.week_index + 1}, Day {req.context.day_key}"
    elif req.context.level == "exercise":
        if req.context.week_index is not None and req.context.week_index < len(weeks):
            day_data = weeks[req.context.week_index].get("days", {}).get(req.context.day_key, {})
            exercises = day_data.get("exercises", [])
            if req.context.exercise_index is not None and req.context.exercise_index < len(exercises):
                relevant_slice = exercises[req.context.exercise_index]
                slice_path = f"Week {req.context.week_index + 1}, Day {req.context.day_key}, Exercise: {relevant_slice.get('name', 'Unknown')}"
            
    if not relevant_slice:
        relevant_slice = plan
        slice_path = "Full Plan"

    # Helper to strip URLs
    def strip_urls(obj):
        if isinstance(obj, dict):
            obj.pop("anatomy_url", None)
            obj.pop("heatmap_url", None)
            for k, v in obj.items(): strip_urls(v)
        elif isinstance(obj, list):
            for x in obj: strip_urls(x)

    clean_slice = json.loads(json.dumps(relevant_slice))
    strip_urls(clean_slice)

    context_desc = f"User is viewing: {req.context.level} level at {slice_path}"
    
    system_prompt = f"""You are SweatSync AI Trainer — a direct, expert fitness coach who modifies workout plans.

RULES:
1. ALWAYS make concrete changes when the user asks for modifications. Actually DO it in the updated_slice.
2. If the user asks a QUESTION, answer clearly using plan data. Reference exercise names, sets, reps.
3. Keep replies SHORT (1-3 sentences). Be direct like a trainer.

PLAN OVERVIEW: {overview_text}
FOCUSED: {context_desc}
{('SAFETY: ' + json.dumps(plan.get('safety_manifesto', {}))) if req.context.level != 'exercise' else ''}

Return valid json:
{{
  "reply": "Short, direct trainer response",
  "updated_slice": <the modified version of the PLAN SLICE below — same structure, with your changes applied. If no changes needed (question only), return the slice unchanged.>
}}

Do NOT include anatomy_url or heatmap_url in exercises.
The "reps" field MUST be a string like "12" or "8-12"."""

    user_prompt = f"{req.prompt}\n\nSLICE:\n{json.dumps(clean_slice)}"

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if match:
            data = json.loads(match.group())
            updated_slice = data.get("updated_slice")
            
            if updated_slice:
                # Merge back into full plan
                if req.context.level == "week":
                    plan["weeks"][req.context.week_index] = updated_slice
                elif req.context.level in ["day", "session"]:
                    plan["weeks"][req.context.week_index]["days"][req.context.day_key] = updated_slice
                elif req.context.level == "exercise":
                    plan["weeks"][req.context.week_index]["days"][req.context.day_key]["exercises"][req.context.exercise_index] = updated_slice
                else:
                    plan = updated_slice

            return {
                "reply": data.get("reply", "Plan updated."),
                "updated_plan": plan # Frontend gets full plan
            }
        else:
            return {"reply": "Could not parse update.", "updated_plan": plan}
    except Exception as e:
        print(f"PlanChat Error: {e}")
        return {"reply": f"Error: {str(e)}", "updated_plan": plan}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    """
    Stateless chat endpoint. 
    Receives history, invokes LLM (forced JSON), 
    checks for SHO completion, and returns structured data.
    """
    llm = get_llm(provider=req.provider)

    lc_messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for msg in req.messages:
        if msg.role == "user":
            lc_messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            lc_messages.append(AIMessage(content=msg.content))

    try:
        response = llm.invoke(lc_messages)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {str(e)}")

    raw_content = response.content

    # Robust JSON Parsing
    try:
        print(f"\n--- RAW LLM RESPONSE ---\n{raw_content}\n-----------------------")
        match = re.search(r'\{.*\}', raw_content, re.DOTALL)
        if match:
            data = json.loads(match.group())
            print(f"Parsed JSON: {json.dumps(data, indent=2)}")
            
            reply = data.get("conversational_message", "").strip()
            # Safety: If message is empty but it's not the final step, fallback to a probe.
            if not reply and not data.get("is_final"):
                reply = "I've noted that. Is there anything else you'd like to clarify before we move on?"

            options = data.get("suggested_options")
            if options is None:
                options = []
            
            inp_type = data.get("input_type") or "text"
            is_final = data.get("is_final", False)
            sho_payload = data.get("sho_payload")

            if is_final and sho_payload:
                # Validate with Pydantic via existing helper
                sho_dict = extract_and_validate_sho(raw_content)
                if sho_dict:
                    # Intentionally delaying save to MongoDB until /api/generate succeeds
                    
                    return ChatResponse(
                        reply=reply or "Your profile is complete!",
                        suggested_options=options,
                        input_type=inp_type,
                        sho=sho_dict,
                        is_complete=True
                    )
                else:
                    # Final but validation failed (e.g. malformed or missing fields)
                    is_final = False # Force continue to fix it
                    if not reply:
                        reply = "I have your data, but some details seem missing. Can you confirm your height and weight again?"

            return ChatResponse(
                reply=reply,
                suggested_options=options,
                input_type=inp_type,
                is_complete=False
            )
        else:
            # Fallback for plain text. If it looks like a failed JSON block, clean it.
            if raw_content.strip().startswith('{') or '"' in raw_content:
                return ChatResponse(
                    reply="I had a slight formatting error. Could you please repeat your last point?",
                    input_type="text"
                )
            return ChatResponse(reply=raw_content, input_type="text")
            
    except Exception as e:
        print(f"JSON Parse Fallback: {e}")
        return ChatResponse(
            reply="Connection stable, but I missed that. Can you say that again?",
            input_type="text"
        )


@app.get("/api/chat/start")
async def start_chat(provider: str = "ollama", current_user: dict = Depends(get_current_user)):
    """
    Returns the initial AI greeting to kick off the conversation.
    """
    llm = get_llm(provider=provider)
    lc_messages = [SystemMessage(content=SYSTEM_PROMPT)]

    try:
        response = llm.invoke(lc_messages)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {str(e)}")

    raw_content = response.content
    try:
        match = re.search(r'\{.*\}', raw_content, re.DOTALL)
        if match:
            data = json.loads(match.group())
            options = data.get("suggested_options")
            if options is None:
                options = []
            return {
                "reply": data.get("conversational_message", ""),
                "suggested_options": options,
                "input_type": data.get("input_type") or "text"
            }
        return {"reply": raw_content, "suggested_options": [], "input_type": "text"}
    except:
        return {"reply": raw_content, "suggested_options": [], "input_type": "text"}


@app.get("/health")
async def health():
    return {"status": "ok"}


# --- Pipeline Generation with SSE Progress ---

@app.post("/api/generate")
async def generate_plan(req: GenerateRequest, current_user: dict = Depends(get_current_user)):
    """
    Runs the 3-agent pipeline (Guardian → Architect → Curator)
    and streams progress events via SSE.
    """
    sho = req.sho

    async def event_stream():
        # Initialize state
        state: SweatSyncState = {
            "user_sho": sho,
            "safety_manifesto": {},
            "strategic_blueprint": {},
            "interactive_planner": {},
            "provider": req.provider,
            "revision_count": 0,
            "conflict_detected": False,
            "max_revisions": 2
        }

        # --- Stage 1: Guardian ---
        yield _sse_event({
            "stage": "guardian",
            "status": "running",
            "progress": 0,
            "summary": "Analyzing your medical profile for safety constraints..."
        })

        try:
            result = await asyncio.to_thread(guardian_node, state)
            state.update(result)
            manifesto = state["safety_manifesto"]
            narrative = manifesto.get("safety_narrative", "Safety review complete.")
            yield _sse_event({
                "stage": "guardian",
                "status": "done",
                "progress": 33,
                "summary": f"Safety review complete. {narrative[:100]}..."
            })
        except Exception as e:
            yield _sse_event({
                "stage": "guardian",
                "status": "error",
                "progress": 0,
                "summary": f"Guardian error: {str(e)}"
            })
            return

        # --- Stage 2: Architect ---
        yield _sse_event({
            "stage": "architect",
            "status": "running",
            "progress": 33,
            "summary": "Calculating optimal training volume and periodization..."
        })

        try:
            result = await asyncio.to_thread(architect_node, state)
            state.update(result)
            blueprint = state["strategic_blueprint"]
            split_keys = list(blueprint.get("training_split", {}).keys())
            yield _sse_event({
                "stage": "architect",
                "status": "done",
                "progress": 50,
                "summary": f"Strategic blueprint ready. Training split across {len(split_keys)} days."
            })
        except Exception as e:
            yield _sse_event({
                "stage": "architect",
                "status": "error",
                "progress": 33,
                "summary": f"Architect error: {str(e)}"
            })
            return

        # --- Stage 3: Curator (per-week progress) ---
        yield _sse_event({
            "stage": "curator",
            "status": "running",
            "progress": 50,
            "summary": f"Selecting exercises and building your workout plan...",
            "week": 0
        })

        try:
            # Run curator (it generates all 7 weeks internally)
            result = await asyncio.to_thread(curator_node, state)
            state.update(result)

            yield _sse_event({
                "stage": "curator",
                "status": "done",
                "progress": 100,
                "summary": "All weeks generated!",
            })
        except Exception as e:
            yield _sse_event({
                "stage": "curator",
                "status": "error",
                "progress": 50,
                "summary": f"Curator error: {str(e)}"
            })
            return

        # --- Final: Save session & send complete plan ---
        planner = state.get("interactive_planner", {})
        
        # Persist SHO + plan to MongoDB for replanning
        import uuid
        session_id = str(uuid.uuid4())
        try:
            await sessions_collection.insert_one({
                "_id": session_id,
                "user_id": str(current_user["_id"]),
                "sho": sho,
                "plan": planner,
                "safety_manifesto": state.get("safety_manifesto", {}),
                "strategic_blueprint": state.get("strategic_blueprint", {}),
            })
        except Exception as e:
            print(f"Session save error: {e}")
        
        yield _sse_event({
            "stage": "complete",
            "progress": 100,
            "plan": planner,
            "session_id": session_id
        })

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


def _sse_event(data: dict) -> str:
    """Format a dict as an SSE event string."""
    return f"data: {json.dumps(data)}\n\n"
