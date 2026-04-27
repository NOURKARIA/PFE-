from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class UIDetectionRequest(BaseModel):
    image_path: str
    include_ocr: bool = False
    target_text: Optional[str] = None
    min_confidence: float = 0.25


class UIElement(BaseModel):
    label: str
    confidence: float
    box: List[float]
    center: List[float]
    text: Optional[str] = None
    is_match: Optional[bool] = None
    strategy: Optional[str] = None


class UIDetectionResponse(BaseModel):
    status: str
    execution_time: float
    elements: List[UIElement]


class SegmentationRequest(BaseModel):
    image_path: str


class RegionResponse(BaseModel):
    box: List[int]
    width: int
    height: int
    area: int


class SegmentationResponse(BaseModel):
    status: str
    execution_time: float
    regions: List[RegionResponse]
    message: Optional[str] = None
    debug: Optional[Dict[str, Any]] = None
