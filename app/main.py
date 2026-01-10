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
from app.routers import chat_v2_langchain

# Configure structured logging for Koyeb
import sys
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)  # Output to stdout for Koyeb logs
    ],
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Global readiness flag for Koyeb health checks
app_ready = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    import time
    startup_start = time.time()

    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info("GenAI Features: LLM Intent Classification, Hybrid Retrieval, Reranking, Token Tracking")

    # Validate critical environment variables
    logger.info("Validating environment configuration...")
    validation_errors = []

    if not settings.openai_api_key:
        validation_errors.append("OPENAI_API_KEY is not set")
        logger.error("CRITICAL: OPENAI_API_KEY environment variable is not set!")

    if settings.rate_limit_requests < 1:
        logger.warning(f"Rate limit too low ({settings.rate_limit_requests}), setting to 5")
        settings.rate_limit_requests = 5

    if settings.max_concurrent_requests < 1:
        logger.warning(f"Max concurrent requests too low ({settings.max_concurrent_requests}), setting to 3")
        settings.max_concurrent_requests = 3

    # Check ChromaDB directory
    import os
    if not os.path.exists(settings.chroma_persist_directory):
        logger.warning(f"ChromaDB directory not found: {settings.chroma_persist_directory}")
        try:
            os.makedirs(settings.chroma_persist_directory, exist_ok=True)
            logger.info(f"Created ChromaDB directory: {settings.chroma_persist_directory}")
        except Exception as e:
            validation_errors.append(f"Failed to create ChromaDB directory: {e}")

    # Log all configuration
    logger.info("Configuration:")
    logger.info(f"  OpenAI Model: {settings.openai_model}")
    logger.info(f"  OpenAI Embedding Model: {settings.openai_embedding_model}")
    logger.info(f"  Rate Limit: {settings.rate_limit_requests} requests per {settings.rate_limit_window}s")
    logger.info(f"  Max Concurrent Requests: {settings.max_concurrent_requests}")
    logger.info(f"  Request Timeout: {settings.request_timeout}s")
    logger.info(f"  Max History Length: {settings.max_history_length}")
    logger.info(f"  Max Context Tokens: {settings.max_tokens_context}")
    logger.info(f"  Max Response Tokens: {settings.max_tokens_response}")
    logger.info(f"  Cache Enabled: {settings.cache_enabled}")
    logger.info(f"  ChromaDB Directory: {settings.chroma_persist_directory}")

    # Fail fast if critical errors
    if validation_errors:
        error_msg = "Environment validation failed:\n" + "\n".join(f"  - {e}" for e in validation_errors)
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    logger.info("Environment validation passed!")

    # Warm up services for faster cold starts
    logger.info("Warming up services...")

    # Pre-load and verify ChromaDB
    try:
        from app.services.hybrid_retriever import retriever
        doc_count = retriever.collection.count()
        logger.info(f"ChromaDB warmed up successfully - {doc_count} documents loaded")

        # Verify data exists, re-ingest if empty
        if doc_count == 0:
            logger.warning("ChromaDB is empty! Re-running ingestion...")
            import subprocess
            result = subprocess.run(["python", "scripts/ingest.py"], capture_output=True, text=True)
            if result.returncode == 0:
                doc_count = retriever.collection.count()
                logger.info(f"Ingestion completed - {doc_count} documents loaded")
            else:
                logger.error(f"Ingestion failed: {result.stderr}")
    except Exception as e:
        logger.error(f"ChromaDB warmup failed: {e}")

    # Pre-load intent classifier
    try:
        from app.services.llm_intent_classifier import intent_classifier
        logger.info("Intent classifier loaded")
    except Exception as e:
        logger.error(f"Intent classifier loading failed: {e}")

    # Pre-load response generator
    try:
        from app.services.advanced_response_generator import response_generator
        logger.info("Response generator loaded")
    except Exception as e:
        logger.error(f"Response generator loading failed: {e}")

    startup_time = time.time() - startup_start
    logger.info(f"Services ready in {startup_time:.2f} seconds")

    # Mark application as ready for traffic
    global app_ready
    app_ready = True
    logger.info("Application is READY to accept traffic")

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

# Middleware (order matters: last added = first executed)
from app.middleware import RateLimitMiddleware, TimeoutMiddleware

# Timeout middleware (outermost - catches all timeouts)
app.add_middleware(TimeoutMiddleware)

# Rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# CORS middleware
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


# Request logging middleware (enhanced for debugging)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all incoming requests with detailed information.

    Logs: method, path, client IP, status code, duration, user agent.
    Critical for debugging issues on Koyeb deployment.
    """
    import time
    import uuid

    # Generate correlation ID for request tracing
    correlation_id = str(uuid.uuid4())[:8]
    request.state.correlation_id = correlation_id

    # Get client IP (handle proxied requests)
    client_ip = request.client.host if request.client else "unknown"
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()

    # Start timing
    start_time = time.time()

    # Log request
    logger.info(
        f"[{correlation_id}] --> {request.method} {request.url.path} "
        f"from {client_ip}"
    )

    try:
        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        logger.info(
            f"[{correlation_id}] <-- {request.method} {request.url.path} "
            f"status={response.status_code} duration={duration:.3f}s"
        )

        # Add correlation ID to response headers for debugging
        response.headers["X-Correlation-ID"] = correlation_id

        return response

    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"[{correlation_id}] <-- {request.method} {request.url.path} "
            f"ERROR after {duration:.3f}s: {str(e)}",
            exc_info=True
        )
        raise


# Include routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(detail.router, prefix="/api", tags=["Detail"])
app.include_router(chat_v2_langchain.router, tags=["Chat-LangChain"])


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
