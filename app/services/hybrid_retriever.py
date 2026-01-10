"""Advanced RAG retrieval with hybrid search and reranking."""

import logging
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import chromadb
from chromadb.config import Settings
from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    Advanced RAG retriever with hybrid search and reranking.

    Features:
    - Semantic search (vector similarity)
    - Keyword search (BM25-like)
    - Query expansion/rewriting
    - Relevance threshold filtering
    - LLM-based reranking
    - Consistent OpenAI embeddings
    """

    # Intent-based configuration (optimized for Koyeb free tier - reduced k values)
    INTENT_CONFIG = {
        "quick_answer": {"categories": ["profile", "skills", "projects", "experience"], "k": 3, "threshold": 0.3},
        "project_deepdive": {"categories": ["projects"], "k": 3, "threshold": 0.25},
        "experience_deepdive": {"categories": ["experience"], "k": 3, "threshold": 0.25},
        "code_walkthrough": {"categories": ["code_snippets", "projects"], "k": 3, "threshold": 0.3},
        "skill_assessment": {"categories": ["skills", "assessments"], "k": 3, "threshold": 0.25},
        "comparison": {"categories": ["projects", "experience", "skills"], "k": 4, "threshold": 0.3},
        "tour": {"categories": ["profile", "skills", "projects", "experience"], "k": 3, "threshold": 0.35},
        "general": {"categories": None, "k": 3, "threshold": 0.35},
    }

    def __init__(self):
        """Initialize the hybrid retriever."""
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        self.chroma_client = None
        self.collection = None
        self._initialize_chromadb()

    def _initialize_chromadb(self) -> None:
        """Initialize ChromaDB client."""
        try:
            persist_dir = Path(settings.chroma_persist_directory)
            persist_dir.mkdir(parents=True, exist_ok=True)

            # Try to reuse existing client if available
            try:
                self.chroma_client = chromadb.PersistentClient(
                    path=str(persist_dir),
                    settings=Settings(anonymized_telemetry=False),
                )
            except Exception:
                # Client already exists, use HttpClient or skip
                logger.warning("ChromaDB client already exists, using existing instance")
                self.chroma_client = chromadb.PersistentClient(
                    path=str(persist_dir),
                )

            self.collection = self.chroma_client.get_or_create_collection(
                name=settings.chroma_collection_name,
                metadata={"hnsw:space": "cosine"},
            )

            doc_count = self.collection.count()
            logger.info(f"HybridRetriever initialized with {doc_count} documents")

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")

    def _get_embedding(self, text: str) -> List[float]:
        """Get OpenAI embedding for text."""
        response = self.openai_client.embeddings.create(
            model=settings.openai_embedding_model,
            input=text,
        )
        return response.data[0].embedding

    def _keyword_search(
        self,
        query: str,
        documents: List[Dict],
        top_k: int = 10,
    ) -> List[Tuple[Dict, float]]:
        """
        Simple BM25-like keyword search.
        
        Returns documents with keyword match scores.
        """
        # Tokenize query
        query_terms = set(re.findall(r'\w+', query.lower()))
        
        scored_docs = []
        for doc in documents:
            content = doc.get("content", "").lower()
            doc_terms = re.findall(r'\w+', content)
            term_freq = Counter(doc_terms)
            
            # Calculate simple TF score
            score = sum(term_freq.get(term, 0) for term in query_terms)
            if score > 0:
                # Normalize by document length
                score = score / (len(doc_terms) + 1)
                scored_docs.append((doc, score))
        
        # Sort by score descending
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return scored_docs[:top_k]

    def _rewrite_query(self, query: str, intent: str) -> str:
        """
        Expand/rewrite query for better retrieval.
        
        Adds context based on intent.
        """
        query_lower = query.lower()
        
        # For quick_answer, expand if asking about counts/lists
        if intent == "quick_answer":
            if any(word in query_lower for word in ["how many", "count", "number of", "list"]):
                if "project" in query_lower:
                    return f"{query} projects portfolio work built developed"
                if "experience" in query_lower or "company" in query_lower or "work" in query_lower:
                    return f"{query} experience company role position"
            return query
        
        expansions = {
            "project_deepdive": f"{query} project architecture implementation tech stack",
            "experience_deepdive": f"{query} role responsibilities achievements company",
            "code_walkthrough": f"{query} code implementation example snippet",
            "skill_assessment": f"{query} skills experience proficiency level",
            "general": query,
        }
        return expansions.get(intent, query)

    async def retrieve(
        self,
        query: str,
        intent: Optional[str] = None,
        k: Optional[int] = None,
        use_reranking: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents using hybrid search.

        Args:
            query: Search query
            intent: User intent for filtering
            k: Number of documents to retrieve
            use_reranking: Whether to rerank results

        Returns:
            List of relevant documents with scores
        """
        if not self.collection:
            logger.warning("ChromaDB not initialized")
            return []

        # Get intent configuration
        config = self.INTENT_CONFIG.get(intent, self.INTENT_CONFIG["general"])
        k = k or config["k"]
        threshold = config["threshold"]
        categories = config["categories"]

        # Rewrite query for better retrieval
        expanded_query = self._rewrite_query(query, intent)

        # Build category filter
        where_filter = None
        if categories:
            where_filter = {"category": {"$in": categories}}

        try:
            # Get OpenAI embedding for query (consistent with ingestion)
            query_embedding = self._get_embedding(expanded_query)

            # Semantic search with OpenAI embeddings
            semantic_results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k * 2,  # Get more for filtering
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )

            # Format semantic results
            semantic_docs = []
            if semantic_results and semantic_results.get("documents"):
                for i, doc in enumerate(semantic_results["documents"][0]):
                    distance = semantic_results["distances"][0][i]
                    score = 1 - distance  # Convert distance to similarity
                    
                    semantic_docs.append({
                        "content": doc,
                        "metadata": semantic_results["metadatas"][0][i],
                        "semantic_score": score,
                        "source": "semantic",
                    })

            # Keyword search on semantic results for hybrid scoring
            keyword_results = self._keyword_search(query, semantic_docs, top_k=k * 2)
            keyword_scores = {doc["content"][:100]: score for doc, score in keyword_results}

            # Combine scores (hybrid)
            for doc in semantic_docs:
                keyword_score = keyword_scores.get(doc["content"][:100], 0)
                # Weighted combination: 70% semantic, 30% keyword
                doc["keyword_score"] = keyword_score
                doc["hybrid_score"] = (0.7 * doc["semantic_score"]) + (0.3 * keyword_score * 10)

            # Filter by relevance threshold
            filtered_docs = [
                doc for doc in semantic_docs 
                if doc["semantic_score"] >= threshold
            ]

            # Sort by hybrid score
            filtered_docs.sort(key=lambda x: x["hybrid_score"], reverse=True)

            # Take top k
            final_docs = filtered_docs[:k]

            # Rerank with LLM if enabled and we have results
            if use_reranking and len(final_docs) > 1:
                final_docs = await self._llm_rerank(query, final_docs)

            logger.debug(
                f"Retrieved {len(final_docs)} docs for '{query[:30]}...' "
                f"(intent: {intent}, threshold: {threshold})"
            )

            return final_docs

        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            return []

    async def _llm_rerank(
        self,
        query: str,
        documents: List[Dict],
        top_k: int = 5,
    ) -> List[Dict]:
        """
        Rerank documents using LLM for relevance.
        
        Uses a fast scoring approach.
        """
        if len(documents) <= 1:
            return documents

        try:
            # Create a simple relevance prompt
            doc_summaries = []
            for i, doc in enumerate(documents[:top_k]):
                content_preview = doc["content"][:200].replace("\n", " ")
                doc_summaries.append(f"[{i}] {content_preview}")

            prompt = f"""Rate the relevance of each document to the query. 
Query: "{query}"

Documents:
{chr(10).join(doc_summaries)}

Return ONLY a comma-separated list of document indices ordered by relevance (most relevant first).
Example: 2,0,1,3"""

            from openai import AsyncOpenAI
            async_client = AsyncOpenAI(api_key=settings.openai_api_key)
            
            response = await async_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=50,
            )

            # Parse ranking
            ranking_str = response.choices[0].message.content.strip()
            indices = [int(i.strip()) for i in ranking_str.split(",") if i.strip().isdigit()]

            # Reorder documents
            reranked = []
            for idx in indices:
                if 0 <= idx < len(documents):
                    doc = documents[idx]
                    doc["rerank_position"] = len(reranked)
                    reranked.append(doc)

            # Add any missing documents at the end
            for i, doc in enumerate(documents):
                if i not in indices:
                    doc["rerank_position"] = len(reranked)
                    reranked.append(doc)

            logger.debug(f"Reranked documents: {indices}")
            return reranked[:top_k]

        except Exception as e:
            logger.warning(f"LLM reranking failed: {e}, using original order")
            return documents

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        if not self.collection:
            return {"status": "not_initialized"}

        try:
            return {
                "status": "connected",
                "collection_name": settings.chroma_collection_name,
                "document_count": self.collection.count(),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
