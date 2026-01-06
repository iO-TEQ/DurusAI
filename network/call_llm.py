from http.client import HTTPException
from typing import Dict, List
import requests

# Call the LLM with given messages and return the response content
def call_llm(url, model, max_tokens, connect_timeout, read_timeout, messages: List[Dict[str, str]]) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.1, # low temperature for more deterministic output, higher for more creative
        "max_tokens": max_tokens, # limit response length. max tokens are approx 4 chars each. default 2048===>8192 chars
    }

    try:
        print("\n[AGENT DEBUG] Calling LLM:", url)
        # Avoid logging full payload content to keep logs tidy
        print("[AGENT DEBUG] Model:", payload.get("model"), "Messages:", len(payload.get("messages", [])))
        resp = requests.post(
            url,
            json=payload,
            timeout=(connect_timeout, read_timeout),
        )
        resp.raise_for_status()                             
    except requests.Timeout as e:
        raise HTTPException(status_code=504, detail=f"LLM read timeout: {e}")
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
