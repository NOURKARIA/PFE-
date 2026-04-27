from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.generator_service import GeneratorService
from app.services.nlp_service import gherkin_nlp_service


router = APIRouter(prefix="/ia", tags=["Generation"])
script_generator = GeneratorService(page=None)


class PlaywrightGenerationRequest(BaseModel):
    gherkin_text: str = Field(..., min_length=1)
    test_name: Optional[str] = "generated-gherkin-test"
    base_url: Optional[str] = None


class PlaywrightGenerationResponse(BaseModel):
    status: str
    test_name: str
    scenarios_count: int
    script: str
    actions: List[Dict[str, Any]]


@router.post("/generate-test", response_model=PlaywrightGenerationResponse)
async def generate_test(request: PlaywrightGenerationRequest):
    parsed = await gherkin_nlp_service.process_feature(request.gherkin_text)
    if parsed.status != "success" or not parsed.scenarios:
        raise HTTPException(status_code=400, detail="Unable to parse the provided Gherkin feature.")

    script = script_generator.generate_playwright_script(
        parsed_response=parsed,
        test_name=request.test_name or "generated-gherkin-test",
        base_url=request.base_url,
    )
    actions = [action.model_dump(mode="json") for scenario in parsed.scenarios for action in scenario.actions]

    return PlaywrightGenerationResponse(
        status="success",
        test_name=request.test_name or "generated-gherkin-test",
        scenarios_count=len(parsed.scenarios),
        script=script,
        actions=actions,
    )
