from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.services.mapping_service import mapping_service

router = APIRouter(prefix="/ia", tags=["Semantic Mapping"])

class NLPResult(BaseModel):
    step: str
    intent: str
    values: List[str]
    target: Optional[str] = None

class SemanticMappingResponse(BaseModel):
    step_text: str
    intent: str
    playwright_method: str
    selector: Optional[str] = None
    value: Optional[str] = None

@router.post("/semantic-mapping", response_model=SemanticMappingResponse)
async def map_semantics(request: NLPResult):
    """
    Maps an NLP intent and extracted entities to an actionable Playwright step.
    """
    try:
        action_step = mapping_service.map_to_action(request.model_dump())
        
        return SemanticMappingResponse(
            step_text=action_step.step_text,
            intent=action_step.intent,
            playwright_method=action_step.playwright_method,
            selector=action_step.selector,
            value=action_step.value
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
