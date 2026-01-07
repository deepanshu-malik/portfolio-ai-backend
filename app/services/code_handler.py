"""Code snippet handling service."""

import logging
from typing import Dict, Optional

from fastapi import HTTPException

from app.models import DetailResponse

logger = logging.getLogger(__name__)


class CodeHandler:
    """
    Handles code snippet retrieval and formatting.

    Features:
    - Pre-defined code snippets with explanations
    - Syntax highlighting support
    - GitHub links
    """

    # Code snippets database
    CODE_SNIPPETS = {
        "rate_limiting": {
            "title": "Rate Limiting Implementation",
            "language": "python",
            "content": '''import asyncio
from openai import AsyncOpenAI

# Limit concurrent requests to avoid rate limits
MAX_CONCURRENT = 2  # Free tier safe value
semaphore = asyncio.Semaphore(MAX_CONCURRENT)

async def call_with_rate_limit(client: AsyncOpenAI, prompt: str) -> str:
    """Make LLM call with rate limiting."""
    async with semaphore:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

async def process_batch(prompts: list[str]) -> list[str]:
    """Process multiple prompts with rate limiting."""
    client = AsyncOpenAI()

    tasks = [
        call_with_rate_limit(client, prompt)
        for prompt in prompts
    ]

    results = await asyncio.gather(*tasks)
    return results''',
            "explanation": "This uses asyncio.Semaphore to limit concurrent API calls. Even with 100 items to process, only MAX_CONCURRENT calls happen simultaneously. This prevents hitting OpenAI's rate limits (3 RPM on free tier).",
            "links": {
                "github": "https://github.com/deepanshu-malik/genai-sandbox/blob/main/05_rate_limiting.py"
            },
        },
        "rag_pipeline": {
            "title": "Complete RAG Pipeline",
            "language": "python",
            "content": '''from chromadb import Client
from openai import OpenAI

class RAGPipeline:
    def __init__(self, collection_name: str):
        self.client = OpenAI()
        self.chroma = Client()
        self.collection = self.chroma.get_or_create_collection(
            name=collection_name
        )

    def add_documents(self, documents: list[str], ids: list[str]):
        """Add documents to vector store."""
        embeddings = self._get_embeddings(documents)
        self.collection.add(
            embeddings=embeddings,
            documents=documents,
            ids=ids
        )

    def query(self, question: str, k: int = 3) -> str:
        """Query with RAG."""
        # Retrieve relevant documents
        query_embedding = self._get_embeddings([question])[0]
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k
        )

        # Build context
        context = "\\n\\n".join(results["documents"][0])

        # Generate response
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Answer based on context:\\n{context}"},
                {"role": "user", "content": question}
            ]
        )

        return response.choices[0].message.content

    def _get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for texts."""
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        return [e.embedding for e in response.data]''',
            "explanation": "Full RAG implementation: Load documents, generate embeddings, store in ChromaDB, retrieve relevant chunks on query, and generate augmented responses. Uses ChromaDB for simplicity and text-embedding-3-small for cost-effective embeddings.",
            "links": {
                "github": "https://github.com/deepanshu-malik/genai-sandbox/blob/main/rag/04_complete_rag_pipeline.py"
            },
        },
        "chunking": {
            "title": "Chunking Strategies",
            "language": "python",
            "content": '''import re

def simple_chunk(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into fixed-size chunks with overlap."""
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap

    return chunks

def sentence_chunk(text: str, max_sentences: int = 5) -> list[str]:
    """Split text into chunks of N sentences."""
    sentences = re.split(r'(?<=[.!?])\\s+', text)
    chunks = []

    for i in range(0, len(sentences), max_sentences):
        chunk = ' '.join(sentences[i:i + max_sentences])
        chunks.append(chunk)

    return chunks

def paragraph_chunk(text: str) -> list[str]:
    """Split text into paragraph-based chunks."""
    paragraphs = text.split('\\n\\n')
    return [p.strip() for p in paragraphs if p.strip()]

# Trade-offs:
# Simple: Fast, predictable size, may break sentences
# Sentence: Preserves meaning, variable sizes
# Paragraph: Best semantic units, may be too large''',
            "explanation": "Three chunking strategies with different trade-offs. Simple chunking is fast but may break mid-sentence. Sentence chunking preserves meaning but has variable sizes. Paragraph chunking preserves semantic units and is best for Q&A.",
            "links": {
                "github": "https://github.com/deepanshu-malik/genai-sandbox/blob/main/rag/02_chunking_strategies.py"
            },
        },
        "async_calls": {
            "title": "Async LLM Calls",
            "language": "python",
            "content": '''import asyncio
from openai import AsyncOpenAI

async def process_single(client: AsyncOpenAI, prompt: str) -> str:
    """Process a single prompt asynchronously."""
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

async def process_batch(prompts: list[str]) -> list[str]:
    """Process multiple prompts concurrently."""
    client = AsyncOpenAI()

    tasks = [process_single(client, p) for p in prompts]
    results = await asyncio.gather(*tasks)

    return results

# Performance comparison:
# Sequential: 10 calls × 1s each = 10s
# Async: 10 calls concurrent = ~1-2s
# Result: 5-10x faster for batch operations''',
            "explanation": "Use AsyncOpenAI client for concurrent API calls. asyncio.gather() runs all tasks simultaneously, achieving 5-10x faster batch processing. Combine with rate limiting for production use.",
            "links": {
                "github": "https://github.com/deepanshu-malik/genai-sandbox/blob/main/04_async_calls.py"
            },
        },
    }

    # Deep dive content
    DEEPDIVE_CONTENT = {
        "rag_architecture": {
            "title": "RAG Pipeline Architecture",
            "content": """## RAG Pipeline Architecture

### Components

1. **Document Ingestion**
   - Load markdown/text files
   - Chunk using paragraph strategy
   - Generate embeddings with OpenAI

2. **Vector Storage (ChromaDB)**
   - Persistent local storage
   - Cosine similarity search
   - Metadata filtering

3. **Retrieval**
   - Embed user query
   - Find top-k similar chunks
   - Return with relevance scores

4. **Augmented Generation**
   - Inject context into prompt
   - Generate with gpt-4o-mini
   - Include citations

### Design Decisions

- **ChromaDB**: Easy local setup, no external service
- **text-embedding-3-small**: Cost-effective, good quality
- **Paragraph chunking**: Preserves semantic context
- **k=3-5**: Balance between context and relevance""",
        },
        "rag_challenges": {
            "title": "RAG Challenges & Solutions",
            "content": """## RAG Challenges Faced

### 1. Rate Limiting
**Problem**: Free tier has 3 RPM limit
**Solution**: Semaphore-based rate limiting

### 2. Chunk Size Optimization
**Problem**: Too small = lost context, too large = irrelevant content
**Solution**: Paragraph-based chunking with fallback

### 3. Context Window Management
**Problem**: Large documents exceed token limits
**Solution**: Top-k retrieval with token counting

### 4. Answer Quality
**Problem**: Generic or off-topic responses
**Solution**: Better system prompts, explicit grounding""",
        },
    }

    # Comparison tables
    COMPARISONS = {
        "rag_vs_backend": {
            "title": "RAG Project vs Professional Backend Work",
            "content": {
                "headers": ["Aspect", "genai-sandbox (RAG)", "Communication Platform"],
                "rows": [
                    ["Domain", "AI/ML", "Distributed systems"],
                    ["Scale", "Learning/Demo", "Production (1000s/day)"],
                    ["Focus", "Embeddings, search", "Reliability, webhooks"],
                    ["Complexity", "Single-service", "Multi-service mesh"],
                    ["Databases", "ChromaDB (vector)", "Mongo + MySQL + OS"],
                    ["Team", "Solo", "Collaborative with CTO/CPO"],
                ],
            },
        },
        "chunking_strategies": {
            "title": "Chunking Strategies Comparison",
            "content": {
                "headers": ["Strategy", "Speed", "Semantic Quality", "Size Control"],
                "rows": [
                    ["Simple", "Fast", "Low", "High"],
                    ["Sentence", "Medium", "Medium", "Medium"],
                    ["Paragraph", "Fast", "High", "Low"],
                ],
            },
        },
    }

    def get_code_snippet(self, target: str) -> DetailResponse:
        """Get a code snippet by target identifier."""
        snippet = self.CODE_SNIPPETS.get(target)

        if not snippet:
            logger.warning(f"Code snippet not found: {target}")
            raise HTTPException(status_code=404, detail=f"Code snippet not found: {target}")

        return DetailResponse(
            type="code",
            title=snippet["title"],
            content=snippet["content"],
            language=snippet.get("language", "python"),
            explanation=snippet.get("explanation"),
            links=snippet.get("links"),
        )

    def get_deepdive(self, target: str) -> DetailResponse:
        """Get deep dive content by target identifier."""
        content = self.DEEPDIVE_CONTENT.get(target)

        if not content:
            logger.warning(f"Deep dive content not found: {target}")
            raise HTTPException(status_code=404, detail=f"Deep dive content not found: {target}")

        return DetailResponse(
            type="text",
            title=content["title"],
            content=content["content"],
            language=None,
            explanation=None,
            links=None,
        )

    def get_comparison(self, target: str) -> DetailResponse:
        """Get comparison table by target identifier."""
        comparison = self.COMPARISONS.get(target)

        if not comparison:
            logger.warning(f"Comparison not found: {target}")
            raise HTTPException(status_code=404, detail=f"Comparison not found: {target}")

        return DetailResponse(
            type="table",
            title=comparison["title"],
            content=comparison["content"],
            language=None,
            explanation=None,
            links=None,
        )
