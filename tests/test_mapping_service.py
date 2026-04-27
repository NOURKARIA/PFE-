from app.services.mapping_service import mapping_service


def test_map_click_intent_to_playwright_action():
    action = mapping_service.map_to_action(
        {
            "step": "When I click the login button",
            "intent": "ACTION_CLICK",
            "values": [],
            "target": "login button",
        }
    )

    assert action.playwright_method == "click"
    assert action.selector == "text='login button'"
    assert action.value is None


def test_map_navigation_intent_uses_navigate_method():
    action = mapping_service.map_to_action(
        {
            "step": "Given I navigate to https://example.com",
            "intent": "NAVIGATION",
            "values": ["https://example.com"],
            "target": "None",
        }
    )

    assert action.playwright_method == "navigate"
    assert action.value == "https://example.com"
    assert action.selector is None
