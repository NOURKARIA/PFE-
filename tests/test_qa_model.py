import pytest
from unittest.mock import patch, MagicMock
from app.models.qa_model import QAModel

@pytest.fixture
def qa_model_mock():
    with patch("app.models.qa_model.pipeline") as mock_pipeline:
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.return_value = {"answer": "success message", "score": 0.95}
        mock_pipeline.return_value = mock_pipeline_instance
        model = QAModel(model_name="fake_model")
        return model, mock_pipeline_instance

def test_qa_model_init(qa_model_mock):
    model, _ = qa_model_mock
    assert model.qa_pipeline is not None

def test_qa_model_answer_question_success(qa_model_mock):
    model, mock_pipeline_instance = qa_model_mock
    result = model.answer_question("What is the message?", "The success message is shown")
    
    mock_pipeline_instance.assert_called_once_with(
        question="What is the message?", 
        context="The success message is shown"
    )
    assert result["answer"] == "success message"
    assert result["score"] == 0.95

def test_qa_model_answer_question_no_pipeline():
    with patch("app.models.qa_model.pipeline", side_effect=Exception("Failed to load")):
        model = QAModel()
        assert model.qa_pipeline is None
        
        result = model.answer_question("Q", "Ctx")
        assert result["answer"] == ""
        assert result["score"] == 0.0

def test_qa_model_answer_question_prediction_error(qa_model_mock):
    model, mock_pipeline_instance = qa_model_mock
    mock_pipeline_instance.side_effect = Exception("Prediction error")
    
    result = model.answer_question("Q", "Ctx")
    assert result["answer"] == ""
    assert result["score"] == 0.0
