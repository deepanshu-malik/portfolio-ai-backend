"""Hybrid retriever using LangChain components."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

from app.config import settings
from app.services.langchain.llm import get_embeddings

logger = logging.getLogger(__name__)

INTENT_CONFIG = {
    "quick_answer": {"k": 3, "categories": ["profile", "skills"]},
    "project_deepdive": {"k": 5, "categories": ["projects"]},
    "experience_deepdive": {"k": 5, "categories": ["experience"]},
    "code_walkthrough": {"k": 4, "categories": ["code_snippets", "projects"]},
    "skill_assessment": {"k": 5, "categories": ["skills", "assessments"]},
    "comparison": {"k": 6, "categories": ["projects", "experience", "skills"]},
    "tour": {"k": 4, "categories": ["profile", "skills", "projects", "experience"]},
    "general": {"k": 4, "categories": None},
}


class LangChainHybridRetriever:
    """Hybrid retriever combining vector search and BM25."""

    def __init__(self, vector_weight: float = 0.7):
        self.vector_weight = vector_weight
        self.keyword_weight = 1 - vector_weight
        self.vectorstore: Optional[Chroma] = None
        self.documents: List[Document] = []
        self._initialize()

    def _initialize(self) -> None:
        """Initialize ChromaDB vectorstore."""
        try:
            self.vectorstore = Chroma(
                collection_name=settings.chroma_collection_name,
                embedding_function=get_embeddings(),
                persist_directory=str(Path(settings.chroma_persist_directory)),
            )
            self._load_documents()
            logger.info(f"LangChain HybridRetriever initialized with {len(self.documents)} documents")
        except Exception as e:
            logger.error(f"Failed to initialize retriever: {e}")

    def _load_documents(self) -> None:
        """Load documents from vectorstore for BM25."""
        try:
            result = self.vectorstore._collection.get(include=["documents", "metadatas"])
            self.documents = [
                Document(page_content=doc, metadata=meta or {})
                for doc, meta in zip(result["documents"], result["metadatas"])
            ]
        except Exception as e:
            logger.warning(f"Failed to load documents for BM25: {e}")

    def _merge_results(
        self, vector_docs: List[Document], bm25_docs: List[Document], k: int
    ) -> List[Document]:
        """Merge and deduplicate results using reciprocal rank fusion."""
        scores: Dict[str, float] = {}
        doc_map: Dict[str, Document] = {}
        
        for rank, doc in enumerate(vector_docs):
            key = doc.page_content[:100]
            scores[key] = scores.get(key, 0) + self.vector_weight / (rank + 1)
            doc_map[key] = doc
            
        for rank, doc in enumerate(bm25_docs):
            key = doc.page_content[:100]
            scores[key] = scores.get(key, 0) + self.keyword_weight / (rank + 1)
            doc_map[key] = doc
        
        sorted_keys = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        return [doc_map[k] for k in sorted_keys[:k]]

    async def retrieve(
        self,
        query: str,
        intent: Optional[str] = None,
        k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant documents using hybrid search."""
        if not self.vectorstore:
            return []

        config = INTENT_CONFIG.get(intent, INTENT_CONFIG["general"])
        k = k or config["k"]
        categories = config["categories"]

        try:
            # Vector search
            search_kwargs = {"k": k}
            if categories:
                search_kwargs["filter"] = {"category": {"$in": categories}}
            vector_docs = self.vectorstore.similarity_search(query, **search_kwargs)

            # BM25 search
            docs_for_bm25 = self.documents
            if categories:
                docs_for_bm25 = [d for d in self.documents if d.metadata.get("category") in categories]
            if not docs_for_bm25:
                docs_for_bm25 = self.documents
                
            bm25 = BM25Retriever.from_documents(docs_for_bm25, k=k)
            bm25_docs = bm25.invoke(query)

            # Merge results
            merged = self._merge_results(vector_docs, bm25_docs, k)

            return [
                {"content": doc.page_content, "metadata": doc.metadata, "source": doc.metadata.get("source", "")}
                for doc in merged
            ]
        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Get retriever statistics."""
        if not self.vectorstore:
            return {"status": "not_initialized"}
        try:
            return {
                "status": "connected",
                "document_count": self.vectorstore._collection.count(),
                "bm25_documents": len(self.documents),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
