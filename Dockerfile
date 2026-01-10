# Multi-stage Dockerfile for Portfolio AI Backend

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim as runtime

WORKDIR /app

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Copy installed packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Set PATH for user packages
ENV PATH=/home/appuser/.local/bin:$PATH

# Copy application code and knowledge base
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser scripts/ ./scripts/

# Create directories for data
RUN mkdir -p chromadb && chown -R appuser:appuser chromadb

# Switch to non-root user
USER appuser

# Run document ingestion at BUILD time to bake data into image
# This ensures ChromaDB data persists across deployments
ARG OPENAI_API_KEY=""
ENV OPENAI_API_KEY=${OPENAI_API_KEY}

# Run ingestion - data will be part of the image
RUN python scripts/ingest.py && \
    echo "ChromaDB ingestion completed successfully" || \
    echo "WARNING: Ingestion failed - will retry at runtime"

# Verify ingestion succeeded by checking ChromaDB directory
RUN test -f chromadb/chroma.sqlite3 && \
    echo "ChromaDB database file found - ingestion verified" || \
    echo "WARNING: ChromaDB database file not found"

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/api/health').raise_for_status()"

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
