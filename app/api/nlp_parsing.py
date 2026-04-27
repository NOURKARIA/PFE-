from fastapi import APIRouter, HTTPException
from typing import List, Union
from app.schemas.gherkin_schema import GherkinParseRequest, GherkinParseResponse
from app.services.nlp_service import gherkin_nlp_service
from app.utils.logging_config import logger

router = APIRouter(prefix="/ia", tags=["Intelligence Artificielle"])

@router.post("/parse-gherkin", response_model=Union[GherkinParseResponse, List[GherkinParseResponse]])
async def parse_gherkin_endpoint(request: Union[GherkinParseRequest, List[str]]):
    logger.info("API: Received request.")

    # BULK CASE []
    if isinstance(request, list):
        results = []
        for text in request:
            res = await gherkin_nlp_service.process_feature(text)
            results.append(res)
        return results

    # SINGLE OBJECT CASE {}
    if not request.gherkin_text.strip():
        raise HTTPException(status_code=400, detail="Empty text")
    
    return await gherkin_nlp_service.process_feature(request.gherkin_text)