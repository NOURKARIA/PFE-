import os
import re

import torch
from transformers import DistilBertForTokenClassification, DistilBertTokenizerFast

from app.utils.logging_config import logger


class EntityExtractor:
    def __init__(self, model_path='trained_models/nlp/entity_extractor.pt'):
        self.model = None
        self.tokenizer = None
        self.id2label = {0: "O", 1: "B-TARGET", 2: "I-TARGET", 3: "B-VALUE", 4: "I-VALUE"}

        if os.getenv("DISABLE_NLP_MODELS", "").lower() in {"1", "true", "yes"}:
            logger.info("EntityExtractor: DISABLE_NLP_MODELS is enabled, using rule-based extraction.")
            return

        try:
            logger.info(f"EntityExtractor: Loading LLM Token Classifier from {model_path}...")
            self.tokenizer = DistilBertTokenizerFast.from_pretrained('distilbert-base-uncased')

            # Prefer loading a transformers save_pretrained directory if present
            if os.path.isdir(model_path):
                logger.info(f"EntityExtractor: Loading pretrained model directory from {model_path}...")
                self.model = DistilBertForTokenClassification.from_pretrained(model_path)
                self.model.eval()
                logger.info("EntityExtractor: Loaded model from directory.")
            else:
                # default: create model architecture and try to load a state_dict .pt file
                self.model = DistilBertForTokenClassification.from_pretrained('distilbert-base-uncased', num_labels=5)
                if os.path.exists(model_path):
                    self.model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
                    self.model.eval()
                    logger.info("EntityExtractor: LLM Model loaded successfully from state_dict.")
                else:
                    logger.warning(f"EntityExtractor: Model file not found at {model_path}, using rules.")
                    self.model = None
        except Exception as e:
            logger.warning(f"EntityExtractor: Falling back to rule-based extraction: {e}")
            self.model = None
            self.tokenizer = None

    def _extract_with_rules(self, step_text: str):
        quoted_values = [double or single for double, single in re.findall(r'"([^"]*)"|\'([^\']*)\'', step_text)]
        value = quoted_values[0] if quoted_values else None
        identifier = quoted_values[1] if len(quoted_values) > 1 else None
        lower = step_text.lower()

        fill_match = re.search(
            r"(?:fill|type|enter|write)\s+(?:the\s+)?['\"]?([^'\"]+?)['\"]?\s+(?:field|input)?\s+with\s+['\"]([^'\"]+)['\"]",
            step_text,
            flags=re.IGNORECASE,
        )
        if fill_match:
            identifier = fill_match.group(1).strip()
            value = fill_match.group(2).strip()

        type_into_match = re.search(
            r"(?:type|enter|write)\s+['\"]([^'\"]+)['\"]\s+(?:into|in)\s+(?:the\s+)?['\"]?([^'\"]+?)['\"]?\s*(?:field|input)?(?:\s|$)",
            step_text,
            flags=re.IGNORECASE,
        )
        if type_into_match:
            value = type_into_match.group(1).strip()
            identifier = type_into_match.group(2).strip()

        click_match_quoted = re.search(
            r"(?:click|press|tap|select)(?:\s+on)?\s+(?:the\s+)?['\"]([^'\"]+)['\"]\s*(button|link)?",
            step_text,
            flags=re.IGNORECASE,
        )
        if click_match_quoted:
            identifier = " ".join(part for part in click_match_quoted.groups() if part).strip()
            value = None

        if not value:
            url_match = re.search(r"https?://\S+", step_text)
            if url_match:
                value = url_match.group(0).rstrip(".,)")

        if not identifier:
            click_match = re.search(r"(?:click|press|tap|select)(?: on| the)? (.+)", step_text, flags=re.IGNORECASE)
            if click_match:
                identifier = click_match.group(1).strip().strip(" .")
                value = None

        if not identifier:
            into_match = re.search(r"(?:into|in|on) the ['\"]?([^'\"]+)['\"]?", step_text, flags=re.IGNORECASE)
            if into_match:
                identifier = into_match.group(1).strip()

        if any(token in lower for token in ["should see", "verify", "expect"]) and quoted_values:
            identifier = quoted_values[-1]
            value = quoted_values[-1]

        element_type = "element"
        candidate = (identifier or "").lower()
        if any(token in lower for token in ["should see", "verify", "expect", "assert"]):
            element_type = "element"
        elif "button" in candidate:
            element_type = "button"
        elif any(token in candidate for token in ["field", "input", "username", "email", "password", "pass"]):
            element_type = "input"
        elif "header" in candidate:
            element_type = "header"

        return {"value": value, "identifier": identifier, "element_type": element_type}

    def extract_entities(self, step_text: str):
        # Prefer simple rule-based extraction when quoted literals are present
        rules_result = self._extract_with_rules(step_text)
        if rules_result.get("value") or rules_result.get("identifier"):
            return rules_result

        if not self.model:
            return rules_result

        try:
            inputs = self.tokenizer(step_text, return_offsets_mapping=True, return_tensors="pt", truncation=True, padding=True)
            offset_mapping = inputs.pop("offset_mapping")[0]

            with torch.no_grad():
                outputs = self.model(**inputs)

            predictions = torch.argmax(outputs.logits, dim=2)[0]
            entities = {"TARGET": [], "VALUE": []}

            for idx, pred_id in enumerate(predictions):
                # pred_id is a torch.tensor scalar - convert to Python int for dict lookup
                pred_idx = int(pred_id.item()) if hasattr(pred_id, 'item') else int(pred_id)
                label = self.id2label.get(pred_idx, "O")
                if label != "O":
                    start, end = offset_mapping[idx]
                    word = step_text[start:end]
                    if "TARGET" in label:
                        entities["TARGET"].append(word)
                    elif "VALUE" in label:
                        entities["VALUE"].append(word)

            target_str = " ".join(entities["TARGET"]).strip()
            value_str = " ".join(entities["VALUE"]).strip().replace("'", "").replace('"', '')

            return {
                "value": value_str if value_str else None,
                "identifier": target_str if target_str else None,
                "element_type": "element"
            }
        except Exception as e:
            logger.error(f"EntityExtractor: Extraction Error: {e}")
            return self._extract_with_rules(step_text)


entity_extractor = EntityExtractor()
