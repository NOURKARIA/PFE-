import os
import time
from playwright.async_api import Page
from app.utils.logging_config import logger

class ScreenshotUtility:
    def __init__(self, output_dir="reports/screenshots"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    async def capture_step_screenshot(self, page: Page, step_name: str, status: str = "passed") -> str:
        """
        Captures a screenshot of the current page and saves it with a structured name.
        Returns the relative path to the screenshot.
        """
        try:
            timestamp = int(time.time())
            safe_name = "".join([c if c.isalnum() else "_" for c in step_name])[:30]
            filename = f"{timestamp}_{status}_{safe_name}.png"
            filepath = os.path.join(self.output_dir, filename)
            
            await page.screenshot(path=filepath, full_page=True)
            logger.info(f"ScreenshotUtility: Saved screenshot to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"ScreenshotUtility: Failed to capture screenshot: {e}")
            return ""
            
    async def capture_element_screenshot(self, page: Page, selector: str, filename: str) -> str:
        """
        Captures a screenshot of a specific element on the page.
        """
        try:
            filepath = os.path.join(self.output_dir, filename)
            element = await page.wait_for_selector(selector, timeout=5000)
            if element:
                await element.screenshot(path=filepath)
                logger.info(f"ScreenshotUtility: Saved element screenshot to {filepath}")
                return filepath
            return ""
        except Exception as e:
            logger.error(f"ScreenshotUtility: Failed to capture element screenshot: {e}")
            return ""

# Singleton utility
screenshot_utility = ScreenshotUtility()
