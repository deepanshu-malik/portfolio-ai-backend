"""Enhanced chat endpoint with advanced GenAI features."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.config import settings
from app.models import ChatRequest, ChatResponse
from app.services.llm_intent_classifier import LLMIntentClassifier
from app.services.hybrid_retriever import HybridRetriever
from app.services.advanced_response_generator import AdvancedResponseGenerator
from app.services.session_manager import SessionManager
from app.services.token_tracker import token_tracker
from app.services.cache import response_cache

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
        
        # Use session's current_topic as previous_topic if not provided by client
        previous_topic = (context.previous_topic if context and context.previous_topic 
                         else session.get("current_topic"))

        # 1. LLM-based intent classification
        intent = await intent_classifier.classify(
            message=message,
            context={
                "current_section": context.current_section if context else None,
                "previous_topic": previous_topic,
                "history": history,
            },
            session_id=session_id,
        )
        logger.info(f"Classified intent: {intent} (previous_topic: {previous_topic})")

        # 1.5. Check cache for existing response (if enabled)
        if settings.cache_enabled:
            cached_response = response_cache.get(message, intent)
            if cached_response:
                logger.info(f"Cache HIT - returning cached response for session {session_id}")
                # Update session with cached response
                session_manager.update_session(
                    session_id=session_id,
                    message=message,
                    response=cached_response["response"],
                    intent=intent,
                )
                return ChatResponse(
                    response=cached_response["response"],
                    suggestions=cached_response.get("suggestions", []),
                    detail_panel=cached_response.get("detail_panel"),
                    intent=intent,
                    session_id=session_id,
                    sources=cached_response.get("sources", []),
                    cached=True,
                )

        # 2. Hybrid retrieval with reranking
        retriever = get_retriever(request)
        retrieved_docs = []
        sources = []
        
        if retriever:
            try:
                retrieved_docs = await retriever.retrieve(
                    query=message,
                    intent=intent,
                    use_reranking=True,
                )
                logger.info(f"Retrieved {len(retrieved_docs)} documents")
                # Extract sources from retrieved documents
                sources = [doc["metadata"].get("source", "") for doc in retrieved_docs if doc.get("metadata")]
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

        # 5. Cache the response (if enabled and no error)
        if settings.cache_enabled and not response_data.get("error"):
            cache_data = {
                "response": response_data["response"],
                "suggestions": response_data.get("suggestions", []),
                "detail_panel": response_data.get("detail_panel"),
                "sources": sources,
            }
            response_cache.set(message, cache_data, intent)
            logger.debug(f"Response cached for message: {message[:50]}...")

        # Log token usage
        if "token_usage" in response_data:
            logger.info(f"Token usage: {response_data['token_usage']}")

        logger.info(f"Response data keys: {response_data.keys()}")
        logger.info(f"Suggestions: {response_data.get('suggestions')}")

        return ChatResponse(
            response=response_data["response"],
            suggestions=response_data.get("suggestions", []),
            detail_panel=response_data.get("detail_panel"),
            intent=intent,
            session_id=session_id,
            sources=sources,
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
        
        # Use session's current_topic as previous_topic if not provided by client
        previous_topic = (context.previous_topic if context and context.previous_topic 
                         else session.get("current_topic"))

        # Classify intent
        intent = await intent_classifier.classify(
            message=message,
            context={
                "current_section": context.current_section if context else None,
                "previous_topic": previous_topic,
            },
            session_id=session_id,
        )

        # Retrieve documents
        retriever = get_retriever(request)
        retrieved_docs = []
        
        if retriever:
            try:
                retrieved_docs = await retriever.retrieve(
                    query=message,
                    intent=intent,
                    use_reranking=False,  # Skip reranking for speed in streaming
                )
            except Exception as e:
                logger.warning(f"Retrieval failed in stream: {e}")

        # Stream response
        async def generate():
            full_response = ""
            async for chunk in response_generator.generate_stream(
                query=message,
                intent=intent,
                retrieved_docs=retrieved_docs,
                history=history,
                session_id=session_id,
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


@router.get("/chat/cache/stats")
async def get_cache_stats():
    """
    Get response cache statistics.

    Returns cache hit rate, size, and other metrics.
    Useful for monitoring cache effectiveness and cost savings.
    """
    stats = response_cache.get_stats()

    # Add estimated cost savings
    # Assuming average response costs ~$0.001 per request
    estimated_savings = stats["hits"] * 0.001
    stats["estimated_cost_savings_usd"] = round(estimated_savings, 4)

    return {
        "cache_enabled": settings.cache_enabled,
        "stats": stats,
        "message": f"Cache is saving ~{stats['hit_rate_percent']}% of OpenAI API calls",
    }


@router.post("/chat/cache/clear")
async def clear_cache():
    """
    Clear all cached responses.

    Useful for debugging or forcing fresh responses.
    """
    response_cache.clear()
    return {
        "status": "success",
        "message": "Response cache cleared",
    }
