import os

import pytest
from fastapi.testclient import TestClient

from app.main import app


RUN_LIVE_INFERENCE = os.getenv("RUN_LIVE_INFERENCE", "").lower() in {"1", "true", "yes"}


UNSEEN_SITE_CASES = [
    {
        "site_name": "Wikipedia",
        "url": "https://www.wikipedia.org/",
        "step": "When I type 'test automation' into the 'Search Wikipedia' field",
        "expected_plan": {"plan_a_selector_playwright", "plan_b_yolo_ocr"},
    },
    {
        "site_name": "Python",
        "url": "https://www.python.org/",
        "step": "When I click the 'Downloads' button",
        "expected_plan": {"plan_a_selector_playwright", "plan_b_yolo_ocr"},
    },
    {
        "site_name": "GitHub Login",
        "url": "https://github.com/login",
        "step": "When I type 'demo@example.com' into the 'Username or email address' field",
        "expected_plan": {"plan_a_selector_playwright", "plan_b_yolo_ocr"},
    },
]


@pytest.mark.skipif(
    not RUN_LIVE_INFERENCE,
    reason="Live inference benchmark is opt-in. Set RUN_LIVE_INFERENCE=1 to execute against real websites.",
)
@pytest.mark.parametrize("case", UNSEEN_SITE_CASES, ids=[case["site_name"] for case in UNSEEN_SITE_CASES])
def test_live_inference_on_unseen_sites(case):
    client = TestClient(app)

    response = client.post(
        "/api/ia/execute-test",
        json={
            "url": case["url"],
            "step": case["step"],
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()

    assert payload["status"] == "completed"
    assert payload["execution_id"]
    assert "reports" in payload
    assert payload["result"]["status"] == "completed"
    assert payload["result"]["result"]["status"] == "success"
    assert payload["result"]["result"]["plan_used"] in case["expected_plan"]


def test_unseen_site_benchmark_definition_contains_three_sites():
    assert len(UNSEEN_SITE_CASES) == 3
