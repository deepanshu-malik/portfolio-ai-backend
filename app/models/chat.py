"""Chat-related Pydantic models."""

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class ChatContext(BaseModel):
    """Context information for the chat session."""

    current_section: Optional[str] = Field(
        None,
        description="Current section of the portfolio the user is viewing",
    )
    previous_topic: Optional[str] = Field(
        None,
        description="Previous topic discussed in the conversation",
    )


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="User's message",
    )
    session_id: str = Field(
        ...,
        min_length=1,
        description="Unique session identifier",
    )
    context: Optional[ChatContext] = Field(
        None,
        description="Additional context for the conversation",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Tell me about your RAG experience",
                "session_id": "session_123456",
                "context": {
                    "current_section": "projects",
                    "previous_topic": None,
                },
            }
        }


class Suggestion(BaseModel):
    """Suggestion chip model."""

    label: str = Field(..., description="Display label for the suggestion")
    action: str = Field(..., description="Action type: code, deepdive, compare")
    target: str = Field(..., description="Target identifier for the action")


class DetailPanel(BaseModel):
    """Detail panel content model."""

    type: str = Field(
        ...,
        description="Content type: code, table, diagram, text",
    )
    content: Any = Field(..., description="Panel content")
    title: Optional[str] = Field(None, description="Panel title")
    language: Optional[str] = Field(None, description="Code language for highlighting")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    response: str = Field(..., description="Bot's response message")
    suggestions: List[Suggestion] = Field(
        default_factory=list,
        description="Suggested follow-up actions",
    )
    detail_panel: Optional[DetailPanel] = Field(
        None,
        description="Content for the detail panel",
    )
    intent: str = Field(
        default="general",
        description="Detected intent of the user's message",
    )
    session_id: str = Field(..., description="Session identifier")

    class Config:
        json_schema_extra = {
            "example": {
                "response": "I've built a production-ready RAG pipeline...",
                "suggestions": [
                    {"label": "Show Code", "action": "code", "target": "rag_pipeline"},
                    {
                        "label": "Architecture",
                        "action": "deepdive",
                        "target": "rag_architecture",
                    },
                ],
                "detail_panel": None,
                "intent": "project_inquiry",
                "session_id": "session_123456",
            }
        }
