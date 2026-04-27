import os
from typing import Any, Dict, Optional

import cv2
import numpy as np
import pytesseract

from app.utils.logging_config import logger


DEFAULT_TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(DEFAULT_TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = DEFAULT_TESSERACT_PATH


def crop_element(image_path: str, box: list):
    """Return a cropped image patch for a detected bounding box."""
    img = cv2.imread(image_path)
    if img is None:
        return None

    x1, y1, x2, y2 = map(int, box)
    h, w = img.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    return img[y1:y2, x1:x2]


def preprocess_patch_for_ocr(image_patch):
    """Use OpenCV to clean a patch before OCR."""
    if image_patch is None or image_patch.size == 0:
        return None

    gray = cv2.cvtColor(image_patch, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    _, thresholded = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresholded


def extract_text_from_patch(image_patch) -> str:
    """Extract OCR text from a cropped patch."""
    processed = preprocess_patch_for_ocr(image_patch)
    if processed is None:
        return ""

    try:
        config = "--psm 6"
        text = pytesseract.image_to_string(processed, config=config)
        return text.strip()
    except Exception as exc:
        logger.warning("image_processing: OCR extraction failed: %s", exc)
        return ""


def summarize_patch(image_patch) -> Dict[str, Any]:
    """Return lightweight OpenCV features helpful for ranking UI candidates."""
    processed = preprocess_patch_for_ocr(image_patch)
    if processed is None:
        return {"text": "", "edge_density": 0.0}

    edge_map = cv2.Canny(processed, 50, 150)
    edge_density = float(np.count_nonzero(edge_map)) / float(edge_map.size) if edge_map.size else 0.0
    text = extract_text_from_patch(image_patch)
    return {"text": text, "edge_density": edge_density}
