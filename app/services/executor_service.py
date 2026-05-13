import asyncio
import datetime
import os
import re
import time
import uuid
from datetime import datetime as dt
from difflib import SequenceMatcher

from playwright.async_api import async_playwright

from app.schemas.report_schemas import ExecutionReport, ReportStep, ReportSummary
from app.config import settings
from app.services.generator_service import GeneratorService
from app.services.nlp_service import NLPService
from app.services.vision_service import VisionService
from app.utils.logging_config import logger


class ExecutorService:
    def __init__(self, nlp: NLPService = None, vision: VisionService = None):
        self.playwright = None
        self.browser = None
        self.page = None
        self.vision = vision or VisionService()
        self.nlp = nlp or NLPService()
        self.generator = None
        self.execution_id = None
        self.feature_name = None
        self.scenario_name = None
        self.start_time = None
        self.steps = []
        self.screenshots = []

    async def start_session(self, url: str):
        self.execution_id = str(uuid.uuid4())
        self.start_time = dt.now()
        self.steps = []
        self.screenshots = []

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=settings.playwright_headless,
            args=["--no-sandbox"],
            slow_mo=int(os.getenv("PLAYWRIGHT_SLOW_MO", "450")),
        )
        self.page = await self.browser.new_page()
        self.page.set_default_timeout(10000)
        self.page.set_default_navigation_timeout(30000)

        async def handle_dialog(dialog):
            logger.info("ExecutorService: dialog opened: %s", dialog.message)
            await dialog.accept()

        self.page.on("dialog", lambda dialog: asyncio.create_task(handle_dialog(dialog)))
        self.generator = GeneratorService(self.page)
        await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await self.dismiss_popups()
        return self.page

    async def execute_gherkin_step(self, step_text: str):
        logger.info("ExecutorService: executing gherkin step: %s", step_text)
        if not self.page:
            raise RuntimeError("No Playwright session started")

        step_start_time = time.time()
        screenshot_path = None

        try:
            await self.dismiss_popups()
            action_data = await self.nlp.process_step(step_text)
            result = await self._execute_with_retry(action_data)
            screenshot_path = await self._take_step_screenshot(step_text)
            if screenshot_path:
                self.screenshots.append(screenshot_path)

            report_step = ReportStep(
                step_text=step_text,
                action=action_data.get("action"),
                selector=action_data.get("selector"),
                plan_used=result.get("plan_used"),
                value=action_data.get("value"),
                status="passed" if result.get("status") == "success" else "failed",
                message=result.get("message"),
                duration=time.time() - step_start_time,
                screenshot_path=screenshot_path,
                metadata={"nlp_payload": action_data, "execution_result": result},
            )
            self.steps.append(report_step)

            return {
                "status": "completed",
                "step": step_text,
                "action": action_data,
                "result": result,
                "screenshot": screenshot_path,
            }
        except Exception as exc:
            logger.exception("ExecutorService: step execution failed: %s", exc)
            screenshot_path = await self._take_step_screenshot(step_text)
            if screenshot_path:
                self.screenshots.append(screenshot_path)

            report_step = ReportStep(
                step_text=step_text,
                status="failed",
                message=str(exc),
                duration=time.time() - step_start_time,
                screenshot_path=screenshot_path,
                metadata={"exception": str(exc)},
            )
            self.steps.append(report_step)
            raise

    async def _execute_with_retry(self, action_data: dict, max_attempts: int = 2):
        last_error = None
        for attempt in range(1, max_attempts + 1):
            try:
                result = await self._execute_plan_a(action_data)
                if result.get("status") == "success":
                    return result
                raise RuntimeError(result.get("message", "Unknown execution error"))
            except Exception as exc:
                last_error = exc
                logger.warning("ExecutorService: attempt %s failed: %s", attempt, exc)
                if attempt < max_attempts:
                    fallback = await self._execute_plan_b(action_data, original_error=str(exc))
                    if fallback.get("status") == "success":
                        return fallback
                    await asyncio.sleep(1)
                else:
                    raise last_error

    async def _execute_plan_a(self, action_data: dict):
        result = await self.generator.generate_and_execute(action_data, selector=action_data.get("selector"), coordinates=None)
        result["plan_used"] = "plan_a_selector_playwright"
        return result

    async def _execute_plan_b(self, action_data: dict, original_error: str = None):
        logger.info("ExecutorService: running vision fallback for %s", action_data.get("step_text"))
        temp_path = await self._get_temp_screenshot_path("fallback")
        await self.take_screenshot(temp_path)

        # Try to collect DOM nodes from the page to improve vision detection
        dom_nodes = None
        try:
            dom_nodes = await self.page.evaluate("""
                () => {
                    function isVisible(el) {
                        if (!el) return false;
                        const style = window.getComputedStyle(el);
                        if (style.visibility === 'hidden' || style.display === 'none' || parseFloat(style.opacity || '1') === 0) return false;
                        const rect = el.getBoundingClientRect();
                        if (rect.width === 0 || rect.height === 0) return false;
                        return true;
                    }
                    const selectors = ['button','input','a','select','textarea','label','option','[role="button"]','[aria-label]'];
                    const candidates = Array.from(document.querySelectorAll(selectors.join(',')));
                    return candidates
                        .filter(isVisible)
                        .map(el => {
                            const r = el.getBoundingClientRect();
                            const text = (el.innerText || el.value || el.getAttribute('aria-label') || el.getAttribute('alt') || '').toString().trim();
                            return {
                                tag: el.tagName.toLowerCase(),
                                text: text || null,
                                x: r.left + window.scrollX,
                                y: r.top + window.scrollY,
                                width: r.width,
                                height: r.height,
                                id: el.id || null,
                                class: el.className || null,
                                name: el.getAttribute('name') || null,
                                aria_label: el.getAttribute('aria-label') || null,
                                role: el.getAttribute('role') || null
                            };
                        });
                }
            """)
        except Exception:
            dom_nodes = None

        target_text = self._clean_target_text(action_data.get("target"))
        elements = self.vision.detect_and_read(temp_path, target_text=target_text, dom_elements=dom_nodes)
        matched = next((item for item in elements if item.get("is_match")), None)
        if not matched:
            matched = self._best_semantic_match(elements, target_text, action_data.get("action"))

        if matched and self._is_optional_cookie_step(action_data) and not self._is_cookie_consent_control(matched):
            matched = None

        if not matched:
            if self._is_optional_cookie_step(action_data):
                return {
                    "status": "success",
                    "message": "Cookie consent control was not visible; skipped optional cookie step",
                    "plan_used": "plan_b_yolo_ocr",
                    "original_error": original_error,
                }
            return {"status": "error", "message": "Vision fallback did not detect a matching UI element", "plan_used": "plan_b_yolo_ocr", "original_error": original_error}

        coords = matched.get("center")
        if not coords:
            return {"status": "error", "message": "Vision fallback detected element without coordinates", "plan_used": "plan_b_yolo_ocr", "original_error": original_error}

        if action_data.get("action") == "click":
            await self.page.mouse.click(coords[0], coords[1])
            return {"status": "success", "message": f"Clicked on UI element detected by vision at {coords}", "plan_used": "plan_b_yolo_ocr", "matched_element": matched, "original_error": original_error}

        if action_data.get("action") == "input":
            await self.page.mouse.click(coords[0], coords[1])
            await self.page.keyboard.type(action_data.get("value") or "")
            return {"status": "success", "message": f"Typed value into UI element detected by vision at {coords}", "plan_used": "plan_b_yolo_ocr", "matched_element": matched, "original_error": original_error}

        if action_data.get("action") == "select":
            await self.page.mouse.click(coords[0], coords[1])
            await self.page.wait_for_timeout(500)
            return {"status": "success", "message": "Selected UI element via vision fallback", "plan_used": "plan_b_yolo_ocr", "matched_element": matched, "original_error": original_error}

        if action_data.get("action") in ["assert", "expect_visible"]:
            return {"status": "success", "message": "Assertion fallback succeeded by locating visible element via vision", "plan_used": "plan_b_yolo_ocr", "matched_element": matched, "original_error": original_error}

        return {"status": "error", "message": "Vision fallback did not support this action", "plan_used": "plan_b_yolo_ocr", "matched_element": matched, "original_error": original_error}

    @staticmethod
    def _clean_target_text(target: str | None) -> str:
        if not target:
            return ""
        cleaned = str(target).strip()
        text_match = re.match(r"^text=['\"]?(.+?)['\"]?$", cleaned)
        if text_match:
            cleaned = text_match.group(1)
        cleaned = cleaned.replace(" button", "").replace(" field", "").strip("\"' ")
        return cleaned

    @staticmethod
    def _similarity(left: str | None, right: str | None) -> float:
        left = (left or "").lower().strip()
        right = (right or "").lower().strip()
        if not left or not right:
            return 0.0
        if left in right or right in left:
            return 1.0
        return SequenceMatcher(None, left, right).ratio()

    def _best_semantic_match(self, elements: list[dict], target_text: str, action: str | None):
        if not target_text:
            return None

        expected_label = None
        lowered_target = target_text.lower()
        if action == "click":
            expected_label = "button"
        elif action == "input" or any(token in lowered_target for token in ["email", "pass", "password", "field"]):
            expected_label = "input_field"

        scored = []
        for element in elements:
            label = element.get("label")
            text = element.get("text") or ""
            score = self._similarity(target_text, text)
            if expected_label and label == expected_label:
                score += 0.2
            scored.append((score, element))

        if not scored:
            return None

        score, element = max(scored, key=lambda item: item[0])
        if score >= 0.72:
            return element
        return None

    @staticmethod
    def _is_optional_cookie_step(action_data: dict) -> bool:
        text = " ".join(
            str(action_data.get(key) or "")
            for key in ["step_text", "target", "value", "selector"]
        ).lower()
        return action_data.get("action") == "click" and any(token in text for token in ["cookie", "cookies", "consent"])

    @staticmethod
    def _is_cookie_consent_control(element: dict) -> bool:
        text = (element.get("text") or "").lower()
        label = (element.get("label") or "").lower()
        return label == "button" and any(token in text for token in ["allow", "accept", "essential", "optional", "consent"])

    async def dismiss_popups(self):
        if not self.page:
            return

        selectors = [
            'button[aria-label*="close"]',
            'button[aria-label*="Close"]',
            'button:has-text("Close")',
            'button:has-text("Dismiss")',
            'button:has-text("Cancel")',
            'button:has-text("OK")',
            'button:has-text("Accept")',
            'button:has-text("Allow all cookies")',
            'button:has-text("Allow essential and optional cookies")',
            'button:has-text("Only allow essential cookies")',
        ]
        for selector in selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                for element in elements:
                    try:
                        await element.click(timeout=3000)
                        logger.info("ExecutorService: dismissed popup with %s", selector)
                    except Exception:
                        continue
            except Exception:
                continue

    async def _take_step_screenshot(self, step_text: str):
        safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", step_text)[:60]
        directory = os.path.join("reports", "screenshots")
        os.makedirs(directory, exist_ok=True)
        filename = f"step_{datetime.datetime.now():%Y%m%d_%H%M%S}_{safe_name}.png"
        path = os.path.join(directory, filename)
        return await self.take_screenshot(path)

    async def take_screenshot(self, path: str):
        if self.page:
            await self.page.screenshot(path=path)
            return path
        return None

    async def _get_temp_screenshot_path(self, prefix: str):
        directory = os.path.join("reports", "screenshots")
        os.makedirs(directory, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return os.path.join(directory, f"{prefix}_{timestamp}.png")

    async def stop_session(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    def get_execution_report(self) -> ExecutionReport:
        passed = sum(1 for step in self.steps if step.status == "passed")
        failed = sum(1 for step in self.steps if step.status == "failed")
        plan_a_steps = sum(1 for step in self.steps if step.plan_used == "plan_a_selector_playwright")
        plan_b_steps = sum(1 for step in self.steps if step.plan_used == "plan_b_yolo_ocr")
        total_duration = (dt.now() - self.start_time).total_seconds() if self.start_time else 0
        overall_status = "passed" if failed == 0 else "failed"

        return ExecutionReport(
            execution_id=self.execution_id,
            feature_name=self.feature_name,
            scenario_name=self.scenario_name,
            status=overall_status,
            started_at=self.start_time,
            finished_at=dt.now(),
            duration=total_duration,
            steps=self.steps,
            summary=ReportSummary(
                total_steps=len(self.steps),
                passed_steps=passed,
                failed_steps=failed,
                duration=total_duration,
                plan_a_steps=plan_a_steps,
                plan_b_steps=plan_b_steps,
            ),
            screenshots=self.screenshots,
        )
