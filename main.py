from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import requests
import os
import json
from json_repair import repair_json
from datetime import datetime
import time
from urllib.parse import urlparse, urlunparse
from typing import Any, Dict, List, Optional
from starlette.responses import StreamingResponse
from doc_loader import ALL_DOCS, ALL_HMI_DOCS
from hmi_schema_doc import HMI_SCHEMA_DOC

DOCS_MAX_CHARS = 1000  # tweak as needed
# Where llama.cpp's HTTP server is listening
LLM_API_URL = os.getenv("LLM_API_URL", "http://127.0.0.1:8080/v1/chat/completions")
LLM_MODEL_NAME = os.getenv(
    "LLM_MODEL_NAME",
    "mlx-community/Meta-Llama-3-8B-Instruct-4bit"
)
# LLM request timeouts (in seconds)
LLM_CONNECT_TIMEOUT = float(os.getenv("LLM_CONNECT_TIMEOUT", "5"))
LLM_READ_TIMEOUT = float(os.getenv("LLM_READ_TIMEOUT", "60"))
LLM_CHAT_READ_TIMEOUT = float(os.getenv("LLM_CHAT_READ_TIMEOUT", str(LLM_READ_TIMEOUT)))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1024"))
LLM_CHAT_MAX_TOKENS = int(os.getenv("LLM_CHAT_MAX_TOKENS", "256"))
CHAT_HISTORY_MAX_MESSAGES = int(os.getenv("CHAT_HISTORY_MAX_MESSAGES", "30"))
CHAT_DOCS_MAX_CHARS = 300
CONVERSATIONS: Dict[str, List[Dict[str, str]]] = {}

app = FastAPI(title="Durus AI Agent Server")

class ControllerConfig(BaseModel):
    database: Dict[str, Any]
    modules: List[Dict[str, Any]]
    hmi: Dict[str, Any]
    charts: List[Dict[str, Any]]

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
    #configuration: Optional[ControllerConfig] = None
    proposed_changes: Dict[str, Any]
    
# --- Chat models ---
class ChatRequest(BaseModel):
    prompt: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str


# ---------- Prompt building ----------
def build_system_prompt() -> str:
    now = datetime.now().strftime("%m-%d-%Y %H:%M:%S")

    base = (
        "You are an assistant for an HMI/tag editor on the Duro controller.\n"
        f"Current local date/time: {now}.\n"
        "\n"
        "You receive:\n"
        "- A natural-language user request.\n"
        "- A 'device_context' object that includes 'controller_config', the CURRENT controller configuration.\n"
        "\n"
        "You MUST respond with a single JSON OBJECT (not an array) and nothing else.\n"
        "The top-level JSON must have exactly these fields:\n"
        "{\n"
        '  \"message\": string,\n'
        '  \"steps\": [ { \"title\": string, \"details\": string }, ... ],\n'
        '  \"proposed_changes\": {\n'
        '    \"hmi\": { \"views\": [ ... view objects to add or replace ... ] },\n'
        '    \"tags_to_add\": [ ... tag objects to create ... ]\n'
        "  }\n"
        "}\n"
        "\n"
        "Rules:\n"
        "- Treat device_context.controller_config as the current state.\n"
        "- In proposed_changes, only include the minimal patch needed (views/tags to add or replace).\n"
        "- Do NOT include the full controller_config in proposed_changes.\n"
        "- Do NOT wrap the top-level JSON object in an array.\n"
        "- Do NOT include any text before or after the JSON.\n"
        "- Do NOT use backticks.\n"
        "- If unsure, return safe empty objects/arrays and explain in 'message'.\n"
        "\n"
        "Below is a truncated description of the controller configuration schema. Use it as a guide,\n"
        "but if the live controller_config contradicts this schema, the live data wins.\n"
    )

    # Truncate the schema doc so /agent/ask stays fast even on CPU
    schema_text = HMI_SCHEMA_DOC[:1800]

    return base + "\n\n=== CONTROLLER CONFIG SCHEMA (TRUNCATED) ===\n\n" + schema_text

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
    from datetime import datetime
    now = datetime.now().strftime("%m-%d-%Y %H:%M:%S")
    base = (
        f"You are a helpful general assistant and an HMI/tag editor assistant for the Duro controller.\n"
        f"Current date and time: {now}\n"
        "You know how its HMI views, HMI components, and database tags works.\n"
        "Use the documentation below when answering questions about the controller.\n"
        "Answer in plain text unless I explicitly ask for JSON.\n"
    )
    # Join docs and truncate to a manageable size
    full_docs = "\n\n---\n\n".join(ALL_DOCS)
    docs_text = full_docs[:CHAT_DOCS_MAX_CHARS]

    return base + "\n\n=== DURO CONTROLLER DOCS (TRUNCATED) ===\n\n" + docs_text

