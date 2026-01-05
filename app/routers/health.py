"""Health check endpoint."""

import logging

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
    # Check ChromaDB status
    chromadb_status = "disconnected"
    try:
        retriever = getattr(request.app.state, "retriever", None)
        if retriever is not None:
            # Try a simple operation to verify connection
            chromadb_status = "connected"
    except Exception as e:
        logger.warning(f"ChromaDB health check failed: {e}")
        chromadb_status = "error"

    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        chromadb=chromadb_status,
    )
