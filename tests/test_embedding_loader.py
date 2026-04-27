import pytest
from unittest.mock import patch, MagicMock
from app.models.embedding_loader import EmbeddingLoader

@pytest.fixture
def embedding_mock():
    with patch("app.models.embedding_loader.AutoTokenizer") as mock_tokenizer_cls, \
         patch("app.models.embedding_loader.AutoModel") as mock_model_cls:
        
        mock_tokenizer = MagicMock()
        mock_tokenizer.return_value = {
            "attention_mask": MagicMock(),
            "input_ids": MagicMock()
        }
        
        mock_model = MagicMock()
        mock_outputs = MagicMock()
        mock_outputs.last_hidden_state = MagicMock()
        mock_model.return_value = mock_outputs
        
        mock_tokenizer_cls.from_pretrained.return_value = mock_tokenizer
        mock_model_cls.from_pretrained.return_value = mock_model
        
        loader = EmbeddingLoader(model_name="fake_model")
        return loader

@patch("app.models.embedding_loader.torch")
@patch("app.models.embedding_loader.F")
def test_get_embedding_success(mock_f, mock_torch, embedding_mock):
    # Mocking torch functions to just return a dummy list
    mock_f.normalize.return_value = MagicMock()
    mock_f.normalize.return_value[0].numpy.return_value.tolist.return_value = [0.1, 0.2, 0.3]
    
    result = embedding_mock.get_embedding("test text")
    assert result == [0.1, 0.2, 0.3]

def test_get_embedding_no_model():
    with patch("app.models.embedding_loader.AutoTokenizer.from_pretrained", side_effect=Exception("Error")):
        loader = EmbeddingLoader()
        assert loader.model is None
        assert loader.get_embedding("test") is None

def test_get_embedding_prediction_error(embedding_mock):
    embedding_mock.tokenizer.side_effect = Exception("Tokenize error")
    result = embedding_mock.get_embedding("test")
    assert result is None
