"""Response models for various endpoints."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Health status")
    version: str = Field(..., description="Application version")
    chromadb: str = Field(..., description="ChromaDB connection status")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "chromadb": "connected",
            }
        }


class DetailRequest(BaseModel):
    """Request model for detail endpoint."""

    action: str = Field(
        ...,
        description="Action type: code, deepdive, compare",
    )
    target: str = Field(
        ...,
        description="Target identifier",
    )
    session_id: str = Field(
        ...,
        description="Session identifier",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "action": "code",
                "target": "rate_limiting",
                "session_id": "session_123456",
            }
        }


class DetailResponse(BaseModel):
    """Response model for detail endpoint."""

    type: str = Field(..., description="Content type: code, table, diagram, text")
    title: str = Field(..., description="Content title")
    content: Any = Field(..., description="Main content")
    language: Optional[str] = Field(None, description="Code language")
    explanation: Optional[str] = Field(None, description="Additional explanation")
    links: Optional[Dict[str, str]] = Field(None, description="Related links")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "code",
                "title": "Rate Limiting Implementation",
                "content": "async def call_with_limit():\n    async with semaphore:\n        ...",
                "language": "python",
                "explanation": "This uses asyncio.Semaphore to limit concurrent API calls...",
                "links": {
                    "github": "https://github.com/deepanshu-malik/genai-sandbox/blob/master/05_rate_limiting.py"
                },
            }
        }
