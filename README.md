# Portfolio AI Backend

Production-grade AI-powered portfolio assistant showcasing advanced GenAI/RAG engineering skills.

**✨ Optimized for Koyeb Free Tier** - Includes comprehensive optimizations for deployment on Koyeb's free tier (512MB RAM):
- 🚀 **Cold start < 10s** - Service warming and readiness probes
- 💾 **Memory-safe** - 300-400MB usage with timeout protection
- 💰 **Cost-optimized** - 55-60% reduction in OpenAI costs via caching & token optimization
- ⚡ **Fast responses** - 1-3s (cached), 3-5s (uncached)
- 🛡️ **Production-ready** - Retry logic, graceful degradation, structured logging

[→ Jump to Koyeb Deployment Guide](#koyeb-recommended---free-tier)

---

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
│   ├── main.py                          # FastAPI entry point with optimizations
│   ├── config.py                        # Pydantic settings (with Koyeb optimizations)
│   ├── routers/
│   │   ├── chat_v2.py                   # Advanced chat endpoints + caching
│   │   ├── detail.py                    # Code snippets & comparisons
│   │   └── health.py                    # Health checks + readiness probes
│   ├── services/
│   │   ├── llm_intent_classifier.py     # LLM-based intent classification
│   │   ├── hybrid_retriever.py          # Hybrid search + reranking
│   │   ├── advanced_response_generator.py # Token-managed generation + retries
│   │   ├── token_tracker.py             # Usage & cost tracking
│   │   ├── cache.py                     # Response caching service (NEW)
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
│   │   ├── rate_limit.py                # In-memory rate limiting
│   │   └── timeout.py                   # Request timeout middleware (NEW)
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
├── requirements.txt                     # Dependencies (with tenacity, psutil)
├── Dockerfile                           # Optimized for Koyeb
├── koyeb.yaml                           # Koyeb deployment config (NEW)
├── .env.koyeb.example                   # Koyeb environment template (NEW)
├── KOYEB_OPTIMIZATION_PLAN.md          # Implementation plan (NEW)
├── IMPLEMENTATION_SUMMARY.md            # Complete optimization summary (NEW)
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

#### GET /api/chat/cache/stats
Response cache performance statistics.

**Response:**
```json
{
  "cache_enabled": true,
  "stats": {
    "size": 45,
    "max_size": 100,
    "hits": 120,
    "misses": 280,
    "hit_rate_percent": 30.0,
    "ttl_seconds": 1800,
    "estimated_cost_savings_usd": 0.12
  },
  "message": "Cache is saving ~30.0% of OpenAI API calls"
}
```

#### POST /api/chat/cache/clear
Clear all cached responses (admin only).

**Response:**
```json
{
  "status": "success",
  "message": "Response cache cleared"
}
```

### Detail

#### POST /api/detail
Fetch code snippets, deep dives, or comparisons.

### Health

#### GET /api/health
Basic health check for load balancers and monitoring.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "chromadb": "healthy"
}
```

#### GET /api/health/detailed
Detailed health with feature status, memory usage, and token stats.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production",
  "timestamp": "2026-01-10T12:00:00",
  "checks": {
    "chromadb": {
      "status": "ok",
      "documents": 25,
      "collection": "portfolio"
    },
    "openai": {
      "status": "ok",
      "model": "gpt-4o-mini",
      "embedding_model": "text-embedding-3-small"
    },
    "memory": {
      "status": "ok",
      "rss_mb": 342.5,
      "percent_of_limit": 66.89,
      "limit_mb": 512
    }
  },
  "features": {
    "llm_intent_classification": true,
    "hybrid_retrieval": true,
    "llm_reranking": true,
    "token_tracking": true,
    "streaming": true,
    "request_timeout": true,
    "rate_limiting": true
  },
  "config": {
    "max_concurrent_requests": 3,
    "request_timeout": 30,
    "max_history_length": 5,
    "rate_limit": "5 requests per 60s"
  },
  "token_usage": {...}
}
```

#### GET /api/ping
Lightweight keep-alive endpoint for cron jobs.

**Response:**
```json
{
  "status": "pong",
  "timestamp": "2026-01-10T12:00:00"
}
```

#### GET /api/ready
Readiness probe for Koyeb (returns 503 during startup).

