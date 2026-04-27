import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from app.utils.image_processing import (
    crop_element,
    preprocess_patch_for_ocr,
    extract_text_from_patch,
    summarize_patch
)

@patch("app.utils.image_processing.cv2.imread")
def test_crop_element_success(mock_imread):
    # Mocking image: 100x100
    mock_imread.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
    
    result = crop_element("fake_path", [10, 10, 50, 50])
    assert result.shape == (40, 40, 3)

@patch("app.utils.image_processing.cv2.imread")
def test_crop_element_not_found(mock_imread):
    mock_imread.return_value = None
    result = crop_element("fake_path", [10, 10, 50, 50])
    assert result is None

def test_preprocess_patch_for_ocr():
    # Provide a simple white patch
    patch_img = np.ones((50, 50, 3), dtype=np.uint8) * 255
    processed = preprocess_patch_for_ocr(patch_img)
    assert processed is not None
    assert len(processed.shape) == 2 # Grayscale/Binary
    
def test_preprocess_patch_for_ocr_none():
    assert preprocess_patch_for_ocr(None) is None

@patch("app.utils.image_processing.pytesseract.image_to_string")
def test_extract_text_from_patch(mock_tesseract):
    mock_tesseract.return_value = "Login "
    patch_img = np.ones((50, 50, 3), dtype=np.uint8) * 255
    text = extract_text_from_patch(patch_img)
    assert text == "Login"

@patch("app.utils.image_processing.pytesseract.image_to_string")
def test_extract_text_from_patch_error(mock_tesseract):
    mock_tesseract.side_effect = Exception("Tesseract error")
    patch_img = np.ones((50, 50, 3), dtype=np.uint8) * 255
    text = extract_text_from_patch(patch_img)
    assert text == ""

@patch("app.utils.image_processing.extract_text_from_patch")
def test_summarize_patch(mock_extract):
    mock_extract.return_value = "Login"
    patch_img = np.zeros((50, 50, 3), dtype=np.uint8)
    # Put a white rectangle to have some edges
    patch_img[10:40, 10:40] = 255
    
    summary = summarize_patch(patch_img)
    assert summary["text"] == "Login"
    assert summary["edge_density"] > 0.0

def test_summarize_patch_none():
    summary = summarize_patch(None)
    assert summary["text"] == ""
    assert summary["edge_density"] == 0.0
