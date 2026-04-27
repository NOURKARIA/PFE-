import asyncio
import sys

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.services.executor_service import ExecutorService
from app.services.report_service import report_service
from app.utils.logging_config import logger


router = APIRouter(prefix="/ia", tags=["Execution"])


class TestStepRequest(BaseModel):
    url: str = Field(...)
    step: str = Field(...)

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)


async def _execute_test_async(url: str, step: str):
    executor = ExecutorService()
    try:
        await executor.start_session(url)
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


def _execute_test_in_worker(url: str, step: str):
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    return asyncio.run(_execute_test_async(url, step))


@router.post("/execute-test")
async def execute_test(request: TestStepRequest):
    try:
        return await asyncio.to_thread(_execute_test_in_worker, request.url, request.step)
    except Exception as exc:
        logger.exception("execute_test failed")
        detail = str(exc) or repr(exc)
        raise HTTPException(status_code=500, detail=detail)
