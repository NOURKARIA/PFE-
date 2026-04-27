import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Smart Searcher AI Agent")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    reports_dir: str = os.getenv("REPORTS_DIR", "reports")
    nlp_model_dir: str = os.getenv("NLP_MODEL_DIR", "trained_models/nlp")
    vision_model_path: str = os.getenv(
        "VISION_MODEL_PATH",
        "trained_models/vision/yolov8_ui_elements.pt",
    )
    playwright_headless: bool = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
