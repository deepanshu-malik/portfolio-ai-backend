# Portfolio AI Backend

AI-powered portfolio assistant with RAG capabilities for Deepanshu Malik's portfolio website.

## Features

- **RAG-powered Chat**: Answers questions about experience, projects, and skills using retrieval-augmented generation
- **Intent Classification**: Understands user intent (quick answer, deep dive, code walkthrough, etc.)
- **Code Snippets**: Returns syntax-highlighted code examples from projects
- **Session Management**: Maintains conversation context across multiple exchanges

## Tech Stack

- **Framework**: FastAPI
- **LLM**: OpenAI API (gpt-4o-mini)
- **Vector Database**: ChromaDB
- **Language**: Python 3.11+

## Project Structure

```
portfolio-ai-backend/
├── app/
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Configuration settings
│   ├── routers/                # API endpoints
│   │   ├── chat.py             # POST /api/chat
│   │   ├── detail.py           # POST /api/detail
│   │   └── health.py           # GET /api/health
│   ├── services/               # Business logic
│   │   ├── intent_classifier.py
│   │   ├── retriever.py
│   │   ├── response_generator.py
│   │   ├── code_handler.py
│   │   └── session_manager.py
│   ├── prompts/                # LLM prompts
│   │   ├── system_prompts.py
│   │   └── templates.py
│   ├── models/                 # Pydantic models
│   │   ├── chat.py
│   │   └── responses.py
│   └── data/
│       └── knowledge_base/     # RAG source documents
├── scripts/
│   └── ingest.py               # Document ingestion script
├── chromadb/                   # Vector database storage
├── requirements.txt
├── Dockerfile
├── render.yaml                 # Render deployment config
└── README.md
```

## Setup

### Prerequisites

- Python 3.11+
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/deepanshu-malik/portfolio-ai-backend.git
cd portfolio-ai-backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

5. Ingest documents to ChromaDB:
```bash
python scripts/ingest.py
```

6. Run the server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### POST /api/chat

Send a chat message and receive an AI-generated response.

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
    {"label": "Show Code", "action": "code", "target": "rag_pipeline"}
  ],
  "detail_panel": null,
  "intent": "project_deepdive",
  "session_id": "session_123"
}
```

### POST /api/detail

Fetch detailed content like code snippets or comparisons.

**Request:**
```json
{
  "action": "code",
  "target": "rate_limiting",
  "session_id": "session_123"
}
```

### GET /api/health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "chromadb": "connected"
}
```

## Deployment

### Render (Recommended)

1. Push code to GitHub
2. Connect repository to Render
3. Set environment variables in Render dashboard:
   - `OPENAI_API_KEY`: Your OpenAI API key
4. Deploy!

### Docker

```bash
docker build -t portfolio-backend .
docker run -p 8000:8000 -e OPENAI_API_KEY=your_key portfolio-backend
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black app/
ruff check app/
```

### Type Checking

```bash
mypy app/
```

## License

MIT License
