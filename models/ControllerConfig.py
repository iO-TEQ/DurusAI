from typing import Any, Dict, List
from pydantic import BaseModel

class ControllerConfig(BaseModel):
    database: Dict[str, Any]
    modules: List[Dict[str, Any]]
    hmi: Dict[str, Any]
    charts: List[Dict[str, Any]]
