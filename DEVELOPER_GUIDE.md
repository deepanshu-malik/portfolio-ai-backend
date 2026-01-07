# Developer Guide: Portfolio AI Backend

A comprehensive guide for developers to understand the complete architecture, workflow, and codebase of this production-grade GenAI/RAG application.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Request Flow](#request-flow)
4. [Core Services](#core-services)
5. [Data Flow](#data-flow)
6. [Configuration](#configuration)
7. [API Reference](#api-reference)
8. [Extending the Application](#extending-the-application)

---

## Overview

This is a RAG (Retrieval Augmented Generation) powered chatbot backend that serves as an AI portfolio assistant. It demonstrates production-grade GenAI engineering patterns.

### Key Technologies
- **FastAPI**: Async web framework
- **OpenAI API**: LLM (gpt-4o-mini) and embeddings (text-embedding-3-small)
- **ChromaDB**: Vector database for semantic search
- **tiktoken**: Token counting for context management
- **Pydantic**: Data validation and settings

### GenAI Features Implemented
1. LLM-based intent classification
2. Hybrid retrieval (semantic + keyword search)
3. Query expansion/rewriting
4. LLM reranking
5. Token management
6. Cost tracking
7. Streaming responses
8. Relevance threshold filtering

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           FastAPI Application                        │
├─────────────────────────────────────────────────────────────────────┤
│  Middleware Layer                                                    │
│  ├── RateLimitMiddleware (in-memory, sliding window)                │
│  └── CORSMiddleware (configured origins)                            │
├─────────────────────────────────────────────────────────────────────┤
│  Router Layer                                                        │
│  ├── /api/chat (POST)        → Main chat endpoint                   │
│  ├── /api/chat/stream (POST) → Streaming responses                  │
│  ├── /api/chat/stats (GET)   → Token usage statistics               │
│  ├── /api/detail (POST)      → Code snippets, comparisons           │
│  ├── /api/health (GET)       → Basic health check                   │
│  └── /api/health/detailed    → Detailed status with features        │
├─────────────────────────────────────────────────────────────────────┤
│  Service Layer                                                       │
│  ├── LLMIntentClassifier     → Intent detection using LLM           │
│  ├── HybridRetriever         → Semantic + keyword search            │
│  ├── AdvancedResponseGenerator → Token-managed LLM responses        │
│  ├── TokenTracker            → Usage and cost monitoring            │
│  ├── SessionManager          → Conversation history                 │
│  └── CodeHandler             → Pre-defined code snippets            │
├─────────────────────────────────────────────────────────────────────┤
│  Data Layer                                                          │
│  ├── ChromaDB (Vector Store) → Persistent embeddings                │
│  └── Knowledge Base (Markdown) → Source documents                   │
└─────────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
portfolio-ai-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Pydantic settings
│   │
│   ├── routers/                # API endpoints
│   │   ├── __init__.py
│   │   ├── chat_v2.py          # Advanced chat (main)
│   │   ├── chat.py             # Legacy chat (backup)
│   │   ├── detail.py           # Code snippets endpoint
│   │   └── health.py           # Health checks
│   │
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── llm_intent_classifier.py    # LLM-based classification
│   │   ├── hybrid_retriever.py         # Hybrid search + reranking
│   │   ├── advanced_response_generator.py  # Token-managed generation
│   │   ├── token_tracker.py            # Cost tracking
│   │   ├── session_manager.py          # Conversation state
│   │   ├── code_handler.py             # Code snippets
│   │   ├── intent_classifier.py        # Regex fallback
│   │   ├── retriever.py                # Basic retriever (legacy)
│   │   └── response_generator.py       # Basic generator (legacy)
│   │
│   ├── models/                 # Pydantic models
│   │   ├── __init__.py
│   │   ├── chat.py             # Chat request/response models
│   │   └── responses.py        # Other response models
│   │
│   ├── prompts/                # LLM prompts
│   │   ├── __init__.py
│   │   ├── system_prompts.py   # Intent-specific prompts
│   │   └── templates.py        # Response templates
│   │
│   ├── middleware/             # Custom middleware
│   │   ├── __init__.py
│   │   └── rate_limit.py       # Rate limiting
│   │
│   └── data/
│       └── knowledge_base/     # RAG source documents
│           ├── profile/        # Personal info
│           ├── projects/       # Project descriptions
│           ├── experience/     # Work experience
│           ├── skills/         # Technical skills
│           ├── code_snippets/  # Code examples
│           └── assessments/    # Role fit assessments
│
├── scripts/
│   └── ingest.py               # Document ingestion script
│
├── chromadb/                   # Vector database storage
├── requirements.txt
├── Dockerfile
├── render.yaml                 # Render deployment config
└── README.md
```

---

## Request Flow

### Complete Chat Request Flow

```
1. HTTP Request arrives at /api/chat
         │
         ▼
2. RateLimitMiddleware checks rate limits
   └── If exceeded → 429 Too Many Requests
         │
         ▼
3. Request validation (Pydantic ChatRequest)
   └── message, session_id, context
         │
         ▼
4. SessionManager retrieves conversation history
   └── In-memory storage, 1-hour expiry
         │
         ▼
5. LLMIntentClassifier classifies intent
   ├── Sends prompt to gpt-4o-mini
   ├── Extracts intent from response
   └── Falls back to regex on failure
         │
         ▼
6. HybridRetriever fetches relevant documents
   ├── Query expansion based on intent
   ├── Generate OpenAI embedding for query
   ├── Semantic search in ChromaDB
   ├── Keyword search (BM25-like) on results
   ├── Combine scores (70% semantic, 30% keyword)
   ├── Filter by relevance threshold
   └── LLM reranking for top results
         │
         ▼
7. AdvancedResponseGenerator creates response
   ├── Select intent-specific system prompt
   ├── Prepare context (token-managed)
   ├── Prepare history (token-managed)
   ├── Build messages array
   ├── Call OpenAI API (with retry logic)
   ├── Track token usage
   └── Generate suggestion chips
         │
         ▼
8. SessionManager updates history
         │
         ▼
9. Return ChatResponse
   └── response, suggestions, intent, session_id
```

---

## Core Services

### 1. LLMIntentClassifier (`llm_intent_classifier.py`)

**Purpose**: Classify user messages into predefined intents using LLM.

**Intents**:
- `quick_answer`: Simple factual questions
- `project_deepdive`: Project details
- `experience_deepdive`: Work experience details
- `code_walkthrough`: Code/implementation requests
- `skill_assessment`: Role fit evaluation
- `comparison`: Compare items
- `tour`: Portfolio overview
- `general`: Default/unclear

**How it works**:
```python
# Prompt template
INTENT_CLASSIFICATION_PROMPT = """
Classify the user's message into ONE of these intents:
- quick_answer, project_deepdive, experience_deepdive...

USER MESSAGE: {message}
Respond with ONLY the intent name.
"""

# Classification flow
async def classify(message, context):
    1. Format prompt with message and context
    2. Call gpt-4o-mini (temperature=0, max_tokens=20)
    3. Validate response is a known intent
    4. Fall back to regex classifier on failure
```

**Why LLM over regex?**
- Handles variations: "tell me about projects" vs "what have you built?"
- Context-aware: understands follow-up questions
- More accurate for ambiguous queries

---

### 2. HybridRetriever (`hybrid_retriever.py`)

**Purpose**: Retrieve relevant documents using hybrid search.

**Components**:

#### a) Query Expansion
```python
def _rewrite_query(query, intent):
    expansions = {
        "project_deepdive": f"{query} project architecture tech stack",
        "experience_deepdive": f"{query} role responsibilities achievements",
        ...
    }
```
Adds intent-specific keywords to improve recall.

#### b) Semantic Search
```python
# Uses OpenAI embeddings (same as ingestion)
query_embedding = self._get_embedding(expanded_query)

# ChromaDB vector search
results = self.collection.query(
    query_embeddings=[query_embedding],
    n_results=k * 2,  # Get more for filtering
    where={"category": {"$in": categories}},
)
```

#### c) Keyword Search (BM25-like)
```python
def _keyword_search(query, documents):
    query_terms = set(re.findall(r'\w+', query.lower()))
    for doc in documents:
        # Calculate term frequency score
        score = sum(term_freq.get(term, 0) for term in query_terms)
        score = score / (len(doc_terms) + 1)  # Normalize
```

#### d) Hybrid Scoring
```python
# Combine scores: 70% semantic, 30% keyword
doc["hybrid_score"] = (0.7 * semantic_score) + (0.3 * keyword_score * 10)
```

#### e) Relevance Filtering
```python
# Filter by threshold (varies by intent)
INTENT_CONFIG = {
    "quick_answer": {"threshold": 0.3},
    "project_deepdive": {"threshold": 0.25},
    ...
}
filtered = [doc for doc in docs if doc["semantic_score"] >= threshold]
```

#### f) LLM Reranking
```python
async def _llm_rerank(query, documents):
    prompt = f"""Rate relevance of each document to query.
    Query: "{query}"
    Documents: [0] ..., [1] ..., [2] ...
    Return indices ordered by relevance: 2,0,1"""
    
    # Reorder based on LLM response
```

---

### 3. AdvancedResponseGenerator (`advanced_response_generator.py`)

**Purpose**: Generate responses with token management and streaming.

#### Token Management
```python
# Limits
MAX_CONTEXT_TOKENS = 3000
MAX_HISTORY_TOKENS = 1000
MAX_RESPONSE_TOKENS = 800

# Count tokens using tiktoken
def count_tokens(text):
    return len(self.encoding.encode(text))

# Truncate to fit
def truncate_to_tokens(text, max_tokens):
    tokens = self.encoding.encode(text)[:max_tokens]
    return self.encoding.decode(tokens)
```

#### Context Preparation
```python
def _prepare_context(retrieved_docs, max_tokens=3000):
    # Sort by score (best first)
    # Add documents until token limit reached
    # Truncate last document if needed
```

#### Message Building
```python
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "system", "content": f"Context:\n{context}"},
    # History (user/assistant pairs)
    {"role": "user", "content": query}
]
```

#### Streaming
```python
async def generate_stream(query, intent, docs, history):
    stream = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        stream=True,
    )
    async for chunk in stream:
        yield chunk.choices[0].delta.content
```

---

### 4. TokenTracker (`token_tracker.py`)

**Purpose**: Track token usage and costs.

```python
# Pricing (per 1M tokens)
MODEL_PRICING = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "text-embedding-3-small": {"input": 0.02},
}

# Track each request
def track(prompt_tokens, completion_tokens, model, session_id):
    usage = TokenUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost=(prompt_tokens/1M * input_price) + (completion_tokens/1M * output_price)
    )
    self.usage_log.append(usage)
    self.session_usage[session_id].append(usage)
```

---

### 5. SessionManager (`session_manager.py`)

**Purpose**: Manage conversation state.

```python
# In-memory storage
sessions = {
    "session_123": {
        "history": [
            {"user": "...", "assistant": "...", "intent": "..."},
        ],
        "current_topic": "project_deepdive",
        "created_at": datetime,
        "last_active": datetime,
    }
}

# Auto-cleanup expired sessions (1 hour)
def _cleanup_expired_sessions():
    expired = [sid for sid, s in sessions.items() 
               if now - s["last_active"] > 1 hour]
    for sid in expired:
        del sessions[sid]
```

---

### 6. CodeHandler (`code_handler.py`)

**Purpose**: Serve pre-defined code snippets and comparisons.

```python
CODE_SNIPPETS = {
    "rate_limiting": {
        "title": "Rate Limiting Implementation",
        "language": "python",
        "content": "...",
        "explanation": "...",
        "links": {"github": "..."}
    },
    "rag_pipeline": {...},
    "chunking": {...},
    "async_calls": {...},
}

DEEPDIVE_CONTENT = {
    "rag_architecture": {...},
    "rag_challenges": {...},
}

COMPARISONS = {
    "rag_vs_backend": {...},
    "chunking_strategies": {...},
}
```

---

## Data Flow

### Document Ingestion (`scripts/ingest.py`)

```
1. Load markdown files from knowledge_base/
         │
         ▼
2. Chunk documents (paragraph-based)
   ├── chunk_size: 1000 chars
   └── overlap: 100 chars
         │
         ▼
3. Generate OpenAI embeddings
   └── model: text-embedding-3-small
         │
         ▼
4. Store in ChromaDB
   ├── documents (text)
   ├── embeddings (vectors)
   ├── metadatas (category, source)
   └── ids (unique hash)
```

### Knowledge Base Structure

```
knowledge_base/
├── profile/
│   ├── profile.md          # Basic info, contact
│   └── education.md        # Education background
├── projects/
│   ├── genai_sandbox.md    # GenAI learning project
│   ├── communication_platform.md
│   └── document_dispatch.md
├── experience/
│   ├── kogta.md            # Current role
│   ├── capri.md
│   ├── voereir.md
│   └── tradeindia.md
├── skills/
│   ├── languages.md
│   ├── frameworks.md
│   ├── databases.md
│   ├── devops.md
│   └── genai_skills.md
├── code_snippets/
│   ├── rate_limiting.md
│   ├── async_calls.md
│   ├── chunking.md
│   └── rag_pipeline.md
└── assessments/
    ├── genai_fit.md
    └── backend_fit.md
```

---

## Configuration

### Environment Variables (`app/config.py`)

```python
class Settings(BaseSettings):
    # Application
    app_name: str = "Portfolio AI Backend"
    app_version: str = "1.0.0"
    app_env: str = "development"
    debug: bool = False

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    # CORS
    allowed_origins: str = "http://localhost:3000,https://deepanshu-malik.github.io"

    # ChromaDB
    chroma_persist_directory: str = "./chromadb"
    chroma_collection_name: str = "portfolio"

    # Rate Limiting
    rate_limit_requests: int = 10
    rate_limit_window: int = 60
```

### Intent Configuration (`hybrid_retriever.py`)

```python
INTENT_CONFIG = {
    "quick_answer": {
        "categories": ["profile", "skills"],
        "k": 3,              # Documents to retrieve
        "threshold": 0.3     # Minimum similarity score
    },
    "project_deepdive": {
        "categories": ["projects"],
        "k": 5,
        "threshold": 0.25
    },
    # ... more intents
}
```

---

## API Reference

### POST /api/chat

**Request**:
```json
{
  "message": "string (required, 1-1000 chars)",
  "session_id": "string (required)",
  "context": {
    "current_section": "string (optional)",
    "previous_topic": "string (optional)"
  }
}
```

**Response**:
```json
{
  "response": "string",
  "suggestions": [
    {"label": "string", "action": "code|deepdive|compare", "target": "string"}
  ],
  "detail_panel": null,
  "intent": "string",
  "session_id": "string"
}
```

### POST /api/chat/stream

Same request as `/api/chat`. Returns Server-Sent Events:
```
data: chunk1

data: chunk2

data: [DONE]
```

### GET /api/chat/stats

**Response**:
```json
{
  "total_tokens": 15420,
  "prompt_tokens": 12000,
  "completion_tokens": 3420,
  "total_cost": 0.0045,
  "request_count": 12,
  "by_type": {
    "chat": {"tokens": 14000, "cost": 0.004, "count": 10}
  }
}
```

### POST /api/detail

**Request**:
```json
{
  "action": "code|deepdive|compare",
  "target": "rate_limiting|rag_pipeline|...",
  "session_id": "string"
}
```

### GET /api/health/detailed

**Response**:
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

---

## Extending the Application

### Adding a New Intent

1. **Update LLM classifier prompt** (`llm_intent_classifier.py`):
```python
INTENTS = [..., "new_intent"]
# Update INTENT_CLASSIFICATION_PROMPT
```

2. **Add retrieval config** (`hybrid_retriever.py`):
```python
INTENT_CONFIG["new_intent"] = {
    "categories": ["relevant_category"],
    "k": 4,
    "threshold": 0.3
}
```

3. **Add system prompt** (`system_prompts.py`):
```python
INTENT_PROMPTS["new_intent"] = f"""{BASE_PERSONA}
For this response:
- Specific instructions...
"""
```

4. **Add suggestions** (`templates.py`):
```python
SUGGESTION_TEMPLATES["new_intent"] = [
    {"label": "...", "action": "...", "target": "..."}
]
```

### Adding Knowledge Base Content

1. Create markdown file in appropriate category folder
2. Run ingestion: `python scripts/ingest.py`
3. Verify: Check `/api/health/detailed` for document count

### Adding a New Code Snippet

Update `code_handler.py`:
```python
CODE_SNIPPETS["new_snippet"] = {
    "title": "...",
    "language": "python",
    "content": "...",
    "explanation": "...",
    "links": {"github": "..."}
}
```

---

## Error Handling

### Retry Logic
```python
MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]  # Exponential backoff

for attempt in range(MAX_RETRIES):
    try:
        response = await client.chat.completions.create(...)
        return response
    except (RateLimitError, APIError, APIConnectionError):
        await asyncio.sleep(RETRY_DELAYS[attempt])
```

### Fallback Chain
```
LLM Intent Classification
    └── fails → Regex Intent Classification
    
HybridRetriever
    └── fails → Return empty results (graceful degradation)
    
Response Generation
    └── fails → Return error message to user
```

---

## Performance Considerations

1. **Token Management**: Prevents context overflow, reduces costs
2. **Relevance Filtering**: Removes low-quality matches before LLM
3. **Reranking**: Only on top candidates (not all results)
4. **Streaming**: Better perceived latency for users
5. **In-memory Sessions**: Fast access, auto-cleanup
6. **Compiled Regex**: Pre-compiled patterns for fallback classifier

---

## Testing Locally

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add OPENAI_API_KEY to .env

# Ingest documents
python scripts/ingest.py

# Run server
uvicorn app.main:app --reload

# Test endpoints
curl http://localhost:8000/api/health/detailed
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about your projects", "session_id": "test"}'
```
