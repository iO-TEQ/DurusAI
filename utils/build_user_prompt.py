import json
from typing import Any, Dict

# Build the user prompt part
# This wraps the user prompt and context into a JSON blob.
def build_user_prompt(prompt: str, context: Dict[str, Any]) -> str:
    """
    Wrap user prompt + context into one JSON blob for the model.
    """
    payload = {
        "user_request": prompt,
        "device_context": context,
    }
    return json.dumps(payload, indent=2)
