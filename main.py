from typing import List, Dict, Optional
import requests
import os
import json
import time
from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException
from json_repair import repair_json
from models.AgentModels import AgentRequest, AgentResponse
from utils.sanitize_llm_json import sanitize_llm_json
from network._llm_models_url import _llm_models_url
from view_creation.build_system_view_creation_prompt import build_system_view_creation_prompt
from utils.build_user_prompt import build_user_prompt
from network.call_llm import call_llm
from RAG.service import get_rag_context, _get_keyword_fallback_context

LLM_API_URL = os.getenv("LLM_API_URL", "http://127.0.0.1:8080/v1/chat/completions")
LLM_MODEL_NAME = os.getenv(
    "LLM_MODEL_NAME",
    "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"
)
# LLM request timeouts (in seconds)
LLM_CONNECT_TIMEOUT = float(os.getenv("LLM_CONNECT_TIMEOUT", "5"))
LLM_READ_TIMEOUT = float(os.getenv("LLM_READ_TIMEOUT", "120"))
LLM_CHAT_READ_TIMEOUT = float(os.getenv("LLM_CHAT_READ_TIMEOUT", str(LLM_READ_TIMEOUT)))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4096"))
LLM_CHAT_MAX_TOKENS = int(os.getenv("LLM_CHAT_MAX_TOKENS", "256"))
CHAT_HISTORY_MAX_MESSAGES = int(os.getenv("CHAT_HISTORY_MAX_MESSAGES", "30"))
CHAT_DOCS_MAX_CHARS = 300
LLM_BUILD_MAX_TOKENS = int(os.getenv("LLM_BUILD_MAX_TOKENS", "4096"))
LLM_BUILD_READ_TIMEOUT = float(os.getenv("LLM_BUILD_READ_TIMEOUT", "120"))
CONVERSATIONS: Dict[str, List[Dict[str, str]]] = {}

app = FastAPI(title="Durus AI Agent Server")

# get LLM Config
@app.get("/debug/llm-config")
def debug_llm_config():
    return {
        "LLM_API_URL": LLM_API_URL,
        "LLM_MODEL_NAME": LLM_MODEL_NAME,
        "LLM_CONNECT_TIMEOUT": LLM_CONNECT_TIMEOUT,
        "LLM_READ_TIMEOUT": LLM_READ_TIMEOUT,
        "LLM_MODELS_URL": _llm_models_url(LLM_API_URL),
    }

# check LLM health
@app.get("/health/llm")
def health_llm():
    """Probes the LLM server to verify reachability and basic functionality."""
    # 1) Try /v1/models if available
    models_url = _llm_models_url(LLM_API_URL)
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
    
# Build view endpoint. ask ai agent to build hmi view.
@app.post("/agent/build_view", response_model=AgentResponse)
def build_view(body: AgentRequest):
    # Build the system prompt for view creation
    system_prompt = build_system_view_creation_prompt()
    
    # RAG: retrieve relevant documentation for the user's prompt
    rag_context = get_rag_context(body.prompt)

    # Fallback: inject key sections from local HMI doc if prompt mentions critical components
    fallback_context = _get_keyword_fallback_context(body.prompt)
    combined_context = rag_context
    if fallback_context:
        combined_context = (rag_context + "\n---\n" + fallback_context) if rag_context else fallback_context
    user_prompt = build_user_prompt(body.prompt, combined_context)

    # Build message list: system + history + new user
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system_prompt},
    ]
    # Always include the user's prompt; add RAG context when available as supplemental system info
    if combined_context:
        messages.append({
            "role": "system",
            "content": (
                "You have access to retrieved project documentation and configuration excerpts. "
                "Use them as the primary source of truth when relevant. "
                "If they conflict with assumptions, prefer the retrieved sources.\n\n"
                f"RAG_CONTEXT_START\n{combined_context}\nRAG_CONTEXT_END"
            ),
        })
    messages.append({"role": "user", "content": user_prompt})
    
    # Call the model
    raw = call_llm(LLM_API_URL, LLM_MODEL_NAME, LLM_BUILD_MAX_TOKENS, LLM_CONNECT_TIMEOUT, LLM_BUILD_READ_TIMEOUT, messages)
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

    # Normalize misplaced top-level keys into proposed_changes for compatibility
    pc = parsed.get("proposed_changes")
    if isinstance(pc, dict):
        # Accept either singular or plural variants from LLM
        if "tags_to_add" in parsed and "tags_to_add" not in pc:
            pc["tags_to_add"] = parsed.pop("tags_to_add")
        if "component_to_add" in parsed and "component_to_add" not in pc:
            pc["component_to_add"] = parsed.pop("component_to_add")
        if "components_to_add" in parsed and "component_to_add" not in pc and "components_to_add" not in pc:
            # prefer normalized singular key inside proposed_changes
            pc["component_to_add"] = parsed.pop("components_to_add")
        # Ensure keys exist with safe defaults
        if "tags_to_add" not in pc:
            pc["tags_to_add"] = {}
        if "component_to_add" not in pc and "components_to_add" not in pc:
            pc["component_to_add"] = {}

    # 5) Build typed response
    try:
        resp_obj = AgentResponse(**parsed)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"LLM JSON missing required fields: {e}",
        )

    return resp_obj