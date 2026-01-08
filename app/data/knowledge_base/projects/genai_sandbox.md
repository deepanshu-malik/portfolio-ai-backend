# GenAI Sandbox - Learning Lab

## Overview
Personal learning project for exploring GenAI/LLM development patterns. Hands-on experiments with OpenAI API, embeddings, and RAG fundamentals.

Repository: https://github.com/deepanshu-malik/genai-sandbox

## Key Learnings

### LLM API Patterns
- Streaming responses for better UX
- Async calls for 5-10x faster batch processing
- Semaphore-based rate limiting for API limits
- Token counting and cost tracking (~$0.000015 per simple call)
- Production patterns: retries, error handling, timeouts

### RAG Fundamentals
- Text embeddings and cosine similarity
- Document chunking strategies:
  - **Simple**: Fixed character count (fast, may break sentences)
  - **Sentence**: Split on boundaries (preserves meaning)
  - **Paragraph**: Semantic units (best for Q&A)
- ChromaDB for vector storage with metadata filtering
- Complete retrieval → augmentation → generation pipeline

### Document Q&A Tool
Built a CLI tool demonstrating:
- Semantic search over documents
- Citation support in responses
- Configurable chunking strategies

## Tech Stack
- Python, OpenAI API (gpt-4o-mini)
- ChromaDB, asyncio

## Why This Matters
These experiments directly informed the architecture of my production RAG system (Portfolio AI Backend), where I applied these patterns at scale with additional features like hybrid search and LLM reranking.
