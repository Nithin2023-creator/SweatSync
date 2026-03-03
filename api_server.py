"""
FastAPI bridge for the SweatSync Onboarding Interviewer Agent.
React frontend calls this directly. MongoDB stores completed SHO profiles.
"""
import json
import re
import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from sweatsync.llm import get_llm
from sweatsync.models.sho import StructuredHealthObject
from sweatsync.agents.interviewer import SYSTEM_PROMPT, extract_and_validate_sho
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="SweatSync Onboarding API")

# CORS — allow Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client["sweatsync"]
profiles_collection = db["profiles"]


# --- Request / Response Models ---

class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

class ChatResponse(BaseModel):
    reply: str
    suggested_options: List[str] = []
    input_type: str = "text"
    sho: Optional[dict] = None
    is_complete: bool = False


# --- Endpoints ---

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Stateless chat endpoint. 
    Receives history, invokes LLM (forced JSON), 
    checks for SHO completion, and returns structured data.
    """
    llm = get_llm()

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
            
            reply = data.get("conversational_message", "")
            options = data.get("suggested_options", [])
            inp_type = data.get("input_type", "text")
            is_final = data.get("is_final", False)
            sho_payload = data.get("sho_payload")

            if is_final and sho_payload:
                # Validate with Pydantic via existing helper
                sho_dict = extract_and_validate_sho(raw_content)
                if sho_dict:
                    try:
                        await profiles_collection.insert_one(sho_dict.copy())
                    except Exception as e:
                        print(f"MongoDB save error: {e}")
                    
                    return ChatResponse(
                        reply=reply,
                        suggested_options=options,
                        input_type=inp_type,
                        sho=sho_dict,
                        is_complete=True
                    )

            return ChatResponse(
                reply=reply,
                suggested_options=options,
                input_type=inp_type,
                is_complete=False
            )
        else:
            # Fallback for plain text (if LLM ignores instructions)
            return ChatResponse(reply=raw_content, input_type="text")
            
    except Exception as e:
        print(f"JSON Parse Fallback: {e}")
        return ChatResponse(reply=raw_content, input_type="text")


@app.get("/api/chat/start")
async def start_chat():
    """
    Returns the initial AI greeting to kick off the conversation.
    """
    llm = get_llm()
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
            return {
                "reply": data.get("conversational_message", ""),
                "suggested_options": data.get("suggested_options", []),
                "input_type": data.get("input_type", "text")
            }
        return {"reply": raw_content, "suggested_options": [], "input_type": "text"}
    except:
        return {"reply": raw_content, "suggested_options": [], "input_type": "text"}


@app.get("/health")
async def health():
    return {"status": "ok"}
