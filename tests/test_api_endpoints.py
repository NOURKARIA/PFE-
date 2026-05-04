from datetime import datetime
from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import reporting, segmentation, semantic_mapping, test_generation
from app.schemas.gherkin_schema import (
    ActionParameters,
    ActionStepResponse,
    GherkinParseResponse,
    ScenarioResponse,
)
from app.schemas.report_schemas import ExecutionReport, ReportStep, ReportSummary


def build_test_client() -> TestClient:
    app = FastAPI()
    app.include_router(semantic_mapping.router, prefix="/api")
    app.include_router(segmentation.router, prefix="/api")
    app.include_router(test_generation.router, prefix="/api")
    app.include_router(reporting.router)
    return TestClient(app)


def make_sample_report(execution_id: str = "exec-api-001") -> ExecutionReport:
    now = datetime.now()
    return ExecutionReport(
        execution_id=execution_id,
        feature_name="Login",
        scenario_name="Happy path",
        status="passed",
        started_at=now,
        finished_at=now,
        duration=1.2,
        steps=[
            ReportStep(
                step_text="When I click login",
                action="click",
                selector="text='login'",
                value=None,
                status="passed",
                message="clicked",
                duration=0.4,
                screenshot_path="reports/screenshots/login.png",
                metadata={"selector_used": "text='login'"},
                plan_used="plan_a_selector_playwright",
            )
        ],
        summary=ReportSummary(
            total_steps=1,
            passed_steps=1,
            failed_steps=0,
            plan_a_steps=1,
            plan_b_steps=0,
            duration=1.2,
        ),
        screenshots=["reports/screenshots/login.png"],
        metadata={"browser": "chromium"},
    )


def test_semantic_mapping_endpoint_returns_selector_candidates_metadata():
    client = build_test_client()

    response = client.post(
        "/api/ia/semantic-mapping",
        json={
            "step": "When I click the login button",
            "intent": "ACTION_CLICK",
            "values": [],
            "target": "login button",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["playwright_method"] == "click"
    assert payload["selector"] == "button[name='login']"
    assert payload["value"] is None


def test_segmentation_endpoint_returns_debug_payload(monkeypatch):
    client = build_test_client()

    monkeypatch.setattr(
        segmentation.segmentation_service,
        "segment_image",
        lambda image_path: {
            "regions": [{"box": [1, 2, 40, 60], "width": 39, "height": 58, "area": 2262}],
            "debug": {
                "image_path": image_path,
                "image_shape": [100, 100, 3],
                "total_contours": 3,
                "kept_regions": 1,
                "filtered_small": 2,
                "filtered_large": 0,
            },
        },
    )

    response = client.post("/api/ia/segment", json={"image_path": "fake/path.png"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert len(payload["regions"]) == 1
    assert payload["debug"]["kept_regions"] == 1


def test_generate_test_endpoint_returns_script_and_actions(monkeypatch):
    client = build_test_client()

    parsed = GherkinParseResponse(
        feature_name="Login feature",
        status="success",
        scenarios=[
            ScenarioResponse(
                scenario_name="Successful login",
                actions=[
                    ActionStepResponse(
                        step_text="When I click the Log In button",
                        intent="ACTION_CLICK",
                        playwright_method="click",
                        parameters=ActionParameters(
                            value="Log In",
                            identifier="Log In button",
                            element_type="button",
                        ),
                    )
                ],
            )
        ],
    )

    monkeypatch.setattr(
        test_generation.gherkin_nlp_service,
        "process_feature",
        AsyncMock(return_value=parsed),
    )

    response = client.post(
        "/api/ia/generate-test",
        json={
            "gherkin_text": "Feature: Login\nScenario: Successful login\nWhen I click the Log In button",
            "test_name": "login_test",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["test_name"] == "login_test"
    assert payload["scenarios_count"] == 1
    assert "import { test, expect } from '@playwright/test';" in payload["script"]
    assert payload["actions"][0]["playwright_method"] == "click"


def test_reporting_list_endpoint_returns_saved_report_summaries(monkeypatch):
    client = build_test_client()
    report = make_sample_report()

    monkeypatch.setattr(
        reporting.report_service,
        "list_json_reports",
        lambda: [("report_exec-api-001_20260426_120000.json", "reports/json/report_exec-api-001.json")],
    )
    monkeypatch.setattr(reporting.report_service, "load_json_report", lambda filepath: report)

    response = client.get("/api/ia/reports")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["total_reports"] == 1
    assert payload["reports"][0]["execution_id"] == "exec-api-001"
    assert payload["reports"][0]["plan_a_steps"] == 1


def test_reporting_summary_endpoint_returns_execution_summary(monkeypatch):
    client = build_test_client()
    report = make_sample_report("exec-api-002")

    monkeypatch.setattr(
        reporting.report_service,
        "list_json_reports",
        lambda: [("report_exec-api-002_20260426_120000.json", "reports/json/report_exec-api-002.json")],
    )
    monkeypatch.setattr(reporting.report_service, "load_json_report", lambda filepath: report)

    response = client.get("/api/ia/reports/exec-api-002/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["execution_id"] == "exec-api-002"
    assert payload["summary"]["total_steps"] == 1
    assert payload["summary"]["plan_a_steps"] == 1
