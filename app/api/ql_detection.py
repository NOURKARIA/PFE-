import os
import time
import tempfile
import urllib.request
import base64
import re
import uuid
from urllib.parse import urlparse
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.schemas.ui_schemas import UIDetectionRequest, UIDetectionResponse
from app.services.vision_service import VisionService

router = APIRouter(prefix="/ia", tags=["Vision"])
vision_service = VisionService()


class ScreenshotAnalysisRequest(BaseModel):
    image_base64: str = Field(..., min_length=1)
    filename: str = "screenshot.png"
    include_ocr: bool = True
    target_text: str | None = None
    min_confidence: float = 0.25


def _safe_upload_filename(filename: str) -> str:
    stem, ext = os.path.splitext(filename or "screenshot.png")
    ext = ext.lower() if ext.lower() in {".png", ".jpg", ".jpeg", ".webp"} else ".png"
    stem = re.sub(r"[^a-zA-Z0-9_-]+", "_", stem).strip("_") or "screenshot"
    return f"{stem}_{uuid.uuid4().hex[:10]}{ext}"


def _save_base64_image(image_base64: str, filename: str) -> str:
    if "," in image_base64:
        image_base64 = image_base64.split(",", 1)[1]
    try:
        image_bytes = base64.b64decode(image_base64, validate=True)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid base64 image data: {exc}")

    upload_dir = os.path.join("data", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    path = os.path.join(upload_dir, _safe_upload_filename(filename))
    with open(path, "wb") as file:
        file.write(image_bytes)
    return path

def _download_image(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="Only http/https URLs are supported for image_path.")
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            if response.status != 200:
                raise HTTPException(status_code=400, detail=f"Failed to download image: HTTP {response.status}")
            suffix = os.path.splitext(parsed.path)[1] or ".jpg"
            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            tmp_file.write(response.read())
            tmp_file.close()
            return tmp_file.name
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to download image URL: {e}")

@router.post("/detect-ui", response_model=UIDetectionResponse)
async def detect_ui(request: UIDetectionRequest):
    start_time = time.time()

    if not request.image_path:
        raise HTTPException(status_code=400, detail="Image path is required")

    local_path = request.image_path
    temp_path = None

    if urlparse(local_path).scheme in ("http", "https"):
        temp_path = _download_image(local_path)
        local_path = temp_path

    try:
        detections = vision_service.detect_ui_elements(
            local_path,
            include_ocr=request.include_ocr,
            target_text=request.target_text,
            min_confidence=request.min_confidence,
            dom_elements=request.dom,
        )
        end_time = time.time()
        return UIDetectionResponse(
            status="success",
            execution_time=end_time - start_time,
            elements=detections
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/analyze-screenshot")
async def analyze_screenshot(request: ScreenshotAnalysisRequest):
    image_path = _save_base64_image(request.image_base64, request.filename)
    detection = await detect_ui(
        UIDetectionRequest(
            image_path=image_path,
            include_ocr=request.include_ocr,
            target_text=request.target_text,
            min_confidence=request.min_confidence,
        )
    )
    return {
        "status": "success",
        "image_path": image_path,
        "detection": detection.model_dump(mode="json"),
    }
