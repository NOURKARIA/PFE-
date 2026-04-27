import pytest
import asyncio
from app.services.nlp_service import gherkin_nlp_service

def test_process_navigation_step():
    step = "Given I navigate to 'https://example.com'"
    result = asyncio.run(gherkin_nlp_service.process_step(step))
    assert result["intent"] == "NAVIGATION"
    assert "https://example.com" in result["value"]

def test_process_click_step():
    step = "When I click on the 'login' button"
    result = asyncio.run(gherkin_nlp_service.process_step(step))
    assert "click" in result["action"] or result["intent"] == "ACTION_CLICK"

def test_process_type_step():
    step = "And I type 'admin' into the 'username' field"
    result = asyncio.run(gherkin_nlp_service.process_step(step))
    assert result["intent"] == "ACTION_TYPE" or "input" in result["action"]
    assert result["value"] == "admin"

def test_process_verification_step():
    step = "Then I should see the 'dashboard' header"
    result = asyncio.run(gherkin_nlp_service.process_step(step))
    assert result["intent"] == "VERIFICATION" or "assert" in result["action"]

def test_process_full_feature():
    gherkin = '''Feature: Login
      Scenario: Valid login
        Given I navigate to "https://test.com"
        When I click the "login" button
        Then I should see "success"
    '''
    result = asyncio.run(gherkin_nlp_service.process_feature(gherkin))
    assert result.status == "success"
    assert len(result.scenarios) == 1
    assert len(result.scenarios[0].actions) == 3

def test_process_invalid_gherkin():
    gherkin = "This is not a valid gherkin file"
    result = asyncio.run(gherkin_nlp_service.process_feature(gherkin))
    assert result.status == "error"

def test_process_empty_gherkin():
    result = asyncio.run(gherkin_nlp_service.process_feature(""))
    assert result.status == "error"

def test_process_edge_case_gherkin():
    gherkin = '''Feature: Edge Case
      Scenario: Weird steps
        Given I do something weird without quotes
        And another step
    '''
    result = asyncio.run(gherkin_nlp_service.process_feature(gherkin))
    assert result.status == "success"
