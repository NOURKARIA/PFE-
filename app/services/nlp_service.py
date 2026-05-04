from app.utils.gherkin_parser import parse_gherkin_text
from nlp.entity_extractor import entity_extractor
from nlp.intent_classifier import intent_classifier
from app.services.mapping_service import mapping_service
from app.schemas.gherkin_schema import GherkinParseResponse, ScenarioResponse, ActionStepResponse, ActionParameters
from app.utils.logging_config import logger

class NLPService:
    async def process_feature(self, gherkin_text: str) -> GherkinParseResponse:
        try:
            logger.info("NLPService: Starting pipeline...")
            # Validate input early: empty or whitespace-only input should be considered invalid
            if not gherkin_text or not gherkin_text.strip():
                return GherkinParseResponse(status="error", feature_name="Invalid Gherkin")

            parsed_data = parse_gherkin_text(gherkin_text)
            if not parsed_data:
                return GherkinParseResponse(status="error", feature_name="Invalid Gherkin")

            final_scenarios = []
            for scenario in parsed_data.get("scenarios", []):
                scenario_actions = []
                for step in scenario.get("steps", []):
                    step_text = f"{step['keyword']} {step['text']}"
                    
                    # AI Analysis
                    entities = entity_extractor.extract_entities(step_text)
                    intent = intent_classifier.predict_intent(step_text)
                    
                    # Mapping
                    nlp_result = {
                        "step": step_text,
                        "intent": intent,
                        "values": [entities["value"]] if entities["value"] else [],
                        "target": entities["identifier"],
                        "element_type": entities["element_type"],
                    }
                    mapped_action = mapping_service.map_to_action(nlp_result)

                    scenario_actions.append(ActionStepResponse(
                        step_text=step_text,
                        intent=intent,
                        playwright_method=mapped_action.playwright_method,
                        parameters=ActionParameters(
                            value=entities["value"],
                            identifier=entities["identifier"],
                            element_type=entities["element_type"]
                        )
                    ))

                final_scenarios.append(ScenarioResponse(
                    scenario_name=scenario["name"],
                    actions=scenario_actions
                ))

            return GherkinParseResponse(
                feature_name=parsed_data.get("feature_name"),
                scenarios=final_scenarios,
                status="success"
            )
        except Exception as e:
            logger.error(f"NLPService Error: {str(e)}")
            return GherkinParseResponse(status="error", scenarios=[])

    async def process_step(self, step_text: str) -> dict:
        """Process a single Gherkin step into an executable action payload."""
        entities = entity_extractor.extract_entities(step_text)
        intent = intent_classifier.predict_intent(step_text)

        nlp_payload = {
            "step": step_text,
            "intent": intent,
            "values": [entities["value"]] if entities["value"] else [],
            "target": entities["identifier"],
            "element_type": entities["element_type"],
        }
        mapped_action = mapping_service.map_to_action(nlp_payload)

        return {
            "step_text": step_text,
            "action": mapped_action.playwright_method,
            "target": mapped_action.selector or entities["identifier"],
            "value": mapped_action.value,
            "selector": mapped_action.selector,
            "intent": mapped_action.intent,
            "metadata": mapped_action.metadata
        }

gherkin_nlp_service = NLPService()