def build_view_creation_prompt() -> str:
    now = datetime.now().strftime("%m-%d-%Y %H:%M:%S")

    base = (
        "You are an assistant for an HMI/tag editor on the Duro controller.\n"
        f"Current local date/time: {now}.\n"
        "\n"
        "You receive:\n"
        "- A natural-language user request.\n"
        "- A 'device_context' object that includes 'controller_config', the CURRENT controller configuration.\n"
        "\n"
        "You MUST respond with a single JSON OBJECT (not an array) and nothing else.\n"
        "The top-level JSON must have exactly these fields:\n"
        "{\n"
        '  \"message\": string,\n'
        '  \"steps\": [ { \"title\": string, \"details\": string }, ... ],\n'
        '  \"proposed_changes\": {\n'
        '    \"hmi\": { \"views\": [ ... view objects to add or replace ... ] },\n'
        "  }\n"
        "}\n"
        "\n"
        "Rules:\n"
        "- Treat device_context.controller_config as the current state.\n"
        "- In proposed_changes, only include the minimal patch needed (views/tags to add or replace).\n"
        "- Do NOT include the full controller_config in proposed_changes.\n"
        "- Do NOT wrap the top-level JSON object in an array.\n"
        "- Do NOT include any text before or after the JSON.\n"
        "- Do NOT use backticks.\n"
        "- If unsure, return safe empty objects/arrays and explain in 'message'.\n"
        "\n"
        "Below is a truncated description of the controller configuration schema. Use it as a guide,\n"
        "but if the live controller_config contradicts this schema, the live data wins.\n"
    )

    # Truncate the schema and HMI docs so /agent/ask stays fast even on CPU
    hmi_full = "\n\n---\n\n".join(ALL_HMI_DOCS)
    hmi_text = hmi_full[:DOCS_MAX_CHARS]

    return (
        base
        + "\n\n=== HMI DOCS (TRUNCATED) ===\n\n" + hmi_text
    )

# ---------- Llama.cpp call ----------
def call_llm(messages: List[Dict[str, str]]) -> str:
    payload = {
        "model": LLM_MODEL_NAME,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": LLM_MAX_TOKENS,
    }

    try:
        print("\n[AGENT DEBUG] Calling LLM:", LLM_API_URL)
        # Avoid logging full payload content to keep logs tidy
        print("[AGENT DEBUG] Model:", payload.get("model"), "Messages:", len(payload.get("messages", [])))
        resp = requests.post(
            LLM_API_URL,
            json=payload,
            timeout=(LLM_CONNECT_TIMEOUT, LLM_READ_TIMEOUT),
        )
        resp.raise_for_status()                             
    except requests.RequestException as e:
        print("\n[AGENT DEBUG] LLM call failed:", e, "\n")
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

