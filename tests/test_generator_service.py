import asyncio
from unittest.mock import AsyncMock, Mock

from app.schemas.gherkin_schema import ActionParameters, ActionStepResponse, GherkinParseResponse, ScenarioResponse
from app.services.generator_service import GeneratorService


class DummyPage:
    def __init__(self):
        self.goto = AsyncMock()
        self.click = AsyncMock()
        self.fill = AsyncMock()
        self.keyboard = Mock()
        self.keyboard.type = AsyncMock()
        self.wait_for_timeout = AsyncMock()
        self.wait_for_load_state = AsyncMock()
        self.select_option = AsyncMock()

        locator_obj = Mock()
        locator_obj.wait_for = AsyncMock()
        locator_obj.inner_text = AsyncMock(return_value="welcome admin")
        self.locator = Mock(return_value=locator_obj)


def test_generate_and_execute_navigate():
    page = DummyPage()
    generator = GeneratorService(page)

    result = asyncio.run(generator.generate_and_execute({"action": "navigate", "target": None, "value": "https://example.com"}))

    assert result["status"] == "success"
    assert "Navigated to" in result["message"]
    page.goto.assert_awaited_once_with("https://example.com")


def test_generate_and_execute_click_with_selector():
    page = DummyPage()
    generator = GeneratorService(page)

    result = asyncio.run(generator.generate_and_execute({"action": "click", "target": "button", "value": None}, selector="#button"))

    assert result["status"] == "success"
    page.click.assert_awaited_once_with("#button", timeout=5000)


def test_generate_and_execute_input_with_selector():
    page = DummyPage()
    generator = GeneratorService(page)

    result = asyncio.run(generator.generate_and_execute({"action": "input", "target": "username", "value": "admin"}, selector="#username"))

    assert result["status"] == "success"
    page.fill.assert_awaited_once_with("#username", "admin")


def test_generate_and_execute_assert_with_selector():
    page = DummyPage()
    generator = GeneratorService(page)

    result = asyncio.run(generator.generate_and_execute({"action": "assert", "target": "username", "value": "admin", "selector": "#username"}, selector="#username"))

    assert result["status"] == "success"
    page.locator.assert_called_once_with("#username")


def test_generate_playwright_script_avoids_duplicate_navigation_and_uses_better_selectors():
    generator = GeneratorService(page=None)
    parsed = GherkinParseResponse(
        feature_name="Login to Facebook",
        status="success",
        scenarios=[
            ScenarioResponse(
                scenario_name="Successful login",
                actions=[
                    ActionStepResponse(
                        step_text="Given I am on 'https://www.facebook.com/'",
                        intent="NAVIGATION",
                        playwright_method="navigate",
                        parameters=ActionParameters(value="https://www.facebook.com/", identifier=None, element_type="element"),
                    ),
                    ActionStepResponse(
                        step_text="When I type 'nour.karia@horizon.tn' into the 'email' field",
                        intent="ACTION_TYPE",
                        playwright_method="input",
                        parameters=ActionParameters(value="nour.karia@horizon.tn", identifier="email", element_type="input"),
                    ),
                    ActionStepResponse(
                        step_text="And I click the 'Log In' button",
                        intent="ACTION_CLICK",
                        playwright_method="click",
                        parameters=ActionParameters(value="Log In", identifier="'log in' button", element_type="button"),
                    ),
                ],
            )
        ],
    )

    script = generator.generate_playwright_script(
        parsed_response=parsed,
        test_name="facebook_login_test",
        base_url="https://www.facebook.com/",
    )

    assert script.count('await page.goto("https://www.facebook.com/");') == 1
    assert "input[placeholder*" in script or "input[name*" in script or "input[id*" in script
    assert "getByRole('button'" in script