**Response:**
```json
{
  "ready": true,
  "timestamp": "2026-01-10T12:00:00"
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

### Koyeb (Recommended - Free Tier)

**Optimized for Koyeb's free tier (512MB RAM, single instance).**

This application includes comprehensive optimizations for Koyeb's free tier:
- ✅ Cold start < 10 seconds
- ✅ Memory usage: 300-400MB (safe within 512MB limit)
- ✅ Response caching (30-40% cost savings)
- ✅ Request timeout protection (30s)
- ✅ Token optimization (55-60% OpenAI cost reduction)
- ✅ Graceful degradation with retry logic
- ✅ Health checks and readiness probes

#### Prerequisites

1. **GitHub Account** - Code must be in a GitHub repository
2. **Koyeb Account** - Sign up at [https://app.koyeb.com](https://app.koyeb.com) (free)
3. **OpenAI API Key** - Get from [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

#### Step-by-Step Deployment

**1. Prepare Repository**

```bash
# Ensure latest code is pushed
git add .
git commit -m "Ready for Koyeb deployment"
git push origin main
```

**2. Create Koyeb Service**

1. Go to [Koyeb Dashboard](https://app.koyeb.com)
2. Click **"Create Service"** → **"Web Service"**
3. Select **"GitHub"** as source
4. Connect your GitHub account (if not already connected)
5. Select repository: `portfolio-ai-backend`
6. Branch: `main`

**3. Configure Build**

- **Builder**: Docker (auto-detected from Dockerfile)
- **Dockerfile path**: `Dockerfile` (default)
- **Build context**: `.` (root directory)

**4. Set Environment Variables**

Click **"Advanced"** → **"Environment Variables"**:

```bash
# Required
OPENAI_API_KEY=<your-key>  # Set as SECRET (see below)

# Application
APP_ENV=production
DEBUG=false

# Models
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# CORS (update with your frontend domain)
ALLOWED_ORIGINS=https://deepanshu-malik.github.io,http://localhost:3000

# ChromaDB
CHROMA_PERSIST_DIRECTORY=./chromadb
CHROMA_COLLECTION_NAME=portfolio

# Rate Limiting (optimized for free tier)
RATE_LIMIT_REQUESTS=5
RATE_LIMIT_WINDOW=60

# Memory Optimization
MAX_CONCURRENT_REQUESTS=3
REQUEST_TIMEOUT=30
MAX_HISTORY_LENGTH=5

# Caching
CACHE_ENABLED=true
CACHE_TTL=1800
CACHE_MAX_SIZE=100

# Token Optimization
MAX_TOKENS_CONTEXT=2000
MAX_TOKENS_HISTORY=500
MAX_TOKENS_RESPONSE=600
MAX_RETRIEVAL_DOCS=3
```

**5. Create Secret for API Key**

For `OPENAI_API_KEY`:
1. Go to **"Secrets"** in sidebar
2. Click **"Create Secret"**
3. Name: `openai-api-key`
4. Value: Your OpenAI API key
5. Save
6. In environment variables, reference as: `@openai-api-key`

**6. Configure Instance & Health Checks**

- **Instance Type**: `nano` (free tier)
- **Region**: `fra` (Frankfurt) or closest to your users
- **Port**: `8000`
- **Health Check Path**: `/api/health`
- **Health Check Interval**: `60s`
- **Readiness Check Path**: `/api/ready` (optional, recommended)

**7. Deploy**

1. Click **"Deploy"**
2. Monitor build logs (takes 2-3 minutes)
3. Wait for health checks to pass
4. App will be available at: `https://your-app-name.koyeb.app`

#### Post-Deployment Setup

**1. Verify Deployment**

```bash
# Test health endpoint
curl https://your-app.koyeb.app/api/health

# Test chat endpoint
curl -X POST https://your-app.koyeb.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, tell me about your projects",
    "session_id": "test-session"
  }'

# Check detailed health
curl https://your-app.koyeb.app/api/health/detailed
```

**2. Set Up Keep-Alive (Prevent Cold Starts)**

Koyeb free tier may sleep after inactivity. Keep your app warm:

