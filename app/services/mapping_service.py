from app.schemas.test_schemas import ActionStep
from app.utils.logging_config import logger


class MappingService:
    def __init__(self):
        self.intent_to_method = {
            "NAVIGATION": "navigate",
            "ACTION_CLICK": "click",
            "ACTION_TYPE": "input",
            "VERIFICATION": "assert",
            "UNKNOWN": "manual_check",
        }

    def _build_selector_candidates(self, target: str, element_type: str | None = None) -> list[str]:
        if not target or target == "None":
            return []

        normalized = str(target).strip()
        lowered = normalized.lower()
        candidates = [f"text='{normalized}'", f"text={normalized}"]

        if element_type == "button" or "button" in lowered:
            label = normalized.replace("button", "").strip() or normalized
            candidates.extend(
                [
                    f"button:has-text('{label}')",
                    f"[role='button']:has-text('{label}')",
                    f"xpath=//button[contains(normalize-space(.), '{label}')]",
                ]
            )
        elif element_type == "input" or any(token in lowered for token in ["field", "input", "email", "username", "password"]):
            label = normalized.replace("field", "").replace("input", "").strip() or normalized
            candidates.extend(
                [
                    f"input[placeholder*='{label}']",
                    f"input[name*='{label}']",
                    f"input[id*='{label}']",
                    f"xpath=//label[contains(normalize-space(.), '{label}')]/following::input[1]",
                ]
            )
        elif element_type == "link" or "link" in lowered:
            label = normalized.replace("link", "").strip() or normalized
            candidates.extend(
                [
                    f"a:has-text('{label}')",
                    f"xpath=//a[contains(normalize-space(.), '{label}')]",
                ]
            )

        return list(dict.fromkeys([candidate for candidate in candidates if candidate]))

    def map_to_action(self, nlp_result: dict) -> ActionStep:
        intent = nlp_result.get("intent", "UNKNOWN")
        method = self.intent_to_method.get(intent, "manual_check")
        target = nlp_result.get("target", "")
        element_type = nlp_result.get("element_type")
        selector_candidates = self._build_selector_candidates(target, element_type)
        selector = selector_candidates[0] if selector_candidates else None

        action = ActionStep(
            step_text=nlp_result.get("step", ""),
            intent=intent,
            playwright_method=method,
            selector=selector,
            value=nlp_result.get("values")[0] if nlp_result.get("values") else None,
            metadata={
                "raw_nlp": nlp_result,
                "selector_candidates": selector_candidates,
                "element_type": element_type,
            },
        )

        logger.info(f"MappingService: Mapped {intent} to {method}")
        return action


mapping_service = MappingService()
