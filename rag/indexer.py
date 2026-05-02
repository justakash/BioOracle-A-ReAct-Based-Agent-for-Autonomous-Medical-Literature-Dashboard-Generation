"""
FAISS Indexer
Builds and persists a FAISS vector index from document chunks.
Used for the RAG layer to provide contextual grounding.
"""

import os
import pickle
from typing import Optional

import numpy as np
from loguru import logger
from sentence_transformers import SentenceTransformer


class FAISSIndexer:
    """
    Builds and manages a FAISS flat index for semantic document retrieval.
    """

    def __init__(self):
        self.index_path = os.getenv("FAISS_INDEX_PATH", "./data/faiss_index")
        self.model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.model: Optional[SentenceTransformer] = None
        self.index = None
        self.documents: list[dict] = []

    def _load_model(self):
        if self.model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)

    def build(self, documents: list[dict], text_field: str = "text"):
        """
        Build a FAISS index from a list of document dicts.
        Each dict must have at least the text_field key.
        """
        import faiss

        self._load_model()

        texts = [str(doc.get(text_field, "")) for doc in documents]
        logger.info(f"Encoding {len(texts)} documents...")
        embeddings = self.model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        embeddings = np.array(embeddings, dtype=np.float32)

        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embeddings)
        self.documents = documents

        logger.info(f"FAISS index built: {self.index.ntotal} vectors, dim={dim}")

    def save(self):
        """Persist the index and document store to disk."""
        import faiss

        os.makedirs(self.index_path, exist_ok=True)
        faiss.write_index(self.index, os.path.join(self.index_path, "index.faiss"))
        with open(os.path.join(self.index_path, "documents.pkl"), "wb") as f:
            pickle.dump(self.documents, f)
        logger.info(f"FAISS index saved to {self.index_path}")

    def load(self):
        """Load a previously saved FAISS index from disk."""
        import faiss

        index_file = os.path.join(self.index_path, "index.faiss")
        docs_file = os.path.join(self.index_path, "documents.pkl")

        if not os.path.exists(index_file):
            raise FileNotFoundError(f"FAISS index not found at {self.index_path}")

        self.index = faiss.read_index(index_file)
        with open(docs_file, "rb") as f:
            self.documents = pickle.load(f)

        logger.info(f"FAISS index loaded: {self.index.ntotal} vectors")

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Retrieve the top_k most relevant documents for a query.
        Returns list of document dicts with an added 'score' key.
        """
        if self.index is None:
            raise RuntimeError("Index not built or loaded. Call build() or load() first.")

        self._load_model()
        query_vec = self.model.encode([query], normalize_embeddings=True)
        query_vec = np.array(query_vec, dtype=np.float32)

        scores, indices = self.index.search(query_vec, top_k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.documents):
                doc = dict(self.documents[idx])
                doc["score"] = float(score)
                results.append(doc)

        logger.debug(f"RAG search returned {len(results)} results for: {query[:60]}")
        return results