def call_llm_for_chat(messages: List[Dict[str, str]]) -> str:
    print("\n[AGENT DEBUG] Calling LLM (chat):", LLM_API_URL)
    payload = {
        "model": LLM_MODEL_NAME,
        "messages": messages,
        "temperature": 0.5,   # chatty, but not insane
        "max_tokens": LLM_CHAT_MAX_TOKENS,
    }

    try:
        print("[AGENT DEBUG] Model:", payload.get("model"), "Messages:", len(payload.get("messages", [])))
        resp = requests.post(
            LLM_API_URL,
            json=payload,
            timeout=(LLM_CONNECT_TIMEOUT, LLM_CHAT_READ_TIMEOUT),
        )
    except requests.Timeout as e:
        raise HTTPException(status_code=504, detail=f"LLM read timeout: {e}")
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

def _iter_llm_chat_stream(messages: List[Dict[str, str]]):
    payload = {
        "model": LLM_MODEL_NAME,
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": LLM_CHAT_MAX_TOKENS,
        "stream": True,
    }
    try:
        resp = requests.post(
            LLM_API_URL,
            json=payload,
            stream=True,
            timeout=(LLM_CONNECT_TIMEOUT, LLM_CHAT_READ_TIMEOUT),
        )
    except requests.Timeout as e:
        yield "[timeout]"
        return
    except requests.RequestException as e:
        yield f"[error] {e}"
        return

    ct = (resp.headers.get("Content-Type") or "").lower()
    if "text/event-stream" in ct:
        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            if line.startswith("data: "):
                data = line[6:].strip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                    for ch in obj.get("choices", []):
                        delta = ch.get("delta") or ch.get("message") or {}
                        content = delta.get("content")
                        if content:
                            yield content
                except Exception:
                    yield data
    else:
        try:
            j = resp.json()
            yield j["choices"][0]["message"]["content"]
        except Exception:
            yield resp.text


def _llm_models_url() -> str:
    """Return the /v1/models URL derived from LLM_API_URL host/port."""
    u = urlparse(LLM_API_URL)
    return urlunparse((u.scheme, u.netloc, "/v1/models", "", "", ""))

# get LLM Config
@app.get("/debug/llm-config")
def debug_llm_config():
    return {
        "LLM_API_URL": LLM_API_URL,
        "LLM_MODEL_NAME": LLM_MODEL_NAME,
        "LLM_CONNECT_TIMEOUT": LLM_CONNECT_TIMEOUT,
        "LLM_READ_TIMEOUT": LLM_READ_TIMEOUT,
        "LLM_MODELS_URL": _llm_models_url(),
    }

# check LLM health
@app.get("/health/llm")
def health_llm():
    """Probes the LLM server to verify reachability and basic functionality."""
    # 1) Try /v1/models if available
    models_url = _llm_models_url()
    try:
        t0 = time.time()
        r = requests.get(models_url, timeout=(LLM_CONNECT_TIMEOUT, 5))
        elapsed = time.time() - t0
        info = {
            "ok": r.status_code == 200,
            "probe": "GET /v1/models",
            "status": r.status_code,
            "elapsed_sec": round(elapsed, 3),
            "url": models_url,
        }
        if r.status_code == 200:
            return info
    except Exception as e:
        models_error = str(e)
    else:
        models_error = None

    # 2) Fallback: tiny chat completion
    payload = {
        "model": LLM_MODEL_NAME,
        "messages": [
            {"role": "system", "content": "ping"},
            {"role": "user", "content": "ping"},
        ],
        "temperature": 0.0,
        "max_tokens": 1,
    }
    try:
        t0 = time.time()
        r = requests.post(
            LLM_API_URL,
            json=payload,
            timeout=(LLM_CONNECT_TIMEOUT, 10),
        )
        elapsed = time.time() - t0
        ok = r.status_code == 200
        return {
            "ok": ok,
            "probe": "POST /v1/chat/completions",
            "status": r.status_code,
            "elapsed_sec": round(elapsed, 3),
            "url": LLM_API_URL,
            "models_probe_error": models_error,
        }
    except Exception as e:
        return {
            "ok": False,
            "probe": "POST /v1/chat/completions",
            "status": None,
            "elapsed_sec": None,
            "url": LLM_API_URL,
            "error": str(e),
            "models_probe_error": models_error,
        }
    

