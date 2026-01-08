# Hybrid Search Pattern (RAG)

## Overview
Combining semantic search with keyword search for better retrieval in RAG systems. Neither method alone is perfect - hybrid scoring gets the best of both.

## Problem Solved
- **Semantic search** misses exact keyword matches
- **Keyword search** misses semantic meaning
- Hybrid approach improves recall and precision

## Implementation
```python
import re
from collections import Counter
from typing import List, Dict

class HybridRetriever:
    def __init__(self, collection, embedding_client):
        self.collection = collection
        self.embedding_client = embedding_client
    
    async def retrieve(self, query: str, k: int = 5) -> List[Dict]:
        # 1. Semantic search
        query_embedding = self._get_embedding(query)
        semantic_results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k * 2,  # Get more for filtering
        )
        
        # 2. Keyword search on semantic results
        keyword_scores = self._keyword_search(query, semantic_results)
        
        # 3. Combine scores
        for doc in semantic_results:
            semantic_score = 1 - doc["distance"]  # Convert distance to similarity
            keyword_score = keyword_scores.get(doc["id"], 0)
            
            # Weighted combination: 70% semantic, 30% keyword
            doc["hybrid_score"] = (0.7 * semantic_score) + (0.3 * keyword_score)
        
        # 4. Sort by hybrid score and return top k
        return sorted(semantic_results, key=lambda x: x["hybrid_score"], reverse=True)[:k]
    
    def _keyword_search(self, query: str, documents: List[Dict]) -> Dict[str, float]:
        """BM25-like keyword scoring"""
        query_terms = set(re.findall(r'\w+', query.lower()))
        scores = {}
        
        for doc in documents:
            content = doc["content"].lower()
            doc_terms = re.findall(r'\w+', content)
            term_freq = Counter(doc_terms)
            
            # Simple TF score normalized by doc length
            score = sum(term_freq.get(term, 0) for term in query_terms)
            scores[doc["id"]] = score / (len(doc_terms) + 1)
        
        return scores
```

## Why 70/30 Split?
- Semantic search is generally more accurate for meaning
- Keyword search catches exact matches semantic might miss
- Tuned based on testing with real queries

## Enhancements
- **Query Expansion**: Add intent-specific keywords before search
- **Relevance Threshold**: Filter low-scoring results
- **LLM Reranking**: Use LLM to reorder top results

## Results
Hybrid search improved retrieval quality in my portfolio RAG system, especially for queries mixing technical terms with natural language.
