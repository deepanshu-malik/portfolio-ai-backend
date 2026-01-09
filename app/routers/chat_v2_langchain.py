"""LangChain-based chat router (v2 endpoint)."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from app.services.langchain import ConversationalChain
from app.services.llm_intent_classifier import LLMIntentClassifier
from app.models import Suggestion
from app.prompts.templates import get_suggestion_templates

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat/v2", tags=["chat-v2"])

# Initialize services
chain = ConversationalChain()
intent_classifier = LLMIntentClassifier()


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    response: str
    intent: Optional[str] = None
    sources: list[str] = []
    suggestions: list[Suggestion] = []
    session_id: str


@router.post("", response_model=ChatResponse)
async def chat_v2(request: ChatRequest):
    """LangChain-powered chat endpoint."""
    try:
        # Get previous topic from conversation history
        history = chain._get_history(request.session_id)
        previous_topic = None
        if history:
            for msg in reversed(history[-4:]):
                if isinstance(msg, HumanMessage):
                    content_lower = msg.content.lower()
                    if "project" in content_lower:
                        previous_topic = "project_deepdive"
                        break
                    elif "experience" in content_lower or "work" in content_lower:
                        previous_topic = "experience_deepdive"
                        break
        
        # Classify intent with context
        intent = await intent_classifier.classify(
            request.message,
            context={"previous_topic": previous_topic}
        )
        
        # Generate response
        result = await chain.invoke(
            query=request.message,
            session_id=request.session_id,
            intent=intent,
        )
        
        # Generate suggestions
        templates = get_suggestion_templates(intent or "general")
        suggestions = [
            Suggestion(label=t["label"], action=t["action"], target=t["target"])
            for t in templates[:4]
        ]
        
        return ChatResponse(
            response=result["response"],
            intent=result.get("intent"),
            sources=result.get("sources", []),
            suggestions=suggestions,
            session_id=request.session_id,
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream_v2(request: ChatRequest):
    """Streaming LangChain chat endpoint."""
    # Get previous topic from conversation history
    history = chain._get_history(request.session_id)
    previous_topic = None
    if history:
        # Check last few messages for context
        for msg in reversed(history[-4:]):
            if isinstance(msg, HumanMessage):
                content_lower = msg.content.lower()
                if "project" in content_lower:
                    previous_topic = "project_deepdive"
                    break
                elif "experience" in content_lower or "work" in content_lower:
                    previous_topic = "experience_deepdive"
                    break
    
    intent = await intent_classifier.classify(
        request.message,
        context={"previous_topic": previous_topic}
    )
    
    async def generate():
        async for chunk in chain.stream(
            query=request.message,
            session_id=request.session_id,
            intent=intent,
        ):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/stats")
async def get_stats():
    """Get token usage statistics."""
    return chain.get_token_stats()


@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """Clear conversation history."""
    chain.clear_session(session_id)
    return {"status": "cleared", "session_id": session_id}
