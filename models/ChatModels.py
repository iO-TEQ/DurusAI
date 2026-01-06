from typing import Optional
from pydantic import BaseModel

class ChatRequest(BaseModel):
    prompt: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
