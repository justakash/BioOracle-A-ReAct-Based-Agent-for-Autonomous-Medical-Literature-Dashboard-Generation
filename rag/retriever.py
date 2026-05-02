"""
RAG Retriever
Merges FAISS vector search results with structured API data
before handing context to the LLM agent.
"""

from typing import Optional

from loguru import logger

from rag.indexer import FAISSIndexer


class RAGRetriever:
    """
    Retrieves relevant context documents and merges them with
    structured biomedical data for the agent's context window.
    """

    def __init__(self):
        self.indexer = FAISSIndexer()
        self._index_loaded = False

    def _ensure_index(self):
        if not self._index_loaded:
            try:
                self.indexer.load()
                self._index_loaded = True
            except FileNotFoundError:
                logger.warning("FAISS index not found. RAG layer will be skipped.")

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Retrieve top_k relevant context documents for a query.
        Returns empty list if no index is available.
        """
        self._ensure_index()
        if not self._index_loaded:
            return []
        return self.indexer.search(query, top_k=top_k)

    def build_context_string(self, query: str, top_k: int = 5) -> str:
        """
        Build a formatted context string from retrieved documents.
        Suitable for injection into the agent's system prompt.
        """
        docs = self.retrieve(query, top_k=top_k)
        if not docs:
            return ""

        lines = ["--- Relevant Background Context (from RAG) ---"]
        for i, doc in enumerate(docs, 1):
            text = doc.get("text", "")
            source = doc.get("source", "unknown")
            score = doc.get("score", 0.0)
            lines.append(f"[{i}] (source: {source}, relevance: {score:.3f})")
            lines.append(text[:500])
            lines.append("")

        lines.append("--- End of Background Context ---")
        return "\n".join(lines)

    def index_documents(self, documents: list[dict], text_field: str = "text"):
        """
        Build a new FAISS index from a list of documents and save it.
        """
        self.indexer.build(documents, text_field=text_field)
        self.indexer.save()
        self._index_loaded = True
        logger.info(f"RAG index built and saved: {len(documents)} documents")
