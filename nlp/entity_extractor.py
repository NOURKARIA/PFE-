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

        try:
            logger.info(f"EntityExtractor: Loading LLM Token Classifier from {model_path}...")
            self.tokenizer = DistilBertTokenizerFast.from_pretrained('distilbert-base-uncased')
            self.model = DistilBertForTokenClassification.from_pretrained('distilbert-base-uncased', num_labels=5)

            if os.path.exists(model_path):
                self.model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
                self.model.eval()
                logger.info("EntityExtractor: LLM Model loaded successfully.")
            else:
                logger.warning(f"EntityExtractor: Model file not found at {model_path}, using rules.")
                self.model = None
        except Exception as e:
            logger.warning(f"EntityExtractor: Falling back to rule-based extraction: {e}")
            self.model = None
            self.tokenizer = None

    def _extract_with_rules(self, step_text: str):
        quoted_values = re.findall(r"['\"]([^'\"]+)['\"]", step_text)
        value = quoted_values[0] if quoted_values else None
        identifier = quoted_values[1] if len(quoted_values) > 1 else None
        lower = step_text.lower()

        if not value:
            url_match = re.search(r"https?://\S+", step_text)
            if url_match:
                value = url_match.group(0).rstrip(".,)")

        if not identifier:
            click_match = re.search(r"(?:click|press|tap|select)(?: on| the)? (.+)", lower)
            if click_match:
                identifier = click_match.group(1).strip()

        if not identifier:
            into_match = re.search(r"(?:into|in|on) the ['\"]?([^'\"]+)['\"]?", lower)
            if into_match:
                identifier = into_match.group(1).strip()

        if not identifier and any(token in lower for token in ["should see", "verify", "expect"]) and quoted_values:
            identifier = quoted_values[-1]

        element_type = "element"
        candidate = identifier or ""
        if "button" in candidate:
            element_type = "button"
        elif any(token in candidate for token in ["field", "input", "username", "email", "password"]):
            element_type = "input"
        elif "header" in candidate:
            element_type = "header"

        return {"value": value, "identifier": identifier, "element_type": element_type}

    def extract_entities(self, step_text: str):
        if not self.model:
            return self._extract_with_rules(step_text)

        try:
            inputs = self.tokenizer(step_text, return_offsets_mapping=True, return_tensors="pt", truncation=True, padding=True)
            offset_mapping = inputs.pop("offset_mapping")[0]

            with torch.no_grad():
                outputs = self.model(**inputs)

            predictions = torch.argmax(outputs.logits, dim=2)[0]
            entities = {"TARGET": [], "VALUE": []}

            for idx, pred_id in enumerate(predictions):
                label = self.id2label[pred_id]
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
