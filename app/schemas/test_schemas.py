from pydantic import BaseModel
from typing import Optional, Dict, Any

class ActionStep(BaseModel):
    step_text: str
    intent: str
    playwright_method: str  # e.g., "click", "fill", "goto"
    selector: Optional[str] = None
    value: Optional[str] = None
    metadata: Dict[str, Any] = {}