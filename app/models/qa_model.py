from transformers import pipeline
from app.utils.logging_config import logger

class QAModel:
    def __init__(self, model_name="deepset/roberta-base-squad2"):
        """
        Initializes the Extractive QA model.
        Used for verification steps: e.g., 'Is there a success message?' given the screen text.
        """
        try:
            logger.info(f"QAModel: Loading HuggingFace QA model ({model_name})...")
            # Using the pipeline for question-answering
            self.qa_pipeline = pipeline("question-answering", model=model_name, tokenizer=model_name)
            logger.info("QAModel: Model loaded successfully.")
        except Exception as e:
            logger.error(f"QAModel: Failed to load QA model: {e}")
            self.qa_pipeline = None

    def answer_question(self, question: str, context: str):
        """
        Answers a question based on the provided context (e.g., extracted OCR text).
        """
        if not self.qa_pipeline:
            return {"answer": "", "score": 0.0}

        try:
            result = self.qa_pipeline(question=question, context=context)
            logger.info(f"QAModel: Answered '{question}' with score {result.get('score', 0):.2f}")
            return {
                "answer": result.get("answer", ""),
                "score": result.get("score", 0.0)
            }
        except Exception as e:
            logger.error(f"QAModel: Prediction error: {e}")
            return {"answer": "", "score": 0.0}

# Singleton instance
qa_model = QAModel()
