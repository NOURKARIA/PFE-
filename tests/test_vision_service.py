import pytest
from unittest.mock import MagicMock, patch

from app.services.vision_service import VisionService


@pytest.fixture
def vision_service_mock():
    with patch("app.services.vision_service.YOLOModelWrapper") as mock_wrapper:
        mock_model_instance = MagicMock()
        mock_result = MagicMock()
        mock_box = MagicMock()
        mock_box.xyxy = [[10.0, 20.0, 100.0, 50.0]]
        mock_box.cls = [0]
        mock_box.conf = [0.85]
        mock_result.boxes = [mock_box]

        mock_model_instance.predict.return_value = [mock_result]
        mock_model_instance.available = True
        mock_model_instance.model = MagicMock()
        mock_model_instance.model.names = {0: "button"}

        mock_wrapper.return_value = mock_model_instance
        return VisionService()


def test_detect_ui_elements(vision_service_mock):
    detections = vision_service_mock.detect_ui_elements("fake/path/screenshot.png")

    assert len(detections) == 1
    element = detections[0]
    assert element["label"] == "button"
    assert element["confidence"] == 0.85
    assert element["box"] == [10.0, 20.0, 100.0, 50.0]
    assert element["center"] == [55.0, 35.0]
    assert element["strategy"] == "yolo"


@patch("app.services.vision_service.crop_element")
@patch("app.services.vision_service.summarize_patch")
def test_detect_and_read(mock_summary, mock_crop, vision_service_mock):
    mock_summary.return_value = {"text": "login", "edge_density": 0.2}

    elements = vision_service_mock.detect_and_read("fake/path/screenshot.png", target_text="login")

    assert len(elements) == 1
    assert elements[0]["label"] == "button"
    assert elements[0]["text"] == "login"
    assert elements[0]["is_match"] is True
    assert elements[0]["strategy"] == "yolo+opencv+ocr"
