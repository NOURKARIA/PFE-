import asyncio
import sys
import re
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.services.executor_service import ExecutorService
from app.services.report_service import report_service
from app.utils.gherkin_parser import parse_gherkin_text
from app.utils.logging_config import logger


router = APIRouter(prefix="/ia", tags=["Execution"])


class TestStepRequest(BaseModel):
    url: str = Field(...)
    step: str = Field(...)
    feature_name: Optional[str] = Field(default=None)
    scenario_name: Optional[str] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)


class TestFeatureRequest(BaseModel):
    url: Optional[str] = Field(default=None)
    gherkin_text: str = Field(...)
    feature_name: Optional[str] = Field(default=None)
    scenario_name: Optional[str] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)


async def _execute_test_async(url: str, step: str, feature_name: Optional[str] = None, scenario_name: Optional[str] = None):
    executor = ExecutorService()
    try:
        await executor.start_session(url)
        executor.feature_name = feature_name
        executor.scenario_name = scenario_name
        result = await executor.execute_gherkin_step(step)
        execution_report = executor.get_execution_report()
        report_paths = report_service.save_both_reports(execution_report)

        return {
            "status": "completed",
            "gherkin_step": step,
            "execution_id": execution_report.execution_id,
            "result": result,
            "reports": report_paths,
        }
    finally:
        try:
            await executor.stop_session()
        except Exception as cleanup_exc:
            logger.warning("execute_test cleanup failed: %s", cleanup_exc)


def _execute_test_in_worker(url: str, step: str, feature_name: Optional[str] = None, scenario_name: Optional[str] = None):
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    return asyncio.run(_execute_test_async(url, step, feature_name, scenario_name))


async def _execute_feature_async(request: TestFeatureRequest):
    parsed = parse_gherkin_text(request.gherkin_text)
    if not parsed or not parsed.get("scenarios"):
        raise ValueError("No scenarios found in the provided Gherkin text")

    scenario = parsed["scenarios"][0]
    steps = scenario.get("steps", [])
    url = request.url

    if not url:
        for step in steps:
            text = step.get("text", "")
            keyword = step.get("keyword", "").strip().lower()
            if keyword.startswith("given") and "navigate to" in text.lower():
                match = re.search(r'"([^"]+)"', text)
                if match:
                    url = match.group(1)
                    break

    if not url:
        raise ValueError("A target URL is required, either in the form or in a Given navigate step")

    executor = ExecutorService()
    try:
        await executor.start_session(url)
        executor.feature_name = request.feature_name or parsed.get("feature_name")
        executor.scenario_name = request.scenario_name or scenario.get("name")

        step_results = []
        for step in steps:
            text = step.get("text", "")
            keyword = step.get("keyword", "").strip().lower()
            if keyword.startswith("given") and "navigate to" in text.lower():
                continue

            try:
                step_results.append(await executor.execute_gherkin_step(text))
            except Exception as exc:
                step_results.append({"status": "failed", "step": text, "error": str(exc)})

        execution_report = executor.get_execution_report()
        report_paths = report_service.save_both_reports(execution_report)

        return {
            "status": "completed",
            "execution_id": execution_report.execution_id,
            "feature_name": execution_report.feature_name,
            "scenario_name": execution_report.scenario_name,
            "summary": execution_report.summary.model_dump(mode="json"),
            "steps": step_results,
            "reports": report_paths,
        }
    finally:
        try:
            await executor.stop_session()
        except Exception as cleanup_exc:
            logger.warning("execute_feature cleanup failed: %s", cleanup_exc)


def _execute_feature_in_worker(request: TestFeatureRequest):
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    return asyncio.run(_execute_feature_async(request))


@router.post("/execute-test")
async def execute_test(request: TestStepRequest):
    try:
        return await asyncio.to_thread(_execute_test_in_worker, request.url, request.step, request.feature_name, request.scenario_name)
    except Exception as exc:
        logger.exception("execute_test failed")
        detail = str(exc) or repr(exc)
        raise HTTPException(status_code=500, detail=detail)


@router.post("/execute-feature")
async def execute_feature(request: TestFeatureRequest):
    try:
        return await asyncio.to_thread(_execute_feature_in_worker, request)
    except Exception as exc:
        logger.exception("execute_feature failed")
        detail = str(exc) or repr(exc)
        raise HTTPException(status_code=500, detail=detail)
