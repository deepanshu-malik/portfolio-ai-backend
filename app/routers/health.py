"""Health check endpoint."""

import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Request

from app.config import settings
from app.models import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    """
    Enhanced health check endpoint for Koyeb.

    Returns the current status of the API and its dependencies.
    Includes ChromaDB document count and memory usage.
    """
    import psutil

    # Check ChromaDB status and document count
    chromadb_status = "unknown"
    try:
        from app.services.hybrid_retriever import retriever
        doc_count = retriever.collection.count()
        chromadb_status = "healthy" if doc_count > 0 else "empty"
        logger.debug(f"ChromaDB health check: {doc_count} documents")
    except Exception as e:
        logger.warning(f"ChromaDB health check failed: {e}")
        chromadb_status = "error"

    # Check memory usage
    try:
        memory = psutil.Process().memory_info()
        memory_mb = round(memory.rss / 1024 / 1024, 2)
        logger.debug(f"Memory usage: {memory_mb}MB")
    except Exception as e:
        logger.warning(f"Memory check failed: {e}")

    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        chromadb=chromadb_status,
    )


@router.get("/health/detailed")
async def detailed_health_check(request: Request) -> Dict[str, Any]:
    """
    Detailed health check with GenAI feature status and system metrics.

    Includes:
    - Service status
    - ChromaDB document count
    - Memory usage
    - Token usage statistics
    - Feature flags
    - OpenAI key validation
    """
    import psutil
    from app.services.token_tracker import token_tracker

    # Overall status
    overall_status = "healthy"
    checks = {}

    # ChromaDB check with document count
    try:
        from app.services.hybrid_retriever import retriever
        doc_count = retriever.collection.count()
        checks["chromadb"] = {
            "status": "ok" if doc_count > 0 else "empty",
            "documents": doc_count,
            "collection": settings.chroma_collection_name,
        }
        if doc_count == 0:
            overall_status = "degraded"
    except Exception as e:
        checks["chromadb"] = {
            "status": "error",
            "error": str(e),
        }
        overall_status = "degraded"

    # OpenAI key validation
    checks["openai"] = {
        "status": "ok" if settings.openai_api_key else "missing_key",
        "model": settings.openai_model,
        "embedding_model": settings.openai_embedding_model,
    }
    if not settings.openai_api_key:
        overall_status = "unhealthy"

    # Memory check
    try:
        memory = psutil.Process().memory_info()
        memory_mb = round(memory.rss / 1024 / 1024, 2)
        memory_percent = round(memory.rss / (512 * 1024 * 1024) * 100, 2)  # % of 512MB
        checks["memory"] = {
            "status": "ok" if memory_mb < 450 else "high",
            "rss_mb": memory_mb,
            "percent_of_limit": memory_percent,
            "limit_mb": 512,
        }
        if memory_mb >= 450:
            overall_status = "degraded"
    except Exception as e:
        checks["memory"] = {
            "status": "error",
            "error": str(e),
        }

    # Token usage stats
    token_stats = token_tracker.get_total_stats()

    return {
        "status": overall_status,
        "version": settings.app_version,
        "environment": settings.app_env,
        "timestamp": datetime.now().isoformat(),
        "checks": checks,
        "features": {
            "llm_intent_classification": True,
            "hybrid_retrieval": True,
            "llm_reranking": True,
            "token_tracking": True,
            "streaming": True,
            "request_timeout": True,
            "rate_limiting": True,
        },
        "config": {
            "max_concurrent_requests": settings.max_concurrent_requests,
            "request_timeout": settings.request_timeout,
            "max_history_length": settings.max_history_length,
            "rate_limit": f"{settings.rate_limit_requests} requests per {settings.rate_limit_window}s",
        },
        "token_usage": token_stats,
    }


@router.get("/ping")
async def ping() -> Dict[str, str]:
    """
    Lightweight ping endpoint for keep-alive services.

    Use this with external services like cron-job.org to prevent cold starts.
    This endpoint has minimal overhead and doesn't check dependencies.
    """
    return {
        "status": "pong",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness probe for Koyeb.

    Returns 200 when app is ready to accept traffic, 503 otherwise.
    Use this for Koyeb's readiness checks to avoid routing traffic
    to instances that are still starting up.
    """
    from app.main import app_ready

    if not app_ready:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={
                "ready": False,
                "message": "Application is still starting up",
            },
        )

    return {
        "ready": True,
        "timestamp": datetime.now().isoformat(),
    }