1. Go to [cron-job.org](https://cron-job.org) (free)
2. Create account and verify email
3. Create new cron job:
   - **Title**: Portfolio AI Keep-Alive
   - **URL**: `https://your-app.koyeb.app/api/ping`
   - **Schedule**: Every 14 minutes (*/14 * * * *)
   - **Method**: GET
   - Enable job

**3. Monitor Performance**

```bash
# Check cache statistics
curl https://your-app.koyeb.app/api/chat/cache/stats

# Check token usage
curl https://your-app.koyeb.app/api/chat/stats

# Monitor logs in Koyeb Dashboard
```

#### Using koyeb.yaml (Alternative Method)

Deploy using the included `koyeb.yaml` configuration:

1. Ensure `koyeb.yaml` is in your repository root
2. In Koyeb dashboard, select **"Deploy from koyeb.yaml"**
3. Koyeb will auto-configure based on the file
4. Just set the `OPENAI_API_KEY` secret

#### Troubleshooting

**Memory Issues (>450MB)**
```bash
# Check memory usage
curl https://your-app.koyeb.app/api/health/detailed

# Solutions:
# 1. Reduce MAX_CONCURRENT_REQUESTS to 2
# 2. Reduce CACHE_MAX_SIZE to 50
# 3. Reduce MAX_HISTORY_LENGTH to 3
```

**Slow Responses**
```bash
# Verify keep-alive is working
curl https://your-app.koyeb.app/api/ping

# Check if app is sleeping (cold start indicator)
# Solutions:
# 1. Ensure cron-job.org ping is active
# 2. Increase CACHE_TTL to 3600 (1 hour)
```

**OpenAI Rate Limits**
```bash
# Check token usage
curl https://your-app.koyeb.app/api/chat/stats

# Solutions:
# 1. Increase cache hit rate
# 2. Reduce MAX_TOKENS_CONTEXT further
# 3. Check OpenAI dashboard for quota
```

**ChromaDB Empty**
```bash
# Check logs in Koyeb dashboard for:
# "ChromaDB is empty! Re-running ingestion..."

# The app will auto-reingest if data is missing
# Ensure build logs show successful ingestion
```

#### Monitoring & Maintenance

**Key Metrics to Monitor:**
- Memory usage: Should stay < 450MB
- Response time: 1-3s (cached), 3-5s (uncached)
- Cache hit rate: Target > 30%
- Error rate: Should be < 1%
- Token usage: Monitor daily costs

**Check these endpoints regularly:**
- `/api/health/detailed` - Full system status
- `/api/chat/cache/stats` - Cache performance
- `/api/chat/stats` - Token usage and costs

**Expected Costs on Free Tier:**
- Koyeb: $0/month (free tier)
- OpenAI: $0.10-0.50/month (depends on usage)
- Total: < $1/month 🎉

---

### Docker (Local Development)

```bash
# Build image with API key
docker build -t portfolio-backend \
  --build-arg OPENAI_API_KEY=your_key .

# Run container
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your_key \
  portfolio-backend

# Check health
curl http://localhost:8000/api/health
```

---

### Render / Railway (Alternative)

Similar steps apply for other platforms:
1. Connect GitHub repository
2. Use Dockerfile for build
3. Set environment variables
4. Configure health check: `/api/health`
5. Port: `8000`

Note: Free tiers on these platforms may have different limitations.

## GenAI Skills Demonstrated

### Core GenAI Capabilities
- ✅ **Prompt Engineering** - Intent-specific system prompts, LLM classification
- ✅ **RAG Pipeline** - End-to-end retrieval augmented generation
- ✅ **Hybrid Search** - Combining semantic and keyword search (70/30 split)
- ✅ **Reranking** - LLM-based relevance reordering
- ✅ **Token Management** - Smart context truncation with tiktoken
- ✅ **Cost Tracking** - Per-request and session-level monitoring
- ✅ **Streaming** - Server-Sent Events for real-time UX

### Production Engineering
- ✅ **Response Caching** - 30-40% cost savings with TTL-based cache
- ✅ **Error Handling** - Exponential backoff with tenacity (2 retries)
- ✅ **Graceful Degradation** - User-friendly fallbacks for API failures
- ✅ **Memory Optimization** - Request timeouts, concurrent request limits
- ✅ **Health Monitoring** - ChromaDB status, memory usage, readiness probes
- ✅ **Structured Logging** - Correlation IDs, request tracing, timing metrics
- ✅ **Rate Limiting** - Sliding window rate limiter
- ✅ **Cost Optimization** - 55-60% OpenAI cost reduction through multiple strategies

## Configuration

### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | **Required**. OpenAI API key |
| `OPENAI_MODEL` | gpt-4o-mini | Chat model |
| `OPENAI_EMBEDDING_MODEL` | text-embedding-3-small | Embedding model |
| `APP_ENV` | development | Environment (development/production) |
| `DEBUG` | false | Enable debug mode |

### ChromaDB Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `CHROMA_PERSIST_DIRECTORY` | ./chromadb | Vector database storage path |
| `CHROMA_COLLECTION_NAME` | portfolio | ChromaDB collection name |

### Rate Limiting

| Variable | Default | Description |
|----------|---------|-------------|
| `RATE_LIMIT_REQUESTS` | 10 | Max requests per window |
| `RATE_LIMIT_WINDOW` | 60 | Time window in seconds |

### Memory Optimization (Koyeb Free Tier)

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_CONCURRENT_REQUESTS` | 3 | Max concurrent request processing |
| `REQUEST_TIMEOUT` | 30 | Request timeout in seconds |
| `MAX_HISTORY_LENGTH` | 5 | Conversation history length |

### Response Caching

| Variable | Default | Description |
|----------|---------|-------------|
| `CACHE_ENABLED` | true | Enable/disable response caching |
| `CACHE_TTL` | 1800 | Cache time-to-live (seconds) |
| `CACHE_MAX_SIZE` | 100 | Maximum cached responses |

### Token Optimization

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_TOKENS_CONTEXT` | 2000 | Max context tokens (reduced for cost) |
| `MAX_TOKENS_HISTORY` | 500 | Max history tokens (reduced for cost) |
| `MAX_TOKENS_RESPONSE` | 600 | Max response tokens (reduced for cost) |
| `MAX_RETRIEVAL_DOCS` | 3 | Number of documents to retrieve |

### CORS Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ALLOWED_ORIGINS` | localhost:3000 | Comma-separated list of allowed origins |

---

**Note:** For Koyeb free tier deployment, use the optimized defaults shown above to stay within the 512MB RAM limit and minimize OpenAI costs.

## License

MIT License
