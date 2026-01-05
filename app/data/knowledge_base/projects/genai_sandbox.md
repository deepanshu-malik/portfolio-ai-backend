# genai-sandbox Project

## Overview
Personal GenAI learning lab with production-ready implementations.
Repository: https://github.com/deepanshu-malik/genai-sandbox

## Components

### LLM API Basics (Session 1)
- First LLM API call with cost tracking
- Streaming responses for better UX
- Production patterns: error handling, retries, token limits
- Async calls for concurrent processing
- Semaphore-based rate limiting for batch operations

### RAG System (Session 2)
- Text embeddings and cosine similarity
- Document chunking strategies (simple, sentence, paragraph)
- ChromaDB for persistent vector storage with metadata filtering
- Complete RAG pipeline: retrieval + augmented prompts + generation
- Document Q&A CLI tool with semantic search and citations

## Tech Stack
- Python
- OpenAI API (gpt-4o-mini)
- ChromaDB
- asyncio

## Key Learnings
- gpt-4o-mini costs ~$0.000015 per simple call
- Always track tokens and costs
- Production code needs: error handling, retries, token limits
- Streaming improves UX but delays token counts
- Async calls enable 5x-10x faster batch processing

## Architecture Decisions

### Rate Limiting
Used semaphore-based approach because OpenAI free tier has 3 RPM limit.
MAX_CONCURRENT = 2 prevents rate limit errors while maximizing throughput.

### Chunking Strategy
Implemented three strategies:
1. Simple: Fixed character count (fast, may break sentences)
2. Sentence: Split on boundaries (preserves meaning, variable size)
3. Paragraph: Semantic units (best for Q&A, larger chunks)

Chose paragraph chunking for Document Q&A tool because it preserves context better for question answering.

### Vector Database Choice
Selected ChromaDB because:
- Easy local setup (no external service needed)
- Persistent storage
- Metadata filtering support
- Good for learning and prototyping
