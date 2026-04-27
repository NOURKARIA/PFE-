import os
from typing import Dict, List

import cv2

from app.utils.logging_config import logger


class SegmentationService:
    def __init__(self):
        logger.info("SegmentationService: Initialized.")

    def segment_image(self, image_path: str) -> Dict:
        """
        Segment structural UI regions using traditional OpenCV contours.
        Returns regions plus debug metadata to explain empty results.
        """
        if not image_path:
            raise ValueError("Image path is required")

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not read image from {image_path}")

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
        dilated = cv2.dilate(edges, kernel, iterations=2)
        contours, _ = cv2.findContours(dilated.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        regions = []
        total_contours = len(contours)
        filtered_small = 0
        filtered_large = 0
        image_area = image.shape[0] * image.shape[1]

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h

            if area <= 500:
                filtered_small += 1
                continue
            if area >= image_area * 0.9:
                filtered_large += 1
                continue

            regions.append(
                {
                    "box": [x, y, x + w, y + h],
                    "width": w,
                    "height": h,
                    "area": area,
                }
            )

        logger.info(
            "SegmentationService: image=%s contours=%s kept=%s filtered_small=%s filtered_large=%s",
            image_path,
            total_contours,
            len(regions),
            filtered_small,
            filtered_large,
        )

        return {
            "regions": regions,
            "debug": {
                "image_path": image_path,
                "image_shape": list(image.shape),
                "total_contours": total_contours,
                "kept_regions": len(regions),
                "filtered_small": filtered_small,
                "filtered_large": filtered_large,
            },
        }


segmentation_service = SegmentationService()
