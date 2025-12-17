from doc_loader import ALL_DOCS
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import requests
import os
import json
from json_repair import repair_json

# Where llama.cpp's HTTP server is listening
LLM_API_URL = os.getenv("LLM_API_URL", "http://127.0.0.1:8080/v1/chat/completions")
LLM_MODEL_NAME = os.getenv(
    "LLM_MODEL_NAME",
    "mlx-community/Meta-Llama-3-8B-Instruct-4bit"
)

app = FastAPI(title="Edge AI Agent Server")

CONVERSATIONS: Dict[str, List[Dict[str, str]]] = {}

# ---------- Data models ----------

class AgentStep(BaseModel):
    title: str
    details: str

class AgentRequest(BaseModel):
    device_id: str
    prompt: str
    context: Optional[Dict[str, Any]] = None  # current views/tags, etc.
    conversation_id: Optional[str] = None

class AgentResponse(BaseModel):
    message: str
    steps: List[AgentStep]
    proposed_changes: Optional[Dict[str, Any]] = None

# --- Chat models ---

class ChatRequest(BaseModel):
    prompt: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str


# ---------- Prompt building ----------

def build_system_prompt() -> str:
    base = """
You are an assistant for the Duro industrial controller.

You MUST answer in this JSON format:
{
  "message": string,
  "steps": [ { "title": string, "details": string }, ... ],
  "proposed_changes": {
    "screens": [],
    "tags": []
  }
}

Rules:
- No extra text, no backticks, only JSON.
- Use the controller docs below. If something is not covered, say you don't know.
"""
    docs_text = "\n\n=== CONTROLLER DOCS ===\n\n" + "\n\n---\n\n".join(ALL_DOCS)
    return base + docs_text
    


def build_user_prompt(prompt: str, context: Dict[str, Any]) -> str:
    """
    Wrap user prompt + context into one JSON blob for the model.
    """
    payload = {
        "user_request": prompt,
        "device_context": context,
    }
    return json.dumps(payload, indent=2)

def build_chat_system_prompt() -> str:
    base = (
        "You are a helpful assistant for the Duro industrial controller.\n"
        "You know how its HMI views, widgets, tags, alarms and logic work.\n"
        "Use the documentation below when answering questions about the controller.\n"
        "Answer in plain text unless I explicitly ask for JSON.\n"
    )
    return base + "\n\n=== CONTROLLER DOCS ===\n\n" + "\n\n---\n\n".join(ALL_DOCS)


# ---------- Llama.cpp call ----------

def call_llama(system_prompt: str, user_prompt: str) -> str:
    """
    Call llama.cpp's /v1/chat/completions endpoint and return the assistant's text.
    """
    payload = {
        "model": LLM_MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 2048,
        # Encourage strict JSON output if supported by llama.cpp OpenAI API
        "response_format": {"type": "json_object"},
    }

    try:
        resp = requests.post(LLM_API_URL, json=payload, timeout=240)
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error calling LLM: {e}")

    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail=f"LLM error: {resp.text[:200]}")

    data = resp.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise HTTPException(status_code=500, detail="Invalid LLM response format")

    return content

def call_llm(messages: List[Dict[str, str]]) -> str:
    payload = {
        "model": LLM_MODEL_NAME,
        "messages": messages,
        "temperature": 0.55,
        "max_tokens": 2048,
    }

    resp = requests.post(LLM_API_URL, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]

def call_llm_freeform(messages: List[Dict[str, str]]) -> str:
    payload = {
        "model": LLM_MODEL_NAME,
        "messages": messages,
        "temperature": 0.6,   # chatty, but not insane
        "max_tokens": 2048,
    }

    try:
        resp = requests.post(LLM_API_URL, json=payload, timeout=60)
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error calling LLM: {e}")

    if resp.status_code != 200:
        raise HTTPException(
            status_code=500,
            detail=f"LLM error: {resp.status_code} {resp.text[:200]}",
        )

    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise HTTPException(status_code=500, detail=f"Bad LLM response: {e}")
    
# ---------- API endpoint ----------

@app.post("/agent/ask", response_model=AgentResponse)
def ask_agent(body: AgentRequest):
    print(f"Received request for device {body.device_id} with prompt: {body.prompt}")
    # You can do auth / IP checks / device_id checks here if you want.
    context = body.context or {}
    conv_id = body.conversation_id or body.device_id  # fallback if no ID

    # Create history list if not there yet
    history = CONVERSATIONS.setdefault(conv_id, [])

    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(body.prompt, context)

    # Build message list: system + history + new user
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)  # list of {"role": "...", "content": "..."} from previous turns
    messages.append({"role": "user", "content": user_prompt})

    # Call the model
    raw = call_llm(messages)

    #raw = call_llama(system_prompt, user_prompt)

    # The model *should* return JSON. We enforce that.
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        # Attempt a best-effort repair for truncated or slightly invalid JSON
        try:
            repaired = repair_json(raw)
            parsed = json.loads(repaired)
            print("Repaired non-JSON response from LLM")
        except Exception:
            print("LLM raw response:", raw)
            # For debugging you might want to log `raw` somewhere.
            raise HTTPException(
                status_code=500,
                detail="LLM did not return valid JSON. Check system prompt or model behavior.",
            )

    # Let Pydantic validate that the JSON matches our schema.
    try:
        # Update history: append this user + assistant turn
        history.append({"role": "user", "content": user_prompt})
        history.append({"role": "assistant", "content": raw})

        # (Optional) Trim history if it gets too long
        if len(history) > 20:
            history[:] = history[-20:]
        return AgentResponse(**parsed)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"LLM JSON missing required fields: {e}",
        )
    
@app.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest):
    # Use provided conversation_id or default
    conv_id = body.conversation_id or "default-chat"

    # Get or create history list for this conversation
    history = CONVERSATIONS.setdefault(conv_id, [])

    # Build messages: system + history + new user message
    system_prompt = build_chat_system_prompt()
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system_prompt}
    ]
    messages.extend(history)
    messages.append({"role": "user", "content": body.prompt})

    # Call the model
    reply = call_llm_freeform(messages)

    # Update history: we store only user and assistant turns (no system)
    history.append({"role": "user", "content": body.prompt})
    history.append({"role": "assistant", "content": reply})

    # Trim history if it gets too long (e.g. keep last 40 messages)
    if len(history) > 40:
        history[:] = history[-40:]

    return ChatResponse(reply=reply)