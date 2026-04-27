import pytest
import os
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from app.utils.screenshot import ScreenshotUtility

@pytest.fixture
def screenshot_util():
    with patch("os.makedirs"):
        return ScreenshotUtility(output_dir="fake_reports")

def test_capture_step_screenshot_success(screenshot_util):
    mock_page = MagicMock()
    mock_page.screenshot = AsyncMock()
    
    with patch("time.time", return_value=12345):
        result = asyncio.run(screenshot_util.capture_step_screenshot(mock_page, "login_step", "passed"))
        
        assert "12345_passed_login_step.png" in result
        mock_page.screenshot.assert_awaited_once()

def test_capture_step_screenshot_error(screenshot_util):
    mock_page = MagicMock()
    mock_page.screenshot = AsyncMock(side_effect=Exception("Screenshot error"))
    
    result = asyncio.run(screenshot_util.capture_step_screenshot(mock_page, "login_step"))
    assert result == ""

def test_capture_element_screenshot_success(screenshot_util):
    mock_page = MagicMock()
    mock_element = MagicMock()
    mock_element.screenshot = AsyncMock()
    mock_page.wait_for_selector = AsyncMock(return_value=mock_element)
    
    result = asyncio.run(screenshot_util.capture_element_screenshot(mock_page, "#btn", "btn.png"))
    
    assert "btn.png" in result
    mock_page.wait_for_selector.assert_awaited_once_with("#btn", timeout=5000)
    mock_element.screenshot.assert_awaited_once()

def test_capture_element_screenshot_not_found(screenshot_util):
    mock_page = MagicMock()
    mock_page.wait_for_selector = AsyncMock(return_value=None)
    
    result = asyncio.run(screenshot_util.capture_element_screenshot(mock_page, "#btn", "btn.png"))
    assert result == ""

def test_capture_element_screenshot_error(screenshot_util):
    mock_page = MagicMock()
    mock_page.wait_for_selector = AsyncMock(side_effect=Exception("Timeout"))
    
    result = asyncio.run(screenshot_util.capture_element_screenshot(mock_page, "#btn", "btn.png"))
    assert result == ""
