# Portfolio AI Backend

Production-grade AI-powered portfolio assistant showcasing advanced GenAI/RAG engineering skills.

## 🚀 GenAI Features

| Feature | Description |
|---------|-------------|
| **LLM Intent Classification** | Uses gpt-4o-mini for accurate intent understanding (8 intents) |
| **Hybrid Retrieval** | Combines semantic search + keyword matching (BM25-like) |
| **Query Expansion** | Intent-aware query rewriting for better recall |
| **LLM Reranking** | Reorders retrieved docs by relevance using LLM |
| **Token Management** | Smart context truncation with tiktoken |
| **Cost Tracking** | Per-request and session token/cost monitoring |
| **Streaming Responses** | Server-Sent Events for real-time UX |
| **Relevance Filtering** | Threshold-based filtering to remove low-quality matches |

## Architecture

```
User Query
    │
    ▼
┌─────────────────────────────────────┐
│  LLM Intent Classification          │ ← gpt-4o-mini
│  (context-aware, fallback to regex) │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  Hybrid Retrieval                   │
│  ├─ Query expansion by intent       │
│  ├─ OpenAI embeddings               │
│  ├─ Semantic search (ChromaDB)      │
│  ├─ Keyword search (BM25-like)      │
│  └─ Relevance threshold filtering   │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  LLM Reranking                      │ ← gpt-4o-mini
│  (reorders by query relevance)      │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  Response Generation                │ ← gpt-4o-mini
│  ├─ Token-managed context           │
│  ├─ Intent-specific prompts         │
│  ├─ Conversation history            │
│  └─ Streaming support               │
└─────────────────────────────────────┘
    │
    ▼
Response + Suggestions + Token Stats
```

## Tech Stack

- **Framework**: FastAPI (async)
- **LLM**: OpenAI API (gpt-4o-mini)
- **Embeddings**: text-embedding-3-small
- **Vector Database**: ChromaDB (persistent)
- **Token Counting**: tiktoken
- **Language**: Python 3.11+

## Project Structure

```
portfolio-ai-backend/
├── app/
│   ├── main.py                          # FastAPI entry point
│   ├── config.py                        # Pydantic settings
│   ├── routers/
│   │   ├── chat_v2.py                   # Advanced chat endpoints
│   │   ├── detail.py                    # Code snippets & comparisons
│   │   └── health.py                    # Health checks with stats
│   ├── services/
│   │   ├── llm_intent_classifier.py     # LLM-based intent classification
│   │   ├── hybrid_retriever.py          # Hybrid search + reranking
│   │   ├── advanced_response_generator.py # Token-managed generation
│   │   ├── token_tracker.py             # Usage & cost tracking
│   │   ├── intent_classifier.py         # Regex fallback classifier
│   │   ├── retriever.py                 # Basic retriever (legacy)
│   │   ├── response_generator.py        # Basic generator (legacy)
│   │   ├── code_handler.py              # Code snippets handler
│   │   └── session_manager.py           # Conversation sessions
│   ├── prompts/
│   │   ├── system_prompts.py            # Intent-specific prompts
│   │   └── templates.py                 # Response templates
│   ├── models/                          # Pydantic models
│   ├── middleware/
│   │   └── rate_limit.py                # In-memory rate limiting
│   └── data/
│       └── knowledge_base/              # RAG source documents
│           ├── profile/
│           ├── projects/
│           ├── experience/
│           ├── skills/
│           ├── code_snippets/
│           └── assessments/
├── scripts/
│   └── ingest.py                        # Document ingestion to ChromaDB
├── chromadb/                            # Vector database storage
├── requirements.txt
├── Dockerfile
└── README.md
```

## API Endpoints

### Chat

#### POST /api/chat
Main chat endpoint with full GenAI pipeline.

**Request:**
```json
{
  "message": "Tell me about your RAG experience",
  "session_id": "session_123",
  "context": {
    "current_section": "projects",
    "previous_topic": null
  }
}
```

**Response:**
```json
{
  "response": "I've built a production-ready RAG pipeline...",
  "suggestions": [
    {"label": "Show RAG Code", "action": "code", "target": "rag_pipeline"}
  ],
  "intent": "project_deepdive",
  "session_id": "session_123"
}
```

#### POST /api/chat/stream
Streaming chat responses (Server-Sent Events).

#### GET /api/chat/stats
Token usage and cost statistics.

**Response:**
```json
{
  "total_tokens": 15420,
  "prompt_tokens": 12000,
  "completion_tokens": 3420,
  "total_cost": 0.0045,
  "request_count": 12,
  "by_type": {
    "chat": {"tokens": 14000, "cost": 0.004, "count": 10},
    "intent": {"tokens": 1420, "cost": 0.0005, "count": 10}
  }
}
```

### Detail

#### POST /api/detail
Fetch code snippets, deep dives, or comparisons.

### Health

#### GET /api/health
Basic health check.

#### GET /api/health/detailed
Detailed health with feature status and token stats.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "features": {
    "llm_intent_classification": true,
    "hybrid_retrieval": true,
    "llm_reranking": true,
    "token_tracking": true,
    "streaming": true
  },
  "models": {
    "chat": "gpt-4o-mini",
    "embedding": "text-embedding-3-small"
  },
  "chromadb": {
    "status": "connected",
    "document_count": 25
  },
  "token_usage": {...}
}
```

## Setup

### Prerequisites
- Python 3.11+
- OpenAI API key

### Installation

```bash
# Clone repository
git clone https://github.com/deepanshu-malik/portfolio-ai-backend.git
cd portfolio-ai-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env and add OPENAI_API_KEY

# Ingest documents to ChromaDB
python scripts/ingest.py

# Run server
uvicorn app.main:app --reload
```

API available at `http://localhost:8000`

## Deployment

### Koyeb (Recommended - Always On)

1. Push code to GitHub
2. Connect repository in Koyeb
3. Select **Dockerfile** build
4. Set environment variable: `OPENAI_API_KEY`
5. Port: `8000`

### Docker

```bash
docker build -t portfolio-backend .
docker run -p 8000:8000 -e OPENAI_API_KEY=your_key portfolio-backend
```

## GenAI Skills Demonstrated

- ✅ **Prompt Engineering** - Intent-specific system prompts, LLM classification
- ✅ **RAG Pipeline** - End-to-end retrieval augmented generation
- ✅ **Hybrid Search** - Combining semantic and keyword search
- ✅ **Reranking** - LLM-based relevance reordering
- ✅ **Token Management** - Context window optimization with tiktoken
- ✅ **Cost Tracking** - Production-ready usage monitoring
- ✅ **Streaming** - Real-time response generation
- ✅ **Error Handling** - Retries, fallbacks, graceful degradation

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | Required. OpenAI API key |
| `OPENAI_MODEL` | gpt-4o-mini | Chat model |
| `OPENAI_EMBEDDING_MODEL` | text-embedding-3-small | Embedding model |
| `CHROMA_PERSIST_DIRECTORY` | ./chromadb | Vector DB path |
| `RATE_LIMIT_REQUESTS` | 10 | Requests per window |
| `RATE_LIMIT_WINDOW` | 60 | Window in seconds |
| `DEBUG` | false | Enable debug mode |

## License

MIT License
