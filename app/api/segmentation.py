import time

from fastapi import APIRouter, HTTPException

from app.schemas.ui_schemas import SegmentationRequest, SegmentationResponse
from app.services.segmentation_service import segmentation_service


router = APIRouter(prefix="/ia", tags=["Vision Segmentation"])


@router.post("/segment", response_model=SegmentationResponse)
async def segment_ui(request: SegmentationRequest):
    """
    Analyze an image and return structural UI regions with debug metadata.
    """
    start_time = time.time()

    if not request.image_path:
        raise HTTPException(status_code=400, detail="Image path is required")

    try:
        result = segmentation_service.segment_image(request.image_path)
        end_time = time.time()
        regions = result["regions"]
        debug = result["debug"]

        message = None
        if not regions:
            message = (
                "No structural UI regions were detected. "
                "This usually means the image has weak contours for the current OpenCV settings."
            )

        return SegmentationResponse(
            status="success",
            execution_time=end_time - start_time,
            regions=regions,
            message=message,
            debug=debug,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
