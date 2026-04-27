import pytest
from unittest.mock import MagicMock

# 1. Gherkin Fixture: Used by test_nlp_service.py
@pytest.fixture
def raw_gherkin_string():
    return """
    Feature: Authentication
      Scenario: Login with valid credentials
        When I enter "nour@addinn.com" in the "Email" field
        And I click the "Login" button
    """

# 2. Vision Fixture: Used by test_vision_service.py
@pytest.fixture
def mock_detection_results():
    return [
        {"label": "button", "box": [50, 100, 80, 200], "conf": 0.98, "text": "Login"},
        {"label": "input", "box": [10, 100, 40, 200], "conf": 0.95, "text": "Email"}
    ]

# 3. Mapping Fixture: Used by test_mapping_service.py
@pytest.fixture
def sample_mapping_data():
    return {
        "action": "click",
        "target": "Login",
        "coordinates": {"x": 65, "y": 150}
    }