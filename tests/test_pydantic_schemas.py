import pytest
from pydantic import ValidationError
from datetime import datetime

from app.schemas.gherkin_schema import (
    GherkinParseRequest,
    ActionParameters,
    ActionStepResponse,
    ScenarioResponse,
    GherkinParseResponse
)
from app.schemas.report_schemas import (
    ReportStep,
    ReportSummary,
    ExecutionReport
)

def test_gherkin_parse_request_valid():
    req = GherkinParseRequest(gherkin_text="Feature: test")
    assert req.gherkin_text == "Feature: test"

def test_gherkin_parse_request_invalid():
    with pytest.raises(ValidationError):
        GherkinParseRequest() # Missing required field

def test_action_parameters():
    params = ActionParameters(value="test", identifier="btn", element_type="button")
    assert params.value == "test"
    assert params.identifier == "btn"
    assert params.element_type == "button"
    
    # Default values
    empty_params = ActionParameters()
    assert empty_params.element_type == "element"
    assert empty_params.value is None

def test_action_step_response():
    params = ActionParameters(value="test")
    step = ActionStepResponse(
        step_text="When I do test",
        intent="TEST",
        playwright_method="click",
        parameters=params
    )
    assert step.confidence_score == 1.0 # Default

def test_execution_report_validation():
    now = datetime.now()
    summary = ReportSummary(
        total_steps=1,
        passed_steps=1,
        failed_steps=0,
        duration=1.5
    )
    step = ReportStep(
        step_text="Test",
        status="passed"
    )
    report = ExecutionReport(
        execution_id="123",
        status="passed",
        started_at=now,
        finished_at=now,
        duration=1.5,
        steps=[step],
        summary=summary
    )
    assert report.execution_id == "123"
    assert report.duration == 1.5

def test_execution_report_invalid():
    with pytest.raises(ValidationError):
        ExecutionReport(
            execution_id="123",
            status="passed",
            # missing dates and summary
        )
