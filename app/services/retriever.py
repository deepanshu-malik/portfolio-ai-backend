"""RAG retrieval service using ChromaDB."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings

from app.config import settings

logger = logging.getLogger(__name__)


class PortfolioRetriever:
    """
    Retrieves relevant documents from ChromaDB for RAG.

    Features:
    - Semantic search using embeddings
    - Metadata filtering by category
    - Intent-based retrieval strategies
    """

    # Intent to collection/filter mapping
    INTENT_FILTERS = {
        "quick_answer": {"categories": ["profile", "skills"]},
        "project_deepdive": {"categories": ["projects"]},
        "experience_deepdive": {"categories": ["experience"]},
        "code_walkthrough": {"categories": ["code_snippets"]},
        "skill_assessment": {"categories": ["skills", "assessments"]},
        "comparison": {"categories": ["projects", "experience", "skills"]},
        "tour": {"categories": ["profile", "skills", "projects", "experience"]},
        "general": {"categories": None},  # Search all
    }

    # Number of documents to retrieve by intent
    INTENT_K_VALUES = {
        "quick_answer": 3,
        "project_deepdive": 5,
        "experience_deepdive": 5,
        "code_walkthrough": 3,
        "skill_assessment": 5,
        "comparison": 6,
        "tour": 4,
        "general": 4,
    }

    def __init__(self):
        """Initialize the retriever with ChromaDB client."""
        self.client = None
        self.collection = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize ChromaDB client and collection."""
        try:
            persist_dir = Path(settings.chroma_persist_directory)
            persist_dir.mkdir(parents=True, exist_ok=True)

            self.client = chromadb.Client(
                Settings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=str(persist_dir),
                    anonymized_telemetry=False,
                )
            )

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=settings.chroma_collection_name,
                metadata={"hnsw:space": "cosine"},
            )

            doc_count = self.collection.count()
            logger.info(
                f"ChromaDB initialized with {doc_count} documents in collection '{settings.chroma_collection_name}'"
            )

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self.client = None
            self.collection = None

    def retrieve(
        self,
        query: str,
        k: Optional[int] = None,
        intent: Optional[str] = None,
        categories: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query.

        Args:
            query: The search query
            k: Number of documents to retrieve
            intent: User intent for filtering
            categories: Explicit category filter

        Returns:
            List of retrieved documents with metadata
        """
        if not self.collection:
            logger.warning("ChromaDB not initialized, returning empty results")
            return []

        # Determine k value
        if k is None:
            k = self.INTENT_K_VALUES.get(intent, 4)

        # Build where filter
        where_filter = None
        if categories:
            where_filter = {"category": {"$in": categories}}
        elif intent and intent in self.INTENT_FILTERS:
            filter_categories = self.INTENT_FILTERS[intent].get("categories")
            if filter_categories:
                where_filter = {"category": {"$in": filter_categories}}

        try:
            # Query ChromaDB
            results = self.collection.query(
                query_texts=[query],
                n_results=k,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )

            # Format results
            documents = []
            if results and results.get("documents"):
                for i, doc in enumerate(results["documents"][0]):
                    metadata = (
                        results["metadatas"][0][i] if results.get("metadatas") else {}
                    )
                    distance = (
                        results["distances"][0][i] if results.get("distances") else None
                    )

                    documents.append(
                        {
                            "content": doc,
                            "metadata": metadata,
                            "score": 1 - distance if distance else None,
                        }
                    )

            logger.debug(f"Retrieved {len(documents)} documents for query: {query[:50]}...")
            return documents

        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            return []

    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
    ) -> None:
        """
        Add documents to the collection.

        Args:
            documents: List of document texts
            metadatas: List of metadata dictionaries
            ids: List of unique document IDs
        """
        if not self.collection:
            raise RuntimeError("ChromaDB not initialized")

        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
            )
            logger.info(f"Added {len(documents)} documents to collection")
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        if not self.collection:
            return {"status": "not_initialized"}

        try:
            count = self.collection.count()
            return {
                "status": "connected",
                "collection_name": settings.chroma_collection_name,
                "document_count": count,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
