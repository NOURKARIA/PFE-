import os
from typing import Any, List

from ultralytics import YOLO


class YOLOModelWrapper:
    """Small adapter around Ultralytics YOLO to keep service code simple."""

    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = YOLO(model_path) if os.path.exists(model_path) and os.path.getsize(model_path) > 0 else None

    @property
    def available(self) -> bool:
        return self.model is not None

    def predict(self, image_path: str, conf: float = 0.1) -> List[Any]:
        if not self.model:
            return []
        return self.model.predict(source=image_path, conf=conf)
