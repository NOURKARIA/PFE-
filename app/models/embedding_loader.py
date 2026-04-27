from transformers import AutoModel, AutoTokenizer
import torch
import torch.nn.functional as F
from app.utils.logging_config import logger

class EmbeddingLoader:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        try:
            logger.info(f"EmbeddingLoader: Loading model {model_name}...")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name)
            logger.info("EmbeddingLoader: Model loaded successfully.")
        except Exception as e:
            logger.error(f"EmbeddingLoader: Failed to load embedding model: {e}")
            self.tokenizer = None
            self.model = None

    def get_embedding(self, text: str):
        """Returns the normalized vector embedding for the text."""
        if not self.model or not self.tokenizer:
            return None

        try:
            # Tokenize input
            inputs = self.tokenizer(text, padding=True, truncation=True, return_tensors="pt")
            
            # Compute token embeddings
            with torch.no_grad():
                outputs = self.model(**inputs)
                
            # Perform pooling (mean pooling)
            token_embeddings = outputs.last_hidden_state
            attention_mask = inputs['attention_mask']
            input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
            
            sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
            sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
            embedding = sum_embeddings / sum_mask
            
            # Normalize embeddings
            normalized_embedding = F.normalize(embedding, p=2, dim=1)
            
            return normalized_embedding[0].numpy().tolist()
            
        except Exception as e:
            logger.error(f"EmbeddingLoader: Error computing embedding for '{text}': {e}")
            return None

# Singleton instance for the application
embedding_loader = EmbeddingLoader()
