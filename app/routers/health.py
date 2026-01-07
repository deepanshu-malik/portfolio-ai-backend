"""Health check endpoint."""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Request

from app.config import settings
from app.models import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    """
    Health check endpoint.

    Returns the current status of the API and its dependencies.
    """
    # Check ChromaDB status via HybridRetriever
    chromadb_status = "disconnected"
    try:
        retriever = getattr(request.app.state, "hybrid_retriever", None)
        if retriever is not None:
            stats = retriever.get_collection_stats()
            chromadb_status = stats.get("status", "unknown")
    except Exception as e:
        logger.warning(f"ChromaDB health check failed: {e}")
        chromadb_status = "error"

    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        chromadb=chromadb_status,
    )


@router.get("/health/detailed")
async def detailed_health_check(request: Request) -> Dict[str, Any]:
    """
    Detailed health check with GenAI feature status.
    """
    from app.services.token_tracker import token_tracker

    # ChromaDB stats
    chromadb_stats = {"status": "disconnected"}
    try:
        retriever = getattr(request.app.state, "hybrid_retriever", None)
        if retriever:
            chromadb_stats = retriever.get_collection_stats()
    except Exception as e:
        chromadb_stats = {"status": "error", "error": str(e)}

    # Token usage stats
    token_stats = token_tracker.get_total_stats()

    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.app_env,
        "features": {
            "llm_intent_classification": True,
            "hybrid_retrieval": True,
            "llm_reranking": True,
            "token_tracking": True,
            "streaming": True,
        },
        "models": {
            "chat": settings.openai_model,
            "embedding": settings.openai_embedding_model,
        },
        "chromadb": chromadb_stats,
        "token_usage": token_stats,
    }
