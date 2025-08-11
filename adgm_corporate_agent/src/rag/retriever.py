from __future__ import annotations
from typing import List, Dict, Any

import chromadb

from src.config import AppConfig
from src.rag.embeddings import EmbeddingsModel


class RAGRetriever:
    def __init__(self, config: AppConfig):
        self.config = config
        self.client = chromadb.PersistentClient(path=config.vectorstore_dir)
        self.collection = self.client.get_or_create_collection("adgm_reference")
        self.emb_model = EmbeddingsModel(config)

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        query_emb = self.emb_model.embed([query])[0]
        res = self.collection.query(query_embeddings=[query_emb], n_results=top_k)
        results: List[Dict[str, Any]] = []
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        for doc, meta in zip(docs, metas):
            results.append({
                "snippet": doc[:300],
                "source": (meta or {}).get("source"),
            })
        return results


