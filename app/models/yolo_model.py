import os
from typing import Any, List

from ultralytics import YOLO

from app.utils.logging_config import logger


class YOLOModelWrapper:
    """Small adapter around Ultralytics YOLO to keep service code simple."""

    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
        if not os.path.exists(model_path) or os.path.getsize(model_path) == 0:
            logger.warning("YOLOModelWrapper: model file is missing or empty: %s", model_path)
            return

        try:
            with open(model_path, "rb") as file:
                header = file.read(64)
            if header.startswith(b"version https://git-lfs"):
                logger.warning(
                    "YOLOModelWrapper: %s is a Git LFS pointer, not a real model file. "
                    "Vision fallback will be disabled.",
                    model_path,
                )
                return

            self.model = YOLO(model_path)
        except Exception as exc:
            logger.warning(
                "YOLOModelWrapper: failed to load model %s. Vision fallback will be disabled. Error: %s",
                model_path,
                exc,
            )

    @property
    def available(self) -> bool:
        return self.model is not None

    def predict(self, image_path: str, conf: float = 0.1) -> List[Any]:
        if not self.model:
            return []
        return self.model.predict(source=image_path, conf=conf)
