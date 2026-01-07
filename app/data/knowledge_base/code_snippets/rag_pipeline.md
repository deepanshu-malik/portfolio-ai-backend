# Complete RAG Pipeline

## Overview
RAG (Retrieval Augmented Generation) - the pattern that makes LLMs useful for your own data.

## How RAG Works
1. User asks a question
2. Find relevant documents (retrieval via embeddings)
3. Include them in the LLM prompt (augmentation)
4. LLM generates answer using that context (generation)
5. Cite sources for transparency

## Why RAG Over Fine-tuning
- Much cheaper than fine-tuning
- Can update knowledge without retraining
- Provides citations (LLM alone can't do this)
- Production pattern for most GenAI apps

## Implementation

### Document Ingestion
```python
def ingest_documents(self, documents: list[dict]):
    for doc in documents:
        chunks = chunk_document(doc['content'])
        for i, chunk in enumerate(chunks):
            embedding = get_embedding(chunk)
            self.collection.add(
                documents=[chunk],
                embeddings=[embedding],
                metadatas=[{"source": doc['title'], "chunk_id": i}],
                ids=[f"{doc['title']}_{i}"]
            )
```

### Retrieval
```python
def retrieve(self, query: str, k: int = 3) -> list[dict]:
    query_embedding = get_embedding(query)
    results = self.collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"]
    )
    return results
```

### Generation with Context
```python
def generate(self, query: str, context_docs: list[str]) -> str:
    context = "\n\n".join(context_docs)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"Answer based on this context:\n{context}"},
            {"role": "user", "content": query}
        ]
    )
    return response.choices[0].message.content
```

## Architecture Decisions
- ChromaDB: Easy local setup, no external service needed
- text-embedding-3-small: Cost-effective, good quality
- Paragraph chunking: Preserves semantic context for Q&A
- k=3-5: Balance between context and relevance

## GitHub
https://github.com/deepanshu-malik/genai-sandbox/blob/main/rag/04_complete_rag_pipeline.py