def sanitize_llm_json(text: str) -> str:
    """
    Strip control tokens and extract the largest {...} block.
    """
    for tok in ("<|eot_id|>", "<|eom_id|>"):
        text = text.replace(tok, "")
    text = text.strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object delimiters found in LLM output")

    json_str = text[start:end + 1]
    return json_str

# ---------- API endpoint ----------

@app.post("/agent/ask", response_model=AgentResponse)
def ask_agent(body: AgentRequest):
    print("\n[AGENT DEBUG] Received request")
    # You can do auth / IP checks / device_id checks here if you want.
    context = body.context or {}
    conv_id = body.conversation_id or body.device_id  # fallback if no ID

    # Create history list if not there yet
    history = CONVERSATIONS.setdefault(conv_id, [])

    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(body.prompt, context)

    # Build message list: system + history + new user
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        #*history,
        #{"role": "user", "content": user_prompt},
    ]
    # If you really want a bit of context, only keep the last 4 turns (8 messages)
    if len(history) > 8:
        short_history = history[-8:]
    else:
        short_history = history

    messages.extend(short_history)
    messages.append({"role": "user", "content": user_prompt})

    # Call the model
    raw = call_llm(messages)
    print("\n[AGENT DEBUG] Raw LLM output:\n", repr(raw), "\n")
    try:
        json_str = sanitize_llm_json(raw)
    except ValueError as e:
        print("\n[AGENT DEBUG] RAW REPR (no JSON found):\n", repr(raw), "\n")
        raise HTTPException(status_code=500, detail=f"LLM output missing JSON object: {e}")
    
    try:
        parsed = json.loads(json_str)
    except json.JSONDecodeError as e:
        # 3) If that fails, try to repair it with json_repair
        try:
            repaired_str = repair_json(json_str)
            parsed = json.loads(repaired_str)
        except Exception as e2:
            raise HTTPException(
                status_code=500,
                detail=f"LLM did not return valid JSON even after repair: {e2}",
            )

    # 3) If model ever wraps in a list, unwrap element 0
    if isinstance(parsed, list):
        if parsed and isinstance(parsed[0], dict):
            parsed = parsed[0]
        else:
            raise HTTPException(
                status_code=500,
                detail="LLM returned a list but no dict inside.",
            )

    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=500,
            detail="LLM JSON top-level is not an object.",
        )

    # 4) Ensure required keys exist, with safe defaults
    if "message" not in parsed:
        parsed["message"] = "No explanation provided by model."

    if "steps" not in parsed or not isinstance(parsed["steps"], list):
        parsed["steps"] = []

    if "proposed_changes" not in parsed or not isinstance(parsed["proposed_changes"], dict):
        parsed["proposed_changes"] = {"hmi": {}}

    # 5) Build typed response
    try:
        resp_obj = AgentResponse(**parsed)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"LLM JSON missing required fields: {e}",
        )

    return resp_obj
    
@app.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest):
    # Use provided conversation_id or default
    conv_id = body.conversation_id or "default-chat"

    # Get or create history list for this conversation
    history = CONVERSATIONS.setdefault(conv_id, [])

    # Build messages: system + trimmed history + new user message
    system_prompt = build_chat_system_prompt()
    messages = [{"role": "system", "content": system_prompt}]
    if len(history) > CHAT_HISTORY_MAX_MESSAGES:
        short_history = history[-CHAT_HISTORY_MAX_MESSAGES:]
    else:
        short_history = history
    messages.extend(short_history)
    messages.append({"role": "user", "content": body.prompt})

    # Call the model
    reply = call_llm_for_chat(messages)

    for tok in ("<|eot_id|>", "<|eom_id|>"):
        reply = reply.replace(tok, "")
    reply = reply.strip()

    # Update history: we store only user and assistant turns (no system)
    history.append({"role": "user", "content": body.prompt})
    history.append({"role": "assistant", "content": reply})

    # Trim history if it gets too long (keep last 30 messages)
    if len(history) > 30:
        history[:] = history[-30:]

    return ChatResponse(reply=reply)


