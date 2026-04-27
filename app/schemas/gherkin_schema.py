from pydantic import BaseModel
from typing import List, Union, Optional

# --- REQUEST ---
class GherkinParseRequest(BaseModel):
    gherkin_text: str

# --- RESPONSE SUB-MODELS ---
class ActionParameters(BaseModel):
    value: Optional[str] = None
    identifier: Optional[str] = None
    element_type: Optional[str] = "element"

class ActionStepResponse(BaseModel):
    step_text: str
    intent: str
    playwright_method: str
    parameters: ActionParameters
    confidence_score: Optional[float] = 1.0

class ScenarioResponse(BaseModel):
    scenario_name: str
    actions: List[ActionStepResponse]

# --- FINAL RESPONSE ---
class GherkinParseResponse(BaseModel):
    feature_name: Optional[str] = "Untitled Feature"
    scenarios: List[ScenarioResponse]
    status: str = "success"