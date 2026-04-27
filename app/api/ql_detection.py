import os
import time
import tempfile
import urllib.request
from urllib.parse import urlparse
from fastapi import APIRouter, HTTPException
from app.schemas.ui_schemas import UIDetectionRequest, UIDetectionResponse
from app.services.vision_service import VisionService

router = APIRouter(prefix="/ia", tags=["Vision"])
vision_service = VisionService()

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
