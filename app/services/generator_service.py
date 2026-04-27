import json
import re


class GeneratorService:
    def __init__(self, page):
        self.page = page

    @staticmethod
    def _clean_identifier(identifier: str | None) -> str:
        if not identifier:
            return "body"
        cleaned = identifier.strip().strip("\"'")
        cleaned = re.sub(r"^\s*['\"]|['\"]\s*$", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def _selector_expression(self, identifier: str, element_type: str | None = None) -> str:
        clean = self._clean_identifier(identifier)
        lowered = clean.lower()

        if element_type == "button" or lowered.endswith(" button"):
            label = re.sub(r"\bbutton\b", "", clean, flags=re.IGNORECASE).strip() or clean
            return f"page.getByRole('button', {{ name: {json.dumps(label)}, exact: false }})"

        if element_type == "input":
            label = re.sub(r"\b(field|input)\b", "", clean, flags=re.IGNORECASE).strip() or clean
            escaped = json.dumps(label)
            return f"page.locator(`input[placeholder*=${escaped}], input[name*=${escaped}], input[id*=${escaped}]`).first()"

        return f"page.locator({json.dumps(f'text={clean}')})"

    def generate_playwright_script(self, parsed_response, test_name: str = "generated-gherkin-test", base_url: str = None) -> str:
        lines = []
        navigated_urls = set()

        if base_url:
            lines.append(f"await page.goto({json.dumps(base_url)});")
            navigated_urls.add(base_url)

        for scenario in parsed_response.scenarios:
            for action in scenario.actions:
                params = action.parameters
                identifier = self._clean_identifier(params.identifier)
                element_type = params.element_type or "element"
                value_literal = json.dumps(params.value or "")
                selector_expr = self._selector_expression(identifier, element_type)

                if action.playwright_method == "navigate" and params.value:
                    if params.value not in navigated_urls:
                        lines.append(f"await page.goto({json.dumps(params.value)});")
                        navigated_urls.add(params.value)
                elif action.playwright_method == "click":
                    lines.append(f"await {selector_expr}.click();")
                elif action.playwright_method == "input":
                    lines.append(f"await {selector_expr}.fill({value_literal});")
                elif action.playwright_method in ["assert", "expect_visible"]:
                    lines.append(f"await expect({selector_expr}).toContainText({value_literal});")
                elif action.playwright_method == "select":
                    lines.append(f"await {selector_expr}.selectOption({value_literal});")
                else:
                    lines.append(f"// Manual check required: {action.step_text}")

        body = "\n".join(f"  {line}" for line in lines) if lines else "  // No executable steps generated."
        return "\n".join(
            [
                "import { test, expect } from '@playwright/test';",
                "",
                f"test({json.dumps(test_name)}, async ({{ page }}) => {{",
                body,
                "});",
            ]
        )

    async def generate_and_execute(self, nlp_json: dict, coordinates: list = None, selector: str = None):
        action = nlp_json.get("action")
        target = nlp_json.get("target")
        value = nlp_json.get("value")
        selector_candidates = nlp_json.get("metadata", {}).get("selector_candidates", [])
        selectors_to_try = [candidate for candidate in [selector, *selector_candidates] if candidate]
        selectors_to_try = list(dict.fromkeys(selectors_to_try))

        if action == "navigate":
            await self.page.goto(value)
            return {"status": "success", "message": f"Navigated to {value}"}

        elif action == "click":
            for candidate in selectors_to_try:
                try:
                    await self.page.click(candidate, timeout=5000)
                    return {"status": "success", "message": f"Clicked selector {candidate}", "selector_used": candidate}
                except Exception:
                    continue
            if coordinates:
                await self.page.mouse.click(coordinates[0], coordinates[1])
                return {"status": "success", "message": f"Clicked on {target} at {coordinates}"}
            return {"status": "error", "message": "No selector or coordinates found for click"}

        elif action == "input":
            for candidate in selectors_to_try:
                try:
                    await self.page.fill(candidate, value or "")
                    return {"status": "success", "message": f"Typed '{value}' into {candidate}", "selector_used": candidate}
                except Exception:
                    continue
            if coordinates:
                await self.page.mouse.click(coordinates[0], coordinates[1])
                await self.page.keyboard.type(value or "")
                return {"status": "success", "message": f"Typed '{value}' into {target} at {coordinates}"}
            return {"status": "error", "message": "No selector or coordinates found for input"}

        elif action == "wait":
            if value and str(value).isdigit():
                await self.page.wait_for_timeout(int(value) * 1000)
            else:
                await self.page.wait_for_load_state("networkidle")
            return {"status": "success", "message": "Waiting completed"}

        elif action == "select":
            for candidate in selectors_to_try:
                try:
                    await self.page.select_option(candidate, value=value)
                    return {"status": "success", "message": f"Selected '{value}' in {candidate}", "selector_used": candidate}
                except Exception:
                    try:
                        await self.page.click(candidate)
                        return {"status": "success", "message": f"Opened dropdown {candidate}", "selector_used": candidate}
                    except Exception:
                        continue
            if coordinates:
                await self.page.mouse.click(coordinates[0], coordinates[1])
                await self.page.wait_for_timeout(500)
                return {"status": "success", "message": f"Clicked dropdown {target} at {coordinates}"}
            return {"status": "error", "message": "No selector or coordinates found for select"}

        elif action in ["assert", "expect_visible"]:
            if not selectors_to_try:
                return {"status": "error", "message": "No selector provided for assertion"}
            for candidate in selectors_to_try:
                try:
                    locator = self.page.locator(candidate)
                    await locator.wait_for(state="visible", timeout=3000)
                    if value:
                        actual_text = await locator.inner_text()
                        if value not in actual_text:
                            continue
                    return {"status": "success", "message": f"Assertion passed for {candidate}", "selector_used": candidate}
                except Exception:
                    continue
            return {"status": "error", "message": "Assertion failed for all selector candidates"}

        elif action in ["alert", "dialog"]:
            return {"status": "success", "message": "Dialog or alert is handled by the execution session"}

        return {"status": "error", "message": f"Unknown action '{action}'"}
