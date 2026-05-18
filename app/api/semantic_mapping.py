from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator
from typing import Any, List, Optional
from app.services.mapping_service import mapping_service

router = APIRouter(prefix="/ia", tags=["Semantic Mapping"])

class SemanticMappingRequest(BaseModel):
    step: Optional[str] = None
    step_text: Optional[str] = None
    intent: Optional[str] = None
    values: List[str] = Field(default_factory=list)
    target: Optional[str] = None
    value: Optional[str] = None
    element_type: Optional[str] = None

    @model_validator(mode="after")
    def validate_step_text(self):
        if not (self.step or self.step_text):
            raise ValueError("Either 'step' or 'step_text' is required.")
        return self

class SemanticMappingResponse(BaseModel):
    step_text: str
    intent: str
    playwright_method: str
    selector: Optional[str] = None
    value: Optional[str] = None
    selector_candidates: List[str] = Field(default_factory=list)
    element_type: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

@router.post("/semantic-mapping", response_model=SemanticMappingResponse)
async def map_semantics(request: SemanticMappingRequest):
    """
    Maps a raw Gherkin step or an NLP payload to an actionable Playwright step.
    """
    try:
        step_text = request.step or request.step_text or ""

        if request.intent:
            values = list(request.values)
            if request.value and request.value not in values:
                values.insert(0, request.value)
            nlp_payload = {
                "step": step_text,
                "intent": request.intent,
                "values": values,
                "target": request.target,
                "element_type": request.element_type,
            }
            action_step = mapping_service.map_to_action(nlp_payload)
        else:
            from app.services.nlp_service import gherkin_nlp_service

            processed = await gherkin_nlp_service.process_step(step_text)
            metadata = processed.get("metadata", {})
            return SemanticMappingResponse(
                step_text=step_text,
                intent=processed.get("intent", "UNKNOWN"),
                playwright_method=processed.get("action", "manual_check"),
                selector=processed.get("selector"),
                value=processed.get("value"),
                selector_candidates=metadata.get("selector_candidates", []),
                element_type=metadata.get("element_type"),
                metadata=metadata,
            )

        metadata = action_step.metadata or {}
        return SemanticMappingResponse(
            step_text=action_step.step_text,
            intent=action_step.intent,
            playwright_method=action_step.playwright_method,
            selector=action_step.selector,
            value=action_step.value,
            selector_candidates=metadata.get("selector_candidates", []),
            element_type=metadata.get("element_type"),
            metadata=metadata,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
