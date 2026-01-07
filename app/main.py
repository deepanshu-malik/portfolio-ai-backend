"""
FastAPI Application Entry Point
Portfolio AI Backend with advanced RAG-powered chatbot capabilities.

Features:
- LLM-based intent classification
- Hybrid retrieval (semantic + keyword search)
- LLM reranking for relevance
- Token management and cost tracking
- Streaming responses
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routers import chat_v2 as chat, detail, health

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info("GenAI Features: LLM Intent Classification, Hybrid Retrieval, Reranking, Token Tracking")

    # Initialize hybrid retriever
    try:
        from app.services.hybrid_retriever import HybridRetriever
        app.state.hybrid_retriever = HybridRetriever()
        logger.info("HybridRetriever initialized successfully")
    except Exception as e:
        logger.warning(f"HybridRetriever initialization failed: {e}")
        app.state.hybrid_retriever = None

    yield

    # Shutdown
    logger.info("Shutting down application")
    
    # Log final token stats
    from app.services.token_tracker import token_tracker
    stats = token_tracker.get_total_stats()
    logger.info(f"Session stats - Total tokens: {stats['total_tokens']}, Cost: ${stats['total_cost']:.4f}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered portfolio assistant with RAG capabilities",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Rate Limiting Middleware (add before CORS)
from app.middleware import RateLimitMiddleware

app.add_middleware(RateLimitMiddleware)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception Handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.debug else "An unexpected error occurred",
        },
    )


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    logger.debug(f"Request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.debug(f"Response: {response.status_code}")
    return response


# Include routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(detail.router, prefix="/api", tags=["Detail"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else "Disabled in production",
        "health": "/api/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
