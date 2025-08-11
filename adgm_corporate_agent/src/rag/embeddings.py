from __future__ import annotations
from typing import List

from sentence_transformers import SentenceTransformer

from src.config import AppConfig


class EmbeddingsModel:
    def __init__(self, config: AppConfig):
        self.config = config
        if config.embeddings_provider == "hf":
            self.model = SentenceTransformer(config.embeddings_model)
            self.dim = self.model.get_sentence_embedding_dimension()
        else:
            # Fallback to HF for this POC
            self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            self.dim = self.model.get_sentence_embedding_dimension()

    def embed(self, texts: List[str]) -> List[List[float]]:
        return [vec.tolist() for vec in self.model.encode(texts, convert_to_tensor=True)]


