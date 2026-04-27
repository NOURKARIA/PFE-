import asyncio
from unittest.mock import AsyncMock, Mock

from app.services.executor_service import ExecutorService


def test_execute_gherkin_step_calls_generator_and_saves_screenshot():
    service = ExecutorService()
    service.page = Mock()
    service.page.query_selector_all = AsyncMock(return_value=[])
    service.generator = Mock()
    service.generator.generate_and_execute = AsyncMock(return_value={"status": "success", "message": "Clicked via selector"})
    service.nlp = Mock(process_step=AsyncMock(return_value={
        "step_text": "When I click the submit button",
        "action": "click",
        "target": "submit button",
        "value": None,
        "selector": "#submit",
        "intent": "ACTION_CLICK",
        "metadata": {}
    }))
    service._take_step_screenshot = AsyncMock(return_value="reports/screenshots/step_click.png")

    result = asyncio.run(service.execute_gherkin_step("When I click the submit button"))

    assert result["status"] == "completed"
    assert result["result"]["status"] == "success"
    assert result["screenshot"] == "reports/screenshots/step_click.png"
    assert result["result"]["plan_used"] == "plan_a_selector_playwright"
    service.generator.generate_and_execute.assert_awaited_once()


def test_execute_gherkin_step_uses_plan_b_when_plan_a_fails():
    service = ExecutorService()
    service.page = Mock()
    service.page.query_selector_all = AsyncMock(return_value=[])
    service.generator = Mock()
    service.generator.generate_and_execute = AsyncMock(side_effect=RuntimeError("selector failed"))
    service.nlp = Mock(process_step=AsyncMock(return_value={
        "step_text": "When I click the submit button",
        "action": "click",
        "target": "submit button",
        "value": None,
        "selector": "#submit",
        "intent": "ACTION_CLICK",
        "metadata": {}
    }))
    service._take_step_screenshot = AsyncMock(return_value="reports/screenshots/step_click.png")
    service._execute_plan_b = AsyncMock(return_value={
        "status": "success",
        "message": "Clicked via yolo fallback",
        "plan_used": "plan_b_yolo_ocr",
    })

    result = asyncio.run(service.execute_gherkin_step("When I click the submit button"))

    assert result["result"]["plan_used"] == "plan_b_yolo_ocr"
    service._execute_plan_b.assert_awaited_once()

import datetime
from app.schemas.report_schemas import ReportStep

def test_get_execution_report():
    service = ExecutorService()
    service.execution_id = "test-exec-id"
    service.start_time = datetime.datetime.now()
    service.steps = [
        ReportStep(step_text="Step 1", status="passed", plan_used="plan_a_selector_playwright", duration=1.0),
        ReportStep(step_text="Step 2", status="failed", plan_used="plan_b_yolo_ocr", duration=2.0)
    ]
    report = service.get_execution_report()
    assert report.execution_id == "test-exec-id"
    assert report.status == "failed"
    assert report.summary.passed_steps == 1
    assert report.summary.failed_steps == 1
    assert report.summary.plan_a_steps == 1
    assert report.summary.plan_b_steps == 1
