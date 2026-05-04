import asyncio
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import health, ql_detection, reporting, segmentation, semantic_mapping, test_execution, test_generation
from app.api.nlp_parsing import router as nlp_router
from app.config import settings
from app.utils.logging_config import logger

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # WindowsProactorEventLoopPolicy is already set at module level (required by Playwright).
    # Do NOT override it here — WindowsSelectorEventLoopPolicy breaks async_playwright().
    logger.info("Application is starting up...")

app.include_router(health.router)
app.include_router(nlp_router, prefix="/api")
app.include_router(ql_detection.router, prefix="/api")
app.include_router(test_execution.router, prefix="/api")
app.include_router(test_generation.router, prefix="/api")
app.include_router(reporting.router)
app.include_router(segmentation.router, prefix="/api")
app.include_router(semantic_mapping.router, prefix="/api")
