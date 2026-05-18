import os
import re

import torch
from transformers import DistilBertForSequenceClassification, DistilBertTokenizer

from app.utils.logging_config import logger


class IntentClassifier:
    def __init__(self, model_path='trained_models/nlp/intention_classifier.pt'):
        self.model = None
        self.tokenizer = None
        self.label_map = {0: "ACTION_CLICK", 1: "ACTION_TYPE", 2: "NAVIGATION", 3: "VERIFICATION"}

        if os.getenv("DISABLE_NLP_MODELS", "").lower() in {"1", "true", "yes"}:
            logger.info("IntentClassifier: DISABLE_NLP_MODELS is enabled, using rule-based classification.")
            return

        try:
            logger.info(f"IntentClassifier: Loading Custom PyTorch model from {model_path}...")
            self.tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')

            # Prefer loading a transformers save_pretrained directory if present
            if os.path.isdir(model_path):
                logger.info(f"IntentClassifier: Loading pretrained model directory from {model_path}...")
                self.model = DistilBertForSequenceClassification.from_pretrained(model_path)
                self.model.eval()
                logger.info("IntentClassifier: Loaded model from directory.")
            else:
                self.model = DistilBertForSequenceClassification.from_pretrained('distilbert-base-uncased', num_labels=4)
                if os.path.exists(model_path):
                    self.model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
                    self.model.eval()
                    logger.info("IntentClassifier: Custom Model loaded successfully from state_dict.")
                else:
                    logger.warning(f"IntentClassifier: Model file not found at {model_path}, using rules.")
                    self.model = None
        except Exception as e:
            logger.warning(f"IntentClassifier: Falling back to rule-based classification: {e}")
            self.model = None
            self.tokenizer = None

    def _predict_with_rules(self, step_text: str) -> str:
        text = step_text.lower().strip()
        if any(token in text for token in ["navigate", "go to", "open ", "visit "]) or re.search(r"https?://", text):
            return "NAVIGATION"
        if any(token in text for token in ["type ", "enter ", "fill ", "write "]):
            return "ACTION_TYPE"
        if any(token in text for token in ["click", "press", "tap", "select"]):
            return "ACTION_CLICK"
        if any(token in text for token in ["should see", "verify", "assert", "expect", "should be"]):
            return "VERIFICATION"
        return "UNKNOWN"

    def predict_intent(self, step_text: str):
        if not self.model:
            return self._predict_with_rules(step_text)

        try:
            inputs = self.tokenizer(step_text, return_tensors="pt", truncation=True, padding=True, max_length=128)
            with torch.no_grad():
                outputs = self.model(**inputs)

            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            score, predicted_idx = torch.max(probs, dim=1)
            predicted_label = self.label_map.get(predicted_idx.item(), "UNKNOWN")

            if score.item() > 0.5:
                return predicted_label
            return self._predict_with_rules(step_text)
        except Exception as e:
            logger.error(f"IntentClassifier Prediction Error: {e}")
            return self._predict_with_rules(step_text)


intent_classifier = IntentClassifier()
