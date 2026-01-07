"""Enhanced chat endpoint with advanced GenAI features."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.models import ChatRequest, ChatResponse
from app.services.llm_intent_classifier import LLMIntentClassifier
from app.services.hybrid_retriever import HybridRetriever
from app.services.advanced_response_generator import AdvancedResponseGenerator
from app.services.session_manager import SessionManager
from app.services.token_tracker import token_tracker

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize advanced services
intent_classifier = LLMIntentClassifier()
response_generator = AdvancedResponseGenerator()
session_manager = SessionManager()


def get_retriever(request: Request) -> Optional[HybridRetriever]:
    """Get or create hybrid retriever."""
    if not hasattr(request.app.state, "hybrid_retriever"):
        try:
            request.app.state.hybrid_retriever = HybridRetriever()
        except Exception as e:
            logger.error(f"Failed to initialize HybridRetriever: {e}")
            return None
    return request.app.state.hybrid_retriever


@router.post("/chat", response_model=ChatResponse)
async def chat(request: Request, chat_request: ChatRequest) -> ChatResponse:
    """
    Process a chat message with advanced GenAI pipeline.

    Pipeline:
    1. LLM-based intent classification
    2. Hybrid retrieval (semantic + keyword)
    3. LLM reranking
    4. Token-managed response generation
    5. Cost tracking
    """
    try:
        message = chat_request.message.strip()
        session_id = chat_request.session_id
        context = chat_request.context

        logger.info(f"Chat request from session {session_id}: {message[:50]}...")

        # Get session history
        session = session_manager.get_session(session_id)
        history = session.get("history", [])

        # 1. LLM-based intent classification
        intent = await intent_classifier.classify(
            message=message,
            context={
                "current_section": context.current_section if context else None,
                "previous_topic": context.previous_topic if context else None,
                "history": history,
            },
        )
        logger.info(f"Classified intent: {intent}")

        # 2. Hybrid retrieval with reranking
        retriever = get_retriever(request)
        retrieved_docs = []
        
        if retriever:
            try:
                retrieved_docs = await retriever.retrieve(
                    query=message,
                    intent=intent,
                    use_reranking=True,
                )
                logger.info(f"Retrieved {len(retrieved_docs)} documents")
            except Exception as e:
                logger.warning(f"Retrieval failed: {e}")

        # 3. Generate response with token management
        response_data = await response_generator.generate(
            query=message,
            intent=intent,
            retrieved_docs=retrieved_docs,
            history=history,
            session_id=session_id,
        )

        # 4. Update session
        session_manager.update_session(
            session_id=session_id,
            message=message,
            response=response_data["response"],
            intent=intent,
        )

        # Log token usage
        if "token_usage" in response_data:
            logger.info(f"Token usage: {response_data['token_usage']}")

        return ChatResponse(
            response=response_data["response"],
            suggestions=response_data.get("suggestions", []),
            detail_panel=response_data.get("detail_panel"),
            intent=intent,
            session_id=session_id,
        )

    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat message: {str(e)}",
        )


@router.post("/chat/stream")
async def chat_stream(request: Request, chat_request: ChatRequest):
    """
    Stream chat response for better UX.
    
    Returns Server-Sent Events (SSE) stream.
    """
    try:
        message = chat_request.message.strip()
        session_id = chat_request.session_id
        context = chat_request.context

        # Get session history
        session = session_manager.get_session(session_id)
        history = session.get("history", [])

        # Classify intent
        intent = await intent_classifier.classify(
            message=message,
            context={
                "current_section": context.current_section if context else None,
                "previous_topic": context.previous_topic if context else None,
            },
        )

        # Retrieve documents
        retriever = get_retriever(request)
        retrieved_docs = []
        
        if retriever:
            retrieved_docs = await retriever.retrieve(
                query=message,
                intent=intent,
                use_reranking=False,  # Skip reranking for speed in streaming
            )

        # Stream response
        async def generate():
            full_response = ""
            async for chunk in response_generator.generate_stream(
                query=message,
                intent=intent,
                retrieved_docs=retrieved_docs,
                history=history,
            ):
                full_response += chunk
                yield f"data: {chunk}\n\n"
            
            # Update session after streaming completes
            session_manager.update_session(
                session_id=session_id,
                message=message,
                response=full_response,
                intent=intent,
            )
            
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    except Exception as e:
        logger.error(f"Stream error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/stats")
async def get_chat_stats(session_id: Optional[str] = None):
    """
    Get token usage and cost statistics.
    
    Args:
        session_id: Optional session ID for session-specific stats
    """
    if session_id:
        return token_tracker.get_session_stats(session_id)
    return token_tracker.get_total_stats()
