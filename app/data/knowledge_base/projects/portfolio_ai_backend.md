# Portfolio AI Backend - Production RAG System

## Overview
Production-grade RAG (Retrieval Augmented Generation) chatbot that serves as an AI portfolio assistant. Demonstrates advanced GenAI engineering patterns with a complete pipeline from intent classification to streaming responses.

Repository: https://github.com/deepanshu-malik/portfolio-ai-backend

## Live Demo
The system powers an interactive portfolio where visitors can ask questions about my experience, projects, and skills - and get contextual, accurate responses.

## GenAI Features

| Feature | Implementation |
|---------|----------------|
| **LLM Intent Classification** | gpt-4o-mini classifies queries into 8 intents with regex fallback |
| **Hybrid Retrieval** | 70% semantic (ChromaDB) + 30% keyword (BM25-like) scoring |
| **Query Expansion** | Intent-aware query rewriting for better recall |
| **LLM Reranking** | Reorders retrieved docs by relevance using LLM |
| **Token Management** | tiktoken for context truncation (3000 ctx, 1000 history, 800 response) |
| **Cost Tracking** | Per-request and session token/cost monitoring |
| **Streaming** | Server-Sent Events for real-time response generation |
| **Relevance Filtering** | Threshold-based filtering removes low-quality matches |

## Architecture

```
User Query
    │
    ▼
┌─────────────────────────────────────┐
│  LLM Intent Classification          │ ← gpt-4o-mini (8 intents)
│  (with regex fallback)              │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  Hybrid Retrieval                   │
│  ├─ Query expansion by intent       │
│  ├─ Semantic search (ChromaDB)      │
│  ├─ Keyword search (BM25-like)      │
│  └─ Relevance threshold filtering   │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  LLM Reranking                      │ ← Reorders by query relevance
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  Response Generation                │
│  ├─ Token-managed context           │
│  ├─ Intent-specific system prompts  │
│  ├─ Conversation history            │
│  └─ Streaming support (SSE)         │
└─────────────────────────────────────┘
    │
    ▼
Response + Suggestions + Token Stats
```

## Tech Stack
- **Framework**: FastAPI (async)
- **LLM**: OpenAI API (gpt-4o-mini)
- **Embeddings**: text-embedding-3-small
- **Vector DB**: ChromaDB (persistent)
- **Token Counting**: tiktoken

## Key Components

### Intent Classification
8 intents for routing queries appropriately:
- `quick_answer`: Simple factual questions
- `project_deepdive`: Project details
- `experience_deepdive`: Work experience
- `code_walkthrough`: Implementation details
- `skill_assessment`: Role fit evaluation
- `comparison`: Compare items
- `tour`: Portfolio overview
- `general`: Default/unclear

### Hybrid Search
Combines two retrieval methods:
```
hybrid_score = (0.7 × semantic_score) + (0.3 × keyword_score)
```
- Semantic search captures meaning
- Keyword search catches exact matches
- Combined scoring improves recall

### Token Management
Prevents context overflow and controls costs:
- Counts tokens with tiktoken before API calls
- Truncates context to fit limits
- Prioritizes higher-scored documents
- Tracks usage per session

### Streaming Responses
Server-Sent Events for real-time UX:
- Chunks streamed as generated
- Better perceived latency
- Token tracking for streamed responses

## API Endpoints
- `POST /api/chat` - Main chat with full pipeline
- `POST /api/chat/stream` - SSE streaming responses
- `GET /api/chat/stats` - Token usage statistics
- `GET /api/health/detailed` - Feature status and metrics

## Production Patterns

### Graceful Degradation
- LLM intent fails → regex fallback
- Retrieval fails → empty context (still generates response)
- Reranking fails → original order preserved

### Retry Logic
```python
MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]  # Exponential backoff
```

### Cost Optimization
- gpt-4o-mini for all LLM calls (cost-effective)
- Token limits prevent runaway costs
- Per-session tracking for monitoring

## My Contributions
- Designed and implemented complete RAG architecture
- Built hybrid retrieval with semantic + keyword search
- Implemented LLM-based intent classification and reranking
- Created token management system with tiktoken
- Added streaming support with SSE
- Built cost tracking and monitoring
- Deployed with Docker on cloud platform

## Skills Demonstrated
- **RAG Pipeline**: End-to-end retrieval augmented generation
- **Prompt Engineering**: Intent-specific system prompts
- **Hybrid Search**: Combining semantic and keyword retrieval
- **LLM Integration**: Classification, reranking, generation
- **Token Management**: Context window optimization
- **Streaming**: Real-time response generation
- **Production Patterns**: Retries, fallbacks, monitoring