@app.post("/chat/stream")
def chat_stream(body: ChatRequest):
    conv_id = body.conversation_id or "default-chat"
    history = CONVERSATIONS.setdefault(conv_id, [])

    system_prompt = build_chat_system_prompt()
    messages = [{"role": "system", "content": system_prompt}]
    if len(history) > CHAT_HISTORY_MAX_MESSAGES:
        short_history = history[-CHAT_HISTORY_MAX_MESSAGES:]
    else:
        short_history = history
    messages.extend(short_history)
    messages.append({"role": "user", "content": body.prompt})

    buffer: List[str] = []

    def gen():
        try:
            for chunk in _iter_llm_chat_stream(messages):
                if chunk:
                    buffer.append(chunk)
                    yield chunk
        finally:
            reply = "".join(buffer).strip()
            history.append({"role": "user", "content": body.prompt})
            history.append({"role": "assistant", "content": reply})
            if len(history) > CHAT_HISTORY_MAX_MESSAGES:
                history[:] = history[-CHAT_HISTORY_MAX_MESSAGES:]

    return StreamingResponse(gen(), media_type="text/plain")


@app.post("/agent/build_view", response_model=AgentResponse)
def build_view(body: AgentRequest):
    print("\n[AGENT DEBUG] Received request")
    # You can do auth / IP checks / device_id checks here if you want.
    context = body.context or {}
    conv_id = body.conversation_id or body.device_id  # fallback if no ID

    # Create history list if not there yet
    history = CONVERSATIONS.setdefault(conv_id, [])

    system_prompt = build_view_creation_prompt()
    user_prompt = build_user_prompt(body.prompt, context)

    # Build message list: system + history + new user
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system_prompt},
    ]
    # If you really want a bit of context, only keep the last 4 turns (8 messages)
    if len(history) > 8:
        short_history = history[-8:]
    else:
        short_history = history

    messages.extend(short_history)
    messages.append({"role": "user", "content": user_prompt})

    # Call the model
    raw = call_llm(messages)
    print("\n[AGENT DEBUG] Raw LLM output:\n", repr(raw), "\n")
    try:
        json_str = sanitize_llm_json(raw)
    except ValueError as e:
        print("\n[AGENT DEBUG] RAW REPR (no JSON found):\n", repr(raw), "\n")
        raise HTTPException(status_code=500, detail=f"LLM output missing JSON object: {e}")
    
    try:
        parsed = json.loads(json_str)
    except json.JSONDecodeError as e:
        # 3) If that fails, try to repair it with json_repair
        try:
            repaired_str = repair_json(json_str)
            parsed = json.loads(repaired_str)
        except Exception as e2:
            raise HTTPException(
                status_code=500,
                detail=f"LLM did not return valid JSON even after repair: {e2}",
            )

    # 3) If model ever wraps in a list, unwrap element 0
    if isinstance(parsed, list):
        if parsed and isinstance(parsed[0], dict):
            parsed = parsed[0]
        else:
            raise HTTPException(
                status_code=500,
                detail="LLM returned a list but no dict inside.",
            )

    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=500,
            detail="LLM JSON top-level is not an object.",
        )

    # 4) Ensure required keys exist, with safe defaults
    if "message" not in parsed:
        parsed["message"] = "No explanation provided by model."

    if "steps" not in parsed or not isinstance(parsed["steps"], list):
        parsed["steps"] = []

    if "proposed_changes" not in parsed or not isinstance(parsed["proposed_changes"], dict):
        parsed["proposed_changes"] = {"hmi": {}}

    # 5) Build typed response
    try:
        resp_obj = AgentResponse(**parsed)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"LLM JSON missing required fields: {e}",
        )

    return resp_obj