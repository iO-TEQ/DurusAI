from typing import Any, Dict, List, Optional
from pydantic import BaseModel

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
    